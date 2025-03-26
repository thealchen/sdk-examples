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

print(os.environ.get("GALILEO_API_KEY"))

logger = GalileoLogger(
    project="chunk-utilization",    
    log_stream="dev",
)
# Initialize OpenAI client
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@log(span_type="retriever")
def retrieve_verbose_documents(query: str):
    """
    Simulated document retrieval that intentionally returns overly verbose chunks
    to demonstrate the chunk utilization problem.
    """
    # Dictionary of queries and their intentionally verbose contexts
    verbose_contexts = {
        "solar system": [
            {
                "id": "doc1",
                "text": "The Solar System is the gravitationally bound system of the Sun and the objects that orbit it. It formed 4.6 billion years ago from the gravitational collapse of a giant interstellar molecular cloud. The vast majority of the system's mass is in the Sun, with most of the remaining mass contained in the planet Jupiter. The four inner system planets—Mercury, Venus, Earth and Mars—are terrestrial planets, being composed primarily of rock and metal. The four giant planets of the outer system are substantially larger and more massive than the terrestrials. The two largest, Jupiter and Saturn, are gas giants, being composed mainly of hydrogen and helium; the next two, Uranus and Neptune, are ice giants, being composed mostly of volatile substances with relatively high melting points compared with hydrogen and helium, such as water, ammonia, and methane. All eight planets have nearly circular orbits that lie near the plane of Earth's orbit, called the ecliptic. The Solar System also contains other objects, including natural satellites (moons), dwarf planets (including Pluto, Ceres, and Eris), asteroids, comets, meteoroids, and interplanetary dust. Six of the primary planets, the six largest possible dwarf planets, and many of the smaller bodies are orbited by natural satellites, commonly called 'moons' after the Moon. Each of the outer planets is encircled by planetary rings of ice, dust, and other small particles.",
                "metadata": {
                    "source": "astronomy_encyclopedia",
                    "category": "planetary systems"
                }
            }
        ],
        "photosynthesis": [
            {
                "id": "doc1",
                "text": "Photosynthesis is the process by which plants, algae, and certain bacteria convert light energy, typically from the Sun, into chemical energy in the form of glucose or other sugars. These organisms are called photoautotrophs since they can create their own food. The glucose created provides the organisms energy to carry on with various life processes. Photosynthesis maintains atmospheric oxygen levels and supplies most of the energy necessary for life on Earth. Although photosynthesis is performed differently by different species, the process always begins when energy from light is absorbed by proteins called reaction centers that contain green chlorophyll (and related) pigments. In plants, these proteins are held inside organelles called chloroplasts, which are most abundant in leaf cells, while in bacteria they are embedded in the plasma membrane. In these light-dependent reactions, some energy is used to strip electrons from suitable substances, such as water, producing oxygen gas. The hydrogen freed by water splitting is transferred in the form of NADPH for use in the subsequent reactions. In the Calvin cycle, atmospheric carbon dioxide is incorporated into already existing organic carbon compounds, such as ribulose bisphosphate (RuBP). Using the ATP and NADPH produced by the light-dependent reactions, the resulting compounds are then reduced and removed to form further carbohydrates, such as glucose. The overall equation for the light-dependent and light-independent reactions of photosynthesis is: 6 CO₂ + 6 H₂O + light energy → C₆H₁₂O₆ + 6 O₂. The overall process consumes water, carbon dioxide, and sunlight, and produces glucose and oxygen as a by-product. In plants, algae and cyanobacteria, sugars are produced by the Calvin cycle, also known as the Calvin-Benson cycle, where carbon dioxide from the atmosphere is converted into simple sugars. The mechanism of photosynthesis varies by species as well, based on the availability of sunlight, water, and carbon dioxide. Some species adapt to low-light environments, while others thrive in high-light conditions.",
                "metadata": {
                    "source": "biology_textbook",
                    "category": "cellular processes"
                }
            }
        ],
        "blockchain": [
            {
                "id": "doc1",
                "text": "A blockchain is a distributed ledger with growing lists of records (blocks) that are securely linked together via cryptographic hashes. Each block contains a cryptographic hash of the previous block, a timestamp, and transaction data (generally represented as a Merkle tree). The timestamp proves that the transaction data existed when the block was published to get into its hash. As blocks each contain information about the previous block, they form a chain, with each additional block reinforcing the ones before it. Therefore, blockchains are resistant to modification of their data because once recorded, the data in any given block cannot be altered retroactively without altering all subsequent blocks. Blockchains are typically managed by a peer-to-peer network for use as a publicly distributed ledger, where nodes collectively adhere to a protocol to communicate and validate new blocks. Although blockchain records are not unalterable as forks are possible, blockchains may be considered secure by design and exemplify a distributed computing system with high Byzantine fault tolerance. The blockchain was popularized by a person (or group of people) using the name Satoshi Nakamoto in 2008 to serve as the public transaction ledger of the cryptocurrency bitcoin, based on work by Stuart Haber, W. Scott Stornetta, and Dave Bayer. The identity of Satoshi Nakamoto remains unknown to date. The implementation of the blockchain within bitcoin made it the first digital currency to solve the double-spending problem without the need of a trusted authority or central server. The bitcoin design has inspired other applications and blockchains that are readable by the public and are widely used by cryptocurrencies. Private blockchains have been proposed for business use. Some marketing for blockchains has been called 'snake oil' due to their inability to solve many of the problems that their advertising claims they will solve.",
                "metadata": {
                    "source": "technology_journal",
                    "category": "distributed systems"
                }
            }
        ],
        "renaissance": [
            {
                "id": "doc1",
                "text": "The Renaissance was a period in European history marking the transition from the Middle Ages to modernity and covering the 15th and 16th centuries. In addition to the standard periodization, proponents of a 'long Renaissance' may include the 14th century and the 17th century. The traditional view focuses more on the early modern aspects of the Renaissance and argues that it was a break from the past, but many historians today focus more on its medieval aspects and argue that it was an extension of the Middle Ages. However, the beginnings of the period – the early Renaissance of the 15th century and the Italian Proto-Renaissance from around 1250 or 1300 – overlap considerably with the Late Middle Ages, conventionally dated to c. 1250–1500, and the Middle Ages themselves were a long period filled with gradual changes, like the modern age; for this reason, some historians have suggested doing away with the tripartite periodization (Antiquity, Middle Ages, and modern period) altogether. The Renaissance began in Italy in the 14th century, and spread throughout the rest of Europe in the 15th and 16th centuries. The traditional view is that the Renaissance began in Florence, in the 14th century. Various theories have been proposed to account for its origins and characteristics, focusing on a variety of factors including the social and civic peculiarities of Florence at the time; its political structure; the patronage of the Medici; and the migration of Greek scholars and their texts to Italy following the Fall of Constantinople in 1453. Other major centers were northern Italian city-states such as Venice, Genoa, Milan, Bologna, and Rome during the Renaissance Papacy. The Renaissance has a long and complex historiography, and, in line with general skepticism of discrete periodizations, there has been much debate among historians reacting to the 19th-century glorification of the 'Renaissance' and individual cultural heroes as 'Renaissance men', questioning the usefulness of Renaissance as a term and as a historical delineation.",
                "metadata": {
                    "source": "history_encyclopedia",
                    "category": "european history"
                }
            }
        ],
        "machine learning": [
            {
                "id": "doc1",
                "text": "Machine learning (ML) is a field of study in artificial intelligence concerned with the development and study of statistical algorithms that can learn from data and generalize to unseen data, and thus perform tasks without explicit instructions. Recently, generative artificial intelligence applications have become well-known to the public. Machine learning approaches have been applied to large language models, computer vision, speech recognition, email filtering, agriculture, and medicine, where it is too costly to develop algorithms to perform the needed tasks. The mathematical foundations of ML are provided by mathematical optimization (mathematical programming) methods. Data mining is a related field of study, focusing on exploratory data analysis through unsupervised learning. Machine learning involves computers discovering how they can perform tasks without being explicitly programmed to do so. For simple tasks assigned to computers, it is possible to program algorithms telling the machine how to execute all steps required to solve the problem at hand; on the computer's part, no learning is needed. For more advanced tasks, it can be challenging for a human to manually create the needed algorithms. In practice, it can turn out to be more effective to help the machine develop its own algorithm, rather than having human programmers specify every needed step. The discipline of machine learning employs various approaches to teach computers to accomplish tasks where no fully satisfactory algorithm is available. In cases where vast numbers of potential answers exist, one approach is to label some of the correct answers as valid. This can then be used as training data for the computer to improve the algorithm(s) it uses to determine correct answers. Machine learning approaches are traditionally divided into three broad categories, depending on the nature of the 'signal' or 'feedback' available to the learning system: Supervised learning, Unsupervised learning, and Reinforcement learning. However, Machine Learning is now generally understood as only one part of a broader field, Artificial Intelligence, which includes many other elements like knowledge representations, natural language processing, planning, robotics, and symbolic AI, even if Machine Learning and AI are often conflated in public discussions.",
                "metadata": {
                    "source": "computer_science_journal",
                    "category": "artificial intelligence"
                }
            }
        ]
    }
    
    # Default case for queries not in our predefined list
    default_docs = [
        {
            "id": "default_doc",
            "text": "This is a generic document with excessive details but limited relevant information. It contains many paragraphs of text that go into great detail about various aspects of the topic, providing historical context, technical specifications, methodological approaches, theoretical frameworks, practical applications, and comparative analyses. Despite its length and apparent comprehensiveness, the key information that would directly answer the query is buried within verbose explanations and tangential discussions that make it difficult to extract the specific details needed to provide a concise and accurate response. The document includes references to related subjects, background information, and contextual factors that, while potentially interesting, do not contribute significantly to addressing the core information need expressed in the query.",
            "metadata": {
                "source": "general_knowledge",
                "category": "miscellaneous"
            }
        }
    ]
    
    # Find the most relevant predefined query
    for key in verbose_contexts:
        if key in query.lower():
            return verbose_contexts[key]
    
    return default_docs

