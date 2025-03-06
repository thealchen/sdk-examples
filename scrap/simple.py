import os
from galileo import log, galileo_context, openai  # Import Galileo components
import json
import time
from pydantic import BaseModel, Field
from typing import Dict, Any
from dotenv import load_dotenv
from rich.console import Console
import questionary

load_dotenv()

# Initialize console and OpenAI client
console = Console()
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Pydantic models for structured output
class NumberConversion(BaseModel):
    number: int = Field(..., description="The numerical value of the text number")

class CalculationResult(BaseModel):
    result: float = Field(..., description="The result of the calculation")

# Load tool specifications from JSON file
def load_tools():
    with open(os.path.join(os.path.dirname(__file__), "tools.json"), "r") as f:
        return json.load(f)

# Tool: Convert text numbers to numerical values using LLM with structured output
@log(span_type="tool")  # Galileo integration: Log this function as a tool
def convert_text_to_number(text):
    """Convert a text number (like 'seven') to its numerical value (7)."""
    console.print(f"[yellow]Converting:[/yellow] {text}")
    
    prompt = f"""
Convert the text number "{text}" to a numerical value.
Return the result as a JSON object with a 'number' field containing only the integer value.
For example, for "twenty-five", return: {{"number": 25}}
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
        
    # Parse the JSON response
    try:
        json_response = json.loads(response.choices[0].message.content.strip())
        # Validate with Pydantic
        validated = NumberConversion(**json_response)
        # Store the number as an integer for internal use
        number = validated.number
        
        console.print(f"[green]Converted to:[/green] {number}")
        # Return a string representation for Galileo logging
        return str(number)
    except Exception as e:
        console.print(f"[bold red]Error parsing LLM response:[/bold red] {str(e)}")
        # Fallback: try to extract a number from the raw text
        raw_text = response.choices[0].message.content.strip()
        try:
            # Look for digits in the response
            for word in raw_text.split():
                if word.isdigit():
                    return str(int(word))
        except:
            pass
        return f"Error: {str(e)}"

# Tool: Calculator for arithmetic operations
@log(span_type="tool")  # Galileo integration: Log this function as a tool
def calculate(expression):
    """Perform a calculation based on the given expression."""
    console.print(f"[yellow]Calculating:[/yellow] {expression}")
    
    try:
        result = eval(expression)
        console.print(f"[green]Result:[/green] {result}")
        return f"The result of {expression} is {result}"
    except Exception as e:
        console.print(f"[bold red]Error calculating:[/bold red] {str(e)}")
        return f"Error calculating {expression}: {str(e)}"

@log(span_type="llm")  # Galileo integration: Log this function as an LLM call
def get_tool_calls(query):
    """Ask the LLM to determine what tools to call for the given query."""
    console.print("[blue]Asking LLM to determine tools to call...[/blue]")
    
    # Load tools
    tools = load_tools()
    
    # Prepare messages for the LLM
    messages = [{
        "role": "system",
        "content": """You are an agent that processes numerical queries using these tools:
1. convert_text_to_number: Converts text numbers (like "seven") to digits (7)
2. calculate: Performs arithmetic with numerical expressions ("4 + 7")

For ANY query containing arithmetic operations (+, -, *, / or plus, minus, times, divide):
1. You MUST first convert any text numbers to digits
2. You MUST then perform the calculation with the converted numbers
3. Both steps are required - never stop after just converting numbers"""
    },
    {
        "role": "user",
        "content": """Example: "What's 4 + seven?"
Required steps:
1. convert_text_to_number(text="seven") -> 7
2. calculate(expression="4 + 7")  # This step is mandatory!

Example: "What's three plus seven?"
Required steps:
1. convert_text_to_number(text="three") -> 3
2. convert_text_to_number(text="seven") -> 7
3. calculate(expression="3 + 7")  # This step is mandatory!

