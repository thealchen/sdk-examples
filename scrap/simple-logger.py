import os
from galileo import galileo_context
from galileo.logger import GalileoLogger
import json
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from rich.console import Console
import questionary
import time
import openai  # Import regular OpenAI client

load_dotenv()

# Initialize console and OpenAI client
console = Console()
# Use regular OpenAI client to avoid automatic trace creation
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Initialize Galileo Logger
logger = GalileoLogger(project="simple-agent", log_stream="dev")

# Define Pydantic models for validation
class NumberConversion(BaseModel):
    number: int = Field(..., description="The numerical value of the text number")

class CalculationResult(BaseModel):
    result: float = Field(..., description="The result of the calculation")

# Load tool specifications from JSON file
def load_tools():
    with open(os.path.join(os.path.dirname(__file__), "tools.json"), "r") as f:
        return json.load(f)

# Tool: Convert text numbers to numerical values using LLM with structured output
def convert_text_to_number(text):
    # We don't create a tool span here anymore - it will be created in process_query
    start_time = time.time()
    
    prompt = f"""
Convert the text number "{text}" to a numerical value.
Return the result as a JSON object with a 'number' field containing only the integer value.
For example, for "twenty-five", return: {{"number": 25}}
"""
    # Use regular OpenAI client to avoid creating a trace
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
        
        # Calculate duration in nanoseconds
        duration_ns = int((time.time() - start_time) * 1_000_000_000)
        
        # Return both the result and duration for logging in process_query
        return str(number), duration_ns
    except Exception as e:
        console.print(f"[bold red]Error parsing LLM response:[/bold red] {str(e)}")
        
        # Calculate duration in nanoseconds
        duration_ns = int((time.time() - start_time) * 1_000_000_000)
        
        # Fallback: try to extract a number from the raw text
        raw_text = response.choices[0].message.content.strip()
        try:
            # Look for digits in the response
            for word in raw_text.split():
                if word.isdigit():
                    number = int(word)
                    return str(number), duration_ns
        except:
            pass
        
        return f"Error: {str(e)}", duration_ns

# Tool: Calculator for arithmetic operations
def calculate(expression):
    # We don't create a tool span here anymore - it will be created in process_query
    start_time = time.time()
    
    try:
        result = eval(expression)
        
        # Calculate duration in nanoseconds
        duration_ns = int((time.time() - start_time) * 1_000_000_000)
        
        # Return both the result and duration for logging in process_query
        return f"The result of {expression} is {result}", duration_ns
    except Exception as e:
        # Calculate duration in nanoseconds
        duration_ns = int((time.time() - start_time) * 1_000_000_000)
        
        return f"Error calculating {expression}: {str(e)}", duration_ns