@log
def rag_with_poor_utilization(query: str):
    """
    RAG implementation that demonstrates poor chunk utilization by not providing
    guidance to the model on how to handle long, verbose documents.
    """
    documents = retrieve_verbose_documents(query)
    
    # Format documents for the prompt
    formatted_docs = ""
    for i, doc in enumerate(documents):
        formatted_docs += f"Document {i+1} (Source: {doc['metadata']['source']}):\n{doc['text']}\n\n"

    # Basic prompt that doesn't guide the model on handling verbose chunks
    basic_prompt = f"""
    Answer the following question based on the provided documents.
    
    Question: {query}

    Documents:
    {formatted_docs}
    """

    try:
        console.print("[bold blue]Generating answer (with poor chunk utilization)...[/bold blue]")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": basic_prompt}
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating response: {str(e)}"

@log
def rag_with_better_utilization(query: str):
    """
    RAG implementation that demonstrates better chunk utilization by giving
    the model specific instructions on how to extract and use information.
    """
    documents = retrieve_verbose_documents(query)
    
    # Format documents for the prompt
    formatted_docs = ""
    for i, doc in enumerate(documents):
        formatted_docs += f"Document {i+1} (Source: {doc['metadata']['source']}):\n{doc['text']}\n\n"

    # Enhanced prompt that guides the model to better utilize the chunks
    enhanced_prompt = f"""
    Answer the following question based on the provided documents. 
    
    IMPORTANT INSTRUCTIONS:
    1. First, identify and extract the key facts and information from each document that are relevant to the question.
    2. Organize these key points in a structured way.
    3. Use these extracted points to formulate your complete answer.
    4. Make sure to utilize all relevant information from the documents.
    5. If the documents contain information that directly answers the question, be sure to include it.
    
    Question: {query}

    Documents:
    {formatted_docs}
    """

    try:
        console.print("[bold green]Generating answer (with improved chunk utilization)...[/bold green]")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that thoroughly extracts and utilizes all relevant information from provided documents. Your goal is to ensure no important details are missed."},
                {"role": "user", "content": enhanced_prompt}
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating response: {str(e)}"

