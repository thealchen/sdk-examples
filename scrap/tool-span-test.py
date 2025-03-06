import os
import json
import time
from galileo import galileo_context
from galileo.logger import GalileoLogger
from dotenv import load_dotenv
from rich.console import Console

# Load environment variables
load_dotenv()

# Initialize console and logger
console = Console()
logger = GalileoLogger(project="tool-span-test", log_stream="dev")

# Define tool specifications similar to tools.json
def load_tool_specs():
    """
    Load tool specifications in the format expected by the LLM
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "get_capital",
                "description": "Get the capital city of a country.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "country": {
                            "type": "string",
                            "description": "The name of the country (e.g., 'France', 'Japan')"
                        }
                    },
                    "required": ["country"],
                    "additionalProperties": False
                },
                "strict": True
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_population",
                "description": "Get the approximate population of a country.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "country": {
                            "type": "string",
                            "description": "The name of the country (e.g., 'France', 'Japan')"
                        }
                    },
                    "required": ["country"],
                    "additionalProperties": False
                },
                "strict": True
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_currency",
                "description": "Get the currency used in a country.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "country": {
                            "type": "string",
                            "description": "The name of the country (e.g., 'France', 'Japan')"
                        }
                    },
                    "required": ["country"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }
    ]

def mock_tool_function(tool_name, **kwargs):
    """
    A mock tool function that simulates processing some input
    """
    console.print(f"[yellow]Tool function processing:[/yellow] {tool_name}({kwargs})")
    
    # Simulate some processing time
    time.sleep(0.5)
    
    # Return different results based on the tool name
    if tool_name == "get_capital":
        country = kwargs.get("country", "unknown")
        capitals = {
            "France": "Paris",
            "Japan": "Tokyo",
            "Brazil": "Brasília",
            "Australia": "Canberra"
        }
        return f"The capital of {country} is {capitals.get(country, 'unknown')}"
    
    elif tool_name == "get_population":
        country = kwargs.get("country", "unknown")
        populations = {
            "France": "67 million",
            "Japan": "126 million",
            "Brazil": "213 million",
            "Australia": "25 million"
        }
        return f"The population of {country} is approximately {populations.get(country, 'unknown')}"
    
    elif tool_name == "get_currency":
        country = kwargs.get("country", "unknown")
        currencies = {
            "France": "Euro (EUR)",
            "Japan": "Japanese Yen (JPY)",
            "Brazil": "Brazilian Real (BRL)",
            "Australia": "Australian Dollar (AUD)"
        }
        return f"The currency of {country} is {currencies.get(country, 'unknown')}"
    
    else:
        return f"Unknown tool: {tool_name}"

def run_simple_agent():
    """
    Run a simple agent that creates a trace, an LLM span for tool selection, and multiple tool spans
    """
    # Create a trace for the entire interaction
    query = "Tell me about France: its capital, population, and currency."
    console.print(f"[bold blue]Processing query:[/bold blue] {query}")
    
    # Start a trace
    trace = logger.start_trace(
        input=query,
        name="multi_tool_agent_trace"
    )
    
    start_time = time.time()
    
    # Load tool specifications
    tools = load_tool_specs()
    console.print(f"[dim]Loaded {len(tools)} tools[/dim]")
    
    # Mock LLM input for tool selection (messages)
    mock_llm_input = [
        {
            "role": "system",
            "content": """You are a helpful assistant with access to tools.
For queries about countries, use the appropriate tools to gather information.
Always use tools when they are available for the requested information."""
        },
        {"role": "user", "content": query}
    ]
    
    # Mock LLM output for tool selection
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
                    "content": "I'll help you find information about France.",
                    "tool_calls": [
                        {
                            "id": "call_capital_123",
                            "type": "function",
                            "function": {
                                "name": "get_capital",
                                "arguments": json.dumps({"country": "France"})
                            }
                        },
                        {
                            "id": "call_population_456",
                            "type": "function",
                            "function": {
                                "name": "get_population",
                                "arguments": json.dumps({"country": "France"})
                            }
                        },
                        {
                            "id": "call_currency_789",
                            "type": "function",
                            "function": {
                                "name": "get_currency",
                                "arguments": json.dumps({"country": "France"})
                            }
                        }
                    ]
                },
                "finish_reason": "tool_calls"
            }
        ],
        "usage": {
            "prompt_tokens": 25,
            "completion_tokens": 20,
            "total_tokens": 45
        }
    }
    
    # Simulate LLM processing time
    time.sleep(1)
    llm_duration_ns = int((time.time() - start_time) * 1_000_000_000)
    
    # Log the LLM span for tool selection
    console.print("[blue]Creating LLM span for tool selection[/blue]")
    logger.add_llm_span(
        input=mock_llm_input,
        output=mock_llm_output,
        model="gpt-4o-mock",
        tools=tools,  # Include the tool specifications
        name="tool_selection_llm_call",
        duration_ns=llm_duration_ns,
        num_input_tokens=25,
        num_output_tokens=20,
        total_tokens=45
    )
    
    # Initialize message history for the conversation
    messages = mock_llm_input.copy()
    
    # Add the assistant's response to the message history
    messages.append({
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
            } for call in mock_llm_output["choices"][0]["message"]["tool_calls"]
        ]
    })
    
    # Process each tool call
    tool_results = []
    tool_calls = mock_llm_output["choices"][0]["message"]["tool_calls"]
    
    for tool_call in tool_calls:
        tool_name = tool_call["function"]["name"]
        tool_args = json.loads(tool_call["function"]["arguments"])
        
        # Process the tool call
        console.print(f"[green]Processing tool call:[/green] {tool_name}({tool_args})")
        
        # Start timing the tool call
        tool_start_time = time.time()
        
        # Call the mock tool function
        tool_input = f"{tool_name}(country={tool_args['country']})"
        tool_output = mock_tool_function(tool_name, **tool_args)
        
        # Store the result
        tool_results.append(tool_output)
        
        # Calculate tool duration
        tool_duration_ns = int((time.time() - tool_start_time) * 1_000_000_000)
        
        # Log the tool span
        console.print(f"[blue]Creating tool span for {tool_name}[/blue]")
        logger.add_tool_span(
            input=tool_input,
            output=tool_output,
            name=tool_name,
            duration_ns=tool_duration_ns,
            metadata=tool_args,
            tool_call_id=tool_call["id"]
        )
        
        # Add the tool response to message history
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": tool_output
        })
    
    # Now create a second LLM call to summarize the results
    summarize_start_time = time.time()
    
    # Add a user message requesting summarization
    messages.append({
        "role": "user",
        "content": "Please summarize this information about France."
    })
    
    # Mock LLM output for summarization
    mock_summarize_output = {
        "id": "mock-completion-id-2",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "gpt-4o-mock",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Here's a summary about France:\n\n- Capital: Paris\n- Population: Approximately 67 million\n- Currency: Euro (EUR)\n\nFrance is a country in Western Europe known for its art, culture, cuisine, and landmarks like the Eiffel Tower."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 150,
            "completion_tokens": 50,
            "total_tokens": 200
        }
    }
    
    # Simulate LLM processing time
    time.sleep(1.5)
    summarize_duration_ns = int((time.time() - summarize_start_time) * 1_000_000_000)
    
    # Log the LLM span for summarization
    console.print("[blue]Creating LLM span for summarization[/blue]")
    logger.add_llm_span(
        input=messages,
        output=mock_summarize_output,
        model="gpt-4o-mock",
        name="summarization_llm_call",
        duration_ns=summarize_duration_ns,
        num_input_tokens=150,
        num_output_tokens=50,
        total_tokens=200
    )
    
    # Add the final response to message history
    messages.append({
        "role": "assistant",
        "content": mock_summarize_output["choices"][0]["message"]["content"]
    })
    
    # Calculate total duration
    total_duration_ns = int((time.time() - start_time) * 1_000_000_000)
    
    # Get the final result from the summarization
    final_result = mock_summarize_output["choices"][0]["message"]["content"]
    
    # Conclude the trace
    logger.conclude(
        output=final_result,
        duration_ns=total_duration_ns
    )
    
    # Flush the traces to ensure they're sent to Galileo
    logger.flush()
    
    console.print(f"[bold green]Final result:[/bold green] {final_result}")
    console.print("[dim]Trace, LLM spans, and tool spans created and logged to Galileo.[/dim]")
    console.print("[dim]Complete conversation history has been properly maintained.[/dim]")

if __name__ == "__main__":
    try:
        console.print("[bold]Multi-Tool Span Test[/bold]")
        console.print("Demonstrating trace, LLM spans, and multiple tool spans with mock data\n")
        
        # Run the agent within a Galileo context
        with galileo_context():
            run_simple_agent()
            
    except KeyboardInterrupt:
        console.print("\n[bold]Exiting. Goodbye![/bold]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        import traceback
        console.print(traceback.format_exc())
    finally:
        # Ensure all traces are flushed
        logger.flush()