def process_query(query):
    """
    Process a numerical query using LLM and tools.
    This function follows the same pattern as simple-simulator.py, which works correctly.
    """
    console.print("[bold blue]Processing query...[/bold blue]")
    console.print(f"Query: {query}")
    
    # Create a trace at the beginning - this is critical
    trace_id = logger.start_trace(
        input=query,
        name="process_query"
    )
    console.print(f"[blue]Started trace with ID: {trace_id}[/blue]")
    
    start_time = time.time()
    
    try:
        # Load tools
        tools = load_tools()
        console.print(f"[dim]Loaded {len(tools)} tools[/dim]")
        
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
        
        # Make the initial LLM call for tool selection
        llm_start_time = time.time()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
        )
        llm_duration_ns = int((time.time() - llm_start_time) * 1_000_000_000)
        
        # Log the LLM span for tool selection
        console.print("[blue]Creating LLM span for tool selection[/blue]")
        llm_span_id = logger.add_llm_span(
            input=messages,
            output=response.model_dump(),
            model="gpt-4o",
            tools=tools,
            name="agent_llm_call",
            duration_ns=llm_duration_ns
        )
        console.print(f"[dim]LLM span created with ID: {llm_span_id}[/dim]")
        
        # Initialize results and conversation history
        results = []
        conversation_history = messages.copy()
        
        # Check if we have tool calls
        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            console.print("[bold yellow]No tool calls detected in the response[/bold yellow]")
            logger.conclude(
                output="I couldn't process your query. Please try again with a clearer request.",
                status_code=400
            )
            logger.flush()
            console.print("[green]Trace flushed successfully[/green]")
            return "I couldn't process your query. Please try again with a clearer request."
        
        # Add the assistant's response to the conversation history
        conversation_history.append({
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
        converted_values = {}
        has_arithmetic = any(op in query.lower() for op in ['+', '-', '*', '/', 'plus', 'minus', 'times', 'divide'])
        calculation_done = False
        
        # Store the last conversion span ID to use as parent for calculation
        last_conversion_span_id = None
        
        # First, process all convert_text_to_number calls
        for call in tool_calls:
            if call.function.name == "convert_text_to_number":
                text = json.loads(call.function.arguments)["text"]
                console.print(f"[yellow]Converting:[/yellow] {text}")
                
                # Call the function and get both result and duration
                number_str, duration_ns = convert_text_to_number(text)
                
                # Log the tool span immediately
                console.print(f"[blue]Creating tool span for convert_text_to_number[/blue]")
                conversion_span_id = logger.add_tool_span(
                    input=f"convert_text_to_number(text=\"{text}\")",
                    output=number_str,
                    name="convert_text_to_number",
                    duration_ns=duration_ns,
                    metadata={"text": text},
                    tool_call_id=call.id,
                    
                )
                console.print(f"[dim]Tool span created for convert_text_to_number with ID: {conversion_span_id}[/dim]")
                
                # Store the last conversion span ID
                last_conversion_span_id = conversion_span_id
                
                number = int(number_str) if number_str.isdigit() else None
                if number is not None:
                    console.print(f"[green]Converted to:[/green] {number}")
                    results.append(f"Converted '{text}' to {number}")
                    converted_values[text] = number
                    
                    # Add the tool response to conversation history
                    conversation_history.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": str(number)
                    })
        
        # Then, process all calculate calls
        for call in tool_calls:
            if call.function.name == "calculate":
                expression = json.loads(call.function.arguments)["expression"]
                console.print(f"[yellow]Calculating:[/yellow] {expression}")
                
                # Call the function and get both result and duration
                result, duration_ns = calculate(expression)
                
                # Log the tool span immediately
                console.print(f"[blue]Creating tool span for calculate[/blue]")
                
                # If we have a conversion span, make the calculate span its child
                parent_span_id = last_conversion_span_id if last_conversion_span_id else llm_span_id
                
                logger.add_tool_span(
                    input=f"calculate(expression=\"{expression}\")",
                    output=result,
                    name="calculate",
                    duration_ns=duration_ns,
                    metadata={"expression": expression},
                    tool_call_id=call.id,
                      # Use the last conversion span as parent if available
                )
                console.print(f"[dim]Tool span created for calculate with ID: {call.id} (parent: {parent_span_id})[/dim]")
                
                console.print(f"[green]Result:[/green] {result}")
                results.append(result)
                calculation_done = True
                
                # Add the tool response to conversation history
                conversation_history.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result
                })
        
        # If we have arithmetic but no calculation was done, make a follow-up request
        if has_arithmetic and not calculation_done and converted_values:
            console.print("[yellow]Calculation step missing - making follow-up request...[/yellow]")
            
            # Add a message requesting completion of the sequence
            conversation_history.append({
                "role": "user",
                "content": f"Now you must calculate the result using the converted numbers. The original query was: '{query}'"
            })
            
            # Make a follow-up request
            follow_up_start_time = time.time()
            follow_up = client.chat.completions.create(
                model="gpt-4o",
                messages=conversation_history,
                tools=tools,
            )
            follow_up_duration_ns = int((time.time() - follow_up_start_time) * 1_000_000_000)
            
            # Log the follow-up LLM span immediately
            console.print("[blue]Creating LLM span for follow-up request[/blue]")
            follow_up_span_id = logger.add_llm_span(
                input=conversation_history,
                output=follow_up.model_dump(),
                model="gpt-4o",
                tools=tools,
                name="follow_up_llm_call",
                duration_ns=follow_up_duration_ns
            )
            console.print(f"[dim]Follow-up LLM span created with ID: {follow_up_span_id}[/dim]")
            
            # Process any additional tool calls
            follow_up_tool_calls = follow_up.choices[0].message.tool_calls
            if follow_up_tool_calls:
                # Add the assistant's response to the conversation history
                conversation_history.append({
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
                        console.print(f"[yellow]Calculating:[/yellow] {expression}")
                        
                        # Call the function and get both result and duration
                        result, duration_ns = calculate(expression)
                        
                        # Log the tool span immediately
                        console.print(f"[blue]Creating tool span for calculate (follow-up)[/blue]")
                        
                        # For follow-up calculations, use the follow-up LLM span as parent
                        # If we have conversions from the first pass, we could also use the last conversion span
                        parent_span_id = last_conversion_span_id if last_conversion_span_id else follow_up_span_id
                        
                        logger.add_tool_span(
                            input=f"calculate(expression=\"{expression}\")",
                            output=result,
                            name="calculate",
                            duration_ns=duration_ns,
                            metadata={"expression": expression},
                            tool_call_id=call.id,
                              # Use the last conversion span or follow-up LLM span
                        )
                        console.print(f"[dim]Tool span created for calculate with ID: {call.id} (parent: {parent_span_id})[/dim]")
                        
                        console.print(f"[green]Result:[/green] {result}")
                        results.append(result)
                        calculation_done = True
                        
                        # Add the tool response to conversation history
                        conversation_history.append({
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
            if calculation_done:
                summary += f"Final answer: {final_answer}"
            else:
                summary += "\n".join(results)
        else:
            summary = "I couldn't process your query. Please try again with a clearer request."
        
        # Calculate total duration in nanoseconds
        total_duration_ns = int((time.time() - start_time) * 1_000_000_000)
        
        # Conclude the trace
        logger.conclude(
            output=summary,
            duration_ns=total_duration_ns
        )
        
        # Flush the traces to ensure they're sent to Galileo
        console.print("[blue]Flushing trace to Galileo...[/blue]")
        logger.flush()
        console.print("[green]Trace flushed successfully[/green]")
        
        console.print(f"[dim]Final results: {results}[/dim]")
        return summary
        
    except Exception as e:
        # Handle any exceptions
        console.print(f"[bold red]Error in process_query:[/bold red] {str(e)}")
        import traceback
        console.print(traceback.format_exc())
        
        # Conclude the trace with an error
        logger.conclude(
            output=f"Error: {str(e)}",
            status_code=500
        )    
        console.print("[yellow]Trace flushed with error status[/yellow]")
        return f"Error processing query: {str(e)}"

def main():    
    # Add a console header
    console.print("[bold]Number Converter & Calculator Agent[/bold]")
    console.print("Simple agent demonstrating Galileo integration with GalileoLogger")
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
        # Process the query and get the result within a Galileo context
        # This ensures all trace operations share the same context
        with galileo_context():
            result = process_query(query)
        
        console.print("\n[bold green]Result:[/bold green]")
        console.print(result)
        console.print("\n[bold]Exiting. Goodbye![/bold]")
            
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        import traceback
        console.print(traceback.format_exc())
        
        # Just flush any existing traces
        logger.flush()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold]Exiting. Goodbye![/bold]")
        # Flush any remaining traces
        logger.flush()