Never stop after just converting numbers - you must calculate the result!"""
    },
    {
        "role": "user", 
        "content": f"Process this query: '{query}'"
    }]
    
    # Make the LLM call
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
    )
    
    return response, tools

@log  # Default workflow span to contain the entire process
def process_query(query):
    """Process a numerical query using LLM and tools."""
    console.print("[bold blue]Processing query...[/bold blue]")
    console.print(f"Query: {query}")
    
    try:
        # Get tool calls from LLM
        response, tools = get_tool_calls(query)
        
        # Check if we have tool calls
        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            console.print("[bold yellow]No tool calls detected in the response[/bold yellow]")
            return "I couldn't process your query. Please try again with a clearer request."
        
        # Initialize results and conversation history
        results = []
        messages = []
        converted_values = {}
        
        # Add the assistant's response to the conversation history
        messages.append({
            "role": "assistant",
            "content": response.choices[0].message.content or "",
            "tool_calls": [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments
                    }
                } for call in tool_calls
            ]
        })
        
        # Process each tool call
        for call in tool_calls:
            if call.function.name == "convert_text_to_number":
                text = json.loads(call.function.arguments)["text"]
                
                # Call the function - the @log decorator will create a tool span
                number_str = convert_text_to_number(text)
                
                number = int(number_str) if number_str.isdigit() else None
                if number is not None:
                    results.append(f"Converted '{text}' to {number}")
                    converted_values[text] = number
                    
                    # Add the tool response to conversation history
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": str(number)
                    })
            
            elif call.function.name == "calculate":
                expression = json.loads(call.function.arguments)["expression"]
                
                # Call the function - the @log decorator will create a tool span
                result = calculate(expression)
                
                results.append(result)
                
                # Add the tool response to conversation history
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result
                })
        
        # Check if we need to make a follow-up request for calculation
        has_arithmetic = any(op in query.lower() for op in ['+', '-', '*', '/', 'plus', 'minus', 'times', 'divide'])
        calculation_done = any("result of" in r for r in results)
        
        if has_arithmetic and not calculation_done and converted_values:
            console.print("[yellow]Calculation step missing - making follow-up request...[/yellow]")
            
            # Add a message requesting completion of the sequence
            follow_up_message = f"Now you must calculate the result using the converted numbers. The original query was: '{query}'"
            console.print(f"[blue]Follow-up request:[/blue] {follow_up_message}")
            
            messages.append({
                "role": "user",
                "content": follow_up_message
            })
            
            # Make a follow-up request
            follow_up = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=tools,
            )
            
            # Process any additional tool calls
            follow_up_tool_calls = follow_up.choices[0].message.tool_calls
            if follow_up_tool_calls:
                # Add the assistant's response to the conversation history
                messages.append({
                    "role": "assistant",
                    "content": follow_up.choices[0].message.content or "",
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": "function",
                            "function": {
                                "name": call.function.name,
                                "arguments": call.function.arguments
                            }
                        } for call in follow_up_tool_calls
                    ]
                })
                
                # Process follow-up tool calls
                for call in follow_up_tool_calls:
                    if call.function.name == "calculate":
                        expression = json.loads(call.function.arguments)["expression"]
                        
                        # Call the function - the @log decorator will create a tool span
                        result = calculate(expression)
                        
                        results.append(result)
                        
                        # Add the tool response to conversation history
                        messages.append({
                            "role": "tool",
                            "tool_call_id": call.id,
                            "content": result
                        })
        
        # Create a final summary
        if results:
            # Extract the calculation result if available
            final_answer = results[-1]
            if "result of" in final_answer and "is" in final_answer:
                final_answer = final_answer.split("is")[-1].strip()
            
            # Create a summary of all operations
            summary = f"I've processed your query '{query}'.\n\n"
            
            # Add information about text number conversions
            if converted_values:
                summary += "Text number conversions:\n"
                for text, number in converted_values.items():
                    summary += f"- '{text}' → {number}\n"
                summary += "\n"
            
            # Add calculation result if available
            if calculation_done or any("result of" in r for r in results):
                summary += f"Final answer: {final_answer}"
            else:
                summary += "\n".join(results)
        else:
            summary = "I couldn't process your query. Please try again with a clearer request."
        
        console.print(f"[dim]Final results: {results}[/dim]")
        return summary
        
    except Exception as e:
        console.print(f"[bold red]Error in process_query:[/bold red] {str(e)}")
        import traceback
        console.print(traceback.format_exc())
        return f"Error processing query: {str(e)}"

def main():    
    # Add a console header
    console.print("[bold]Number Converter & Calculator Agent[/bold]")
    console.print("Simple agent demonstrating Galileo integration")
    console.print("Type your query or 'exit' to quit\n")
    
    # Process a single query and exit
    query = questionary.text(
        "Enter your query:",
        default="What's 4 + seven?"
    ).ask()
    
    if query is None or query.lower() in ['exit', 'quit', 'q']:
        console.print("\n[bold]Exiting. Goodbye![/bold]")
        return
        
    try:
        # Galileo integration: Create a context for tracking this entire request
        # This wraps the entire process in a Galileo trace for observability
        with galileo_context():
            result = process_query(query)
        
        console.print("\n[bold green]Result:[/bold green]")
        console.print(result)
        console.print("\n[bold]Exiting. Goodbye![/bold]")
            
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        import traceback
        console.print(traceback.format_exc())

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold]Exiting. Goodbye![/bold]")
