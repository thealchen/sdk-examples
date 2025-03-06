import os
import json
import time
from galileo import galileo_context
from galileo.logger import GalileoLogger
from dotenv import load_dotenv
from rich.console import Console
import questionary

# Load environment variables
load_dotenv()

# Initialize console and logger
console = Console()
logger = GalileoLogger(project="simple-simulator", log_stream="dev")

# Define tool specifications similar to tools.json
def load_tool_specs():
    """
    Load tool specifications in the format expected by the LLM
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "convert_text_to_number",
                "description": "Converts text numbers (like 'seven') to digits (7)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text number to convert (e.g., 'seven', 'forty-two')"
                        }
                    },
                    "required": ["text"],
                    "additionalProperties": False
                },
                "strict": True
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "Performs arithmetic with numerical expressions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "The arithmetic expression to calculate (e.g., '4 + 7', '10 * 3')"
                        }
                    },
                    "required": ["expression"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }
    ]

# Mock function to simulate text-to-number conversion
def mock_convert_text_to_number(text):
    """
    Simulate converting a text number to a digit
    """
    start_time = time.time()
    
    # Simulate processing time
    time.sleep(0.5)
    
    # Simple mapping for common numbers
    number_map = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
        "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20
    }
    
    # Get the number or default to 42 if not found
    number = number_map.get(text.lower(), 42)
    
    # Calculate duration in nanoseconds
    duration_ns = int((time.time() - start_time) * 1_000_000_000)
    
    return str(number), duration_ns

# Mock function to simulate calculation
def mock_calculate(expression):
    """
    Simulate calculating an arithmetic expression
    """
    start_time = time.time()
    
    # Simulate processing time
    time.sleep(0.3)
    
    try:
        # Simple evaluation of the expression
        result = eval(expression)
        output = f"The result of {expression} is {result}"
    except Exception as e:
        output = f"Error calculating {expression}: {str(e)}"
    
    # Calculate duration in nanoseconds
    duration_ns = int((time.time() - start_time) * 1_000_000_000)
    
    return output, duration_ns

def process_query(query: str) -> str:
    """
    Process a numerical query using simulated LLM and tools.
    This function follows the same pattern as tool-span-test.py.
    """
    console.print("[bold blue]Processing query...[/bold blue]")
    console.print(f"Query: {query}")
    
    # Start a trace for the query processing
    trace_id = logger.start_trace(query)
    console.print(f"[blue]Started trace with ID: {trace_id}[/blue]")
    
    start_time = time.time()
    
    try:
        # Load tools
        tools = load_tool_specs()
        console.print(f"[dim]Loaded {len(tools)} tools[/dim]")
        
        # Simulate LLM processing time
        time.sleep(1)
        llm_duration_ns = int(1 * 1_000_000_000)  # 1 second in nanoseconds
        
        # Parse the query to determine what tools to call
        has_arithmetic = any(op in query.lower() for op in ['+', '-', '*', '/', 'plus', 'minus', 'times', 'divide'])
        
        # Mock LLM input
        mock_llm_input = [
            {
                "role": "system",
                "content": "You are an agent that processes numerical queries using tools."
            },
            {"role": "user", "content": query}
        ]
        
        # Mock LLM output with tool calls
        mock_tool_calls = []
        
        # Extract text numbers from the query (improved logic)
        text_numbers = []
        query_lower = query.lower()
        
        # Define a more comprehensive list of text numbers to check for
        number_words = [
            "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
            "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"
        ]
        
        # Check for each number word in the query
        for word in number_words:
            if word in query_lower:
                text_numbers.append(word)
        
        console.print(f"[dim]Detected text numbers: {text_numbers}[/dim]")
        
        # Create tool calls for text number conversion
        for i, text_number in enumerate(text_numbers):
            mock_tool_calls.append({
                "id": f"call_convert_{i}",
                "type": "function",
                "function": {
                    "name": "convert_text_to_number",
                    "arguments": json.dumps({"text": text_number})
                }
            })
        
        # If we have arithmetic, add a calculate tool call
        if has_arithmetic:
            # We'll add the calculation tool call after processing the conversions
            calculation_needed = True
        else:
            calculation_needed = False
        
        # Mock LLM output
        mock_llm_output = {
            "id": "mock-completion-id-1",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "gpt-4o-mock",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "I'll process this query for you.",
                        "tool_calls": mock_tool_calls
                    },
                    "finish_reason": "tool_calls"
                }
            ]
        }
        
        # Log the LLM span for tool selection
        console.print("[blue]Creating LLM span for tool selection[/blue]")
        logger.add_llm_span(
            input=mock_llm_input,
            output=mock_llm_output,
            model="gpt-4o-mock",
            tools=tools,
            name="agent_llm_call",
            duration_ns=llm_duration_ns
        )
        
        # Initialize results and conversation history
        results = []
        conversation_history = mock_llm_input.copy()
        
        # Add the assistant's response to the conversation history
        conversation_history.append({
            "role": "assistant",
            "content": mock_llm_output["choices"][0]["message"]["content"],
            "tool_calls": [
                {
                    "id": call["id"],
                    "type": "function",
                    "function": {
                        "name": call["function"]["name"],
                        "arguments": call["function"]["arguments"]
                    }
                } for call in mock_tool_calls
            ]
        })
        
        # Process each tool call
        converted_values = {}
        
        for call in mock_tool_calls:
            if call["function"]["name"] == "convert_text_to_number":
                text = json.loads(call["function"]["arguments"])["text"]
                console.print(f"[yellow]Converting:[/yellow] {text}")
                
                # Call the mock function
                number_str, duration_ns = mock_convert_text_to_number(text)
                
                # Log the tool span
                console.print(f"[blue]Creating tool span for convert_text_to_number[/blue]")
                logger.add_tool_span(
                    input=f"convert_text_to_number(text=\"{text}\")",
                    output=number_str,
                    name="convert_text_to_number",
                    duration_ns=duration_ns,
                    metadata={"text": text},
                    tool_call_id=call["id"]
                )
                console.print(f"[dim]Tool span created for convert_text_to_number with ID: {call['id']}[/dim]")
                
                number = int(number_str)
                console.print(f"[green]Converted to:[/green] {number}")
                results.append(f"Converted '{text}' to {number}")
                converted_values[text] = number
                
                # Add the tool response to conversation history
                conversation_history.append({
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": str(number)
                })
        
        # If we need to calculate, create a follow-up request
        if calculation_needed and converted_values:
            # Create an expression based on the query and converted values
            expression = query.lower()
            for text, number in converted_values.items():
                expression = expression.replace(text, str(number))
            
            # Extract just the arithmetic expression (improved logic)
            # First, try to find a simple expression with digits and operators
            import re
            arithmetic_matches = re.findall(r'\d+\s*[\+\-\*\/]\s*\d+', expression)
            
            if arithmetic_matches:
                expression = arithmetic_matches[0]
            else:
                # If no clear expression is found, construct one from the query
                # For "What's 4 + seven?" where seven is converted to 7, create "4 + 7"
                digits = re.findall(r'\d+', expression)
                if len(digits) >= 2 and '+' in expression:
                    expression = f"{digits[0]} + {digits[1]}"
                elif len(digits) >= 2 and '-' in expression:
                    expression = f"{digits[0]} - {digits[1]}"
                elif len(digits) >= 2 and '*' in expression or 'times' in expression:
                    expression = f"{digits[0]} * {digits[1]}"
                elif len(digits) >= 2 and '/' in expression or 'divided' in expression:
                    expression = f"{digits[0]} / {digits[1]}"
                # Fallback for "What's 4 + seven?"
                elif "what's" in expression.lower() and "+" in expression and len(digits) >= 2:
                    expression = f"{digits[0]} + {digits[1]}"
                else:
                    # If we couldn't extract a clean expression, create a simple one
                    numbers = list(converted_values.values())
                    if len(numbers) >= 2:
                        expression = f"{numbers[0]} + {numbers[1]}"
                    else:
                        # For "What's 4 + seven?" specifically
                        if "4 + 7" in expression or "4+7" in expression:
                            expression = "4 + 7"
                        else:
                            expression = f"{numbers[0]} + 5"  # Default
            
            console.print(f"[dim]Extracted expression: {expression}[/dim]")
            
            # Create a mock follow-up LLM call
            follow_up_start_time = time.time()
            time.sleep(0.8)  # Simulate processing time
            follow_up_duration_ns = int(0.8 * 1_000_000_000)  # 0.8 seconds in nanoseconds
            
            # Mock follow-up tool call
            mock_follow_up_tool_call = {
                "id": "call_calculate_1",
                "type": "function",
                "function": {
                    "name": "calculate",
                    "arguments": json.dumps({"expression": expression})
                }
            }
            
            # Mock follow-up LLM output
            mock_follow_up_output = {
                "id": "mock-completion-id-2",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "gpt-4o-mock",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Now I'll calculate the result.",
                            "tool_calls": [mock_follow_up_tool_call]
                        },
                        "finish_reason": "tool_calls"
                    }
                ]
            }
            
            # Add a message requesting calculation
            conversation_history.append({
                "role": "user",
                "content": f"Now calculate the result using the converted numbers. The original query was: '{query}'"
            })
            
            # Log the follow-up LLM span
            console.print("[blue]Creating LLM span for follow-up request[/blue]")
            logger.add_llm_span(
                input=conversation_history,
                output=mock_follow_up_output,
                model="gpt-4o-mock",
                tools=tools,
                name="follow_up_llm_call",
                duration_ns=follow_up_duration_ns
            )
            
            # Add the assistant's response to the conversation history
            conversation_history.append({
                "role": "assistant",
                "content": mock_follow_up_output["choices"][0]["message"]["content"],
                "tool_calls": [
                    {
                        "id": mock_follow_up_tool_call["id"],
                        "type": "function",
                        "function": {
                            "name": mock_follow_up_tool_call["function"]["name"],
                            "arguments": mock_follow_up_tool_call["function"]["arguments"]
                        }
                    }
                ]
            })
            
            # Process the calculate tool call
            console.print(f"[yellow]Calculating:[/yellow] {expression}")
            
            # Call the mock function
            result, duration_ns = mock_calculate(expression)
            
            # Log the tool span
            console.print(f"[blue]Creating tool span for calculate[/blue]")
            logger.add_tool_span(
                input=f"calculate(expression=\"{expression}\")",
                output=result,
                name="calculate",
                duration_ns=duration_ns,
                metadata={"expression": expression},
                tool_call_id=mock_follow_up_tool_call["id"]
            )
            console.print(f"[dim]Tool span created for calculate with ID: {mock_follow_up_tool_call['id']}[/dim]")
            
            console.print(f"[green]Result:[/green] {result}")
            results.append(result)
            
            # Add the tool response to conversation history
            conversation_history.append({
                "role": "tool",
                "tool_call_id": mock_follow_up_tool_call["id"],
                "content": result
            })
            
            # Create a final summary LLM call to simulate the final result
            summary_start_time = time.time()
            time.sleep(0.5)  # Simulate processing time
            summary_duration_ns = int(0.5 * 1_000_000_000)  # 0.5 seconds in nanoseconds
            
            # Extract the calculation result from the output
            calculation_result = result
            if "result of" in result and "is" in result:
                calculation_result = result.split("is")[-1].strip()
            
            # Create a simulated final summary
            final_summary = f"I've processed your query '{query}'.\n\n"
            
            # Add information about text number conversions
            if converted_values:
                final_summary += "Text number conversions:\n"
                for text, number in converted_values.items():
                    final_summary += f"- '{text}' → {number}\n"
                final_summary += "\n"
            
            # Add calculation result if available
            if calculation_needed:
                final_summary += f"Calculation: {expression} = {calculation_result}\n\n"
            
            # Add final answer
            final_summary += f"Final answer: {calculation_result}"
            
            # Mock summary LLM output
            mock_summary_output = {
                "id": "mock-completion-id-3",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "gpt-4o-mock",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": final_summary
                        },
                        "finish_reason": "stop"
                    }
                ]
            }
            
            # Add a message requesting a summary
            conversation_history.append({
                "role": "user",
                "content": "Please provide a summary of the results."
            })
            
            # Log the summary LLM span
            console.print("[blue]Creating LLM span for final summary[/blue]")
            logger.add_llm_span(
                input=conversation_history,
                output=mock_summary_output,
                model="gpt-4o-mock",
                name="summary_llm_call",
                duration_ns=summary_duration_ns
            )
            
            # Add the final summary to the results
            results.append(final_summary)
            
            # Add the assistant's response to the conversation history
            conversation_history.append({
                "role": "assistant",
                "content": final_summary
            })
        
        # Calculate total duration in nanoseconds
        end_time = time.time()
        total_duration_ns = int((end_time - start_time) * 1e9)
        logger.set_trace_duration(total_duration_ns)
        
        # Conclude the trace
        final_result = results[-1] if results else "I couldn't process your query. Please try again with a clearer request."
        logger.conclude(
            output=final_result,
            duration_ns=total_duration_ns
        )
        
        # Flush the traces to ensure they are sent to Galileo
        console.print(f"[blue]Flushing trace to Galileo...[/blue]")
        logger.flush()
        console.print(f"[green]Trace flushed successfully[/green]")
        
        console.print(f"[dim]Final results: {results}[/dim]")
        return final_result
        
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
        logger.flush()
        return f"Error processing query: {str(e)}"

def main():    
    # Add a console header
    console.print("[bold]Number Converter & Calculator Simulator[/bold]")
    console.print("Simple agent simulator demonstrating Galileo integration with GalileoLogger")
    console.print("Type your query or 'exit' to quit\n")
    
    # Process a single query and exit
    query = questionary.text(
        "Enter your query:",
        default="What's 4 + seven?"
    ).ask()
    
    if query.lower() in ['exit', 'quit', 'q']:
        console.print("\n[bold]Exiting. Goodbye![/bold]")
        return
        
    try:
        # Process the query and get the result within a Galileo context
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
 