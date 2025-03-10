import os
from dotenv import load_dotenv
from galileo import openai, log, GalileoLogger
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
import questionary
import sys

load_dotenv()

# Initialize console for rich output
console = Console()

# Check if Galileo logging is enabled
logging_enabled = os.environ.get("GALILEO_API_KEY") is not None

logger = GalileoLogger(
    project="out-of-context",    
    log_stream="dev",
)
# Initialize OpenAI client
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@log(span_type="retriever")
def retrieve_documents(query: str):
    """
    Simulated document retrieval that intentionally returns incomplete information
    to demonstrate the out-of-context problem.
    """
    # Dictionary of queries and their intentionally incomplete contexts
    incomplete_contexts = {
        "eiffel tower": [
            {
                "id": "doc1",
                "text": "The Eiffel Tower is an iron lattice tower located in Paris, France. It was designed by Gustave Eiffel.",
                "metadata": {
                    "source": "travel_guide",
                    "category": "landmarks"
                }
            }
        ],
        "python language": [
            {
                "id": "doc1",
                "text": "Python is a high-level programming language known for its readability and simple syntax.",
                "metadata": {
                    "source": "programming_guide",
                    "category": "languages"
                }
            }
        ],
        "climate change": [
            {
                "id": "doc1",
                "text": "Climate change refers to long-term shifts in temperatures and weather patterns. Human activities have been the main driver of climate change since the 1800s.",
                "metadata": {
                    "source": "environmental_science",
                    "category": "global_issues"
                }
            }
        ],
        "artificial intelligence": [
            {
                "id": "doc1",
                "text": "Artificial intelligence involves creating systems capable of performing tasks that typically require human intelligence.",
                "metadata": {
                    "source": "technology_overview",
                    "category": "ai"
                }
            }
        ],
        "quantum computing": [
            {
                "id": "doc1",
                "text": "Quantum computing uses quantum bits or qubits that can represent multiple states simultaneously.",
                "metadata": {
                    "source": "computing_technology",
                    "category": "quantum"
                }
            }
        ]
    }
    
    # Default case for queries not in our predefined list
    default_docs = [
        {
            "id": "default_doc",
            "text": "This is a generic response with limited information about the query topic.",
            "metadata": {
                "source": "general_knowledge",
                "category": "miscellaneous"
            }
        }
    ]
    
    # Find the most relevant predefined query
    for key in incomplete_contexts:
        if key in query.lower():
            return incomplete_contexts[key]
    
    return default_docs

@log
def rag_with_hallucination(query: str):
    """
    RAG implementation that demonstrates the out-of-context problem by using
    a system prompt that doesn't properly constrain the model.
    """
    documents = retrieve_documents(query)
    
    # Format documents for better readability in the prompt
    formatted_docs = ""
    for i, doc in enumerate(documents):
        formatted_docs += f"Document {i+1} (Source: {doc['metadata']['source']}):\n{doc['text']}\n\n"

    # This prompt doesn't strongly constrain the model to only use the provided context
    weak_prompt = f"""
    Answer the following question based on the context provided.
    
    Question: {query}

    Context:
    {formatted_docs}
    """

    try:
        console.print("[bold blue]Generating answer (prone to out-of-context information)...[/bold blue]")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": weak_prompt}
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating response: {str(e)}"

@log
def rag_with_constraint(query: str):
    """
    RAG implementation that demonstrates how to mitigate the out-of-context problem
    by using a stronger system prompt and explicit instructions.
    """
    documents = retrieve_documents(query)
    
    # Format documents for better readability in the prompt
    formatted_docs = ""
    for i, doc in enumerate(documents):
        formatted_docs += f"Document {i+1} (Source: {doc['metadata']['source']}):\n{doc['text']}\n\n"

    # This prompt strongly constrains the model to only use the provided context
    strong_prompt = f"""
    Answer the following question based STRICTLY on the context provided. 
    If the information needed to answer the question is not explicitly contained in the context, 
    respond with: "I don't have enough information in the provided context to answer this question."
    
    DO NOT use any knowledge outside of the provided context.
    
    Question: {query}

    Context:
    {formatted_docs}
    """

    try:
        console.print("[bold green]Generating answer (constrained to context)...[/bold green]")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that ONLY answers based on the provided context. Never use external knowledge."},
                {"role": "user", "content": strong_prompt}
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating response: {str(e)}"

@log
def main():

    console.print(Panel.fit(
        "[bold]Out-of-Context RAG Demo[/bold]\nThis demo shows how RAG systems can generate out-of-context information and how to prevent it.",
        title="Galileo RAG Challenge: Out-of-Context Information",
        border_style="red"
    ))
    
    # Check environment setup
    if logging_enabled:
        console.print("[green]✅ Galileo logging is enabled[/green]")
    else:
        console.print("[yellow]⚠️ Galileo logging is disabled[/yellow]")
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        console.print("[green]✅ OpenAI API Key is set[/green]")
    else:
        console.print("[red]❌ OpenAI API Key is missing[/red]")
        sys.exit(1)
    
    # Suggested queries
    suggested_queries = [
        "When was the Eiffel Tower completed?",
        "Who created the Python language and when?",
        "What are the main effects of climate change?",
        "When was artificial intelligence first developed?",
        "How many qubits are in the most powerful quantum computer?"
    ]
    
    console.print("\n[bold yellow]Suggested queries (these will demonstrate the problem):[/bold yellow]")
    for i, q in enumerate(suggested_queries):
        console.print(f"[yellow]{i+1}. {q}[/yellow]")
    
    # Main interaction loop
    while True:
        # Get user query
        query = questionary.text(
            "Enter your question (or type a number 1-5 to use a suggested query):",
            validate=lambda text: len(text) > 0
        ).ask()
        
        if query.lower() in ['exit', 'quit', 'q']:
            break
            
        # Check if user entered a number for suggested queries
        if query.isdigit() and 1 <= int(query) <= len(suggested_queries):
            query = suggested_queries[int(query)-1]
            console.print(f"[bold]Using query:[/bold] {query}")
        
        try:
            # Generate both types of responses
            hallucinated_result = rag_with_hallucination(query)
            constrained_result = rag_with_constraint(query)
            
            # Display the retrieved context
            documents = retrieve_documents(query)
            console.print("\n[bold cyan]Retrieved Context:[/bold cyan]")
            for i, doc in enumerate(documents):
                console.print(Panel(
                    f"[bold]Source:[/bold] {doc['metadata']['source']}\n\n{doc['text']}",
                    title=f"Document {i+1}",
                    border_style="cyan"
                ))
            
            # Display the hallucinated response
            console.print("\n[bold red]Unconstrained Response (Prone to Out-of-Context Information):[/bold red]")
            console.print(Panel(Markdown(hallucinated_result), border_style="red"))
            
            # Display the constrained response
            console.print("\n[bold green]Constrained Response (Limited to Context):[/bold green]")
            console.print(Panel(Markdown(constrained_result), border_style="green"))
            
            # Explain the difference
            console.print("\n[bold yellow]Analysis:[/bold yellow]")
            console.print(Panel(
                "The unconstrained response may include information not present in the retrieved context, "
                "demonstrating the out-of-context problem. The constrained response is limited to only "
                "information explicitly provided in the context, reducing hallucinations but potentially "
                "providing less complete answers.",
                border_style="yellow"
            ))
            
            # Ask if user wants to continue
            continue_session = questionary.confirm(
                "Do you want to ask another question?",
                default=True
            ).ask()
            
            if not continue_session:
                break
                
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold]Exiting Out-of-Context RAG Demo. Goodbye![/bold]")