def main():

    console.print(Panel.fit(
        "[bold]Chunk Utilization RAG Demo[/bold]\nThis demo shows how RAG systems can struggle with verbose chunks and how to improve information extraction.",
        title="Galileo RAG Challenge: Chunk Utilization",
        border_style="blue"
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
        "What are the planets in our solar system?",
        "Explain the process of photosynthesis simply.",
        "How does blockchain technology work?",
        "What were the key characteristics of the Renaissance period?",
        "What are the different types of machine learning?"
    ]
    
    console.print("\n[bold yellow]Suggested queries (these will demonstrate the chunk utilization problem):[/bold yellow]")
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
            poor_result = rag_with_poor_utilization(query)
            better_result = rag_with_better_utilization(query)
            
            # Display the retrieved context
            documents = retrieve_verbose_documents(query)
            console.print("\n[bold cyan]Retrieved Context (Verbose Chunks):[/bold cyan]")
            for i, doc in enumerate(documents):
                console.print(Panel(
                    f"[bold]Source:[/bold] {doc['metadata']['source']}\n\n[dim]{doc['text']}[/dim]",
                    title=f"Document {i+1} ({len(doc['text'])} characters)",
                    border_style="cyan"
                ))
            
            # Display the poor utilization response
            console.print("\n[bold red]Response with Poor Chunk Utilization:[/bold red]")
            console.print(Panel(Markdown(poor_result), border_style="red"))
            
            # Display the better utilization response
            console.print("\n[bold green]Response with Improved Chunk Utilization:[/bold green]")
            console.print(Panel(Markdown(better_result), border_style="green"))                      
            
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
        console.print("\n[bold]Exiting Chunk Utilization RAG Demo. Goodbye![/bold]")
