import os
import streamlit as st
from dotenv import load_dotenv
from galileo import openai, log

load_dotenv()

# Initialize OpenAI client directly
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@log(span_type="retriever")
def retrieve_documents(query: str):
    # TODO: Replace with actual RAG retrieval
    documents = [
        {
            "id": "doc1",
            "text": "Galileo is an observability platform for LLM applications. It helps developers monitor, debug, and improve their AI systems by tracking inputs, outputs, and performance metrics.",
            "metadata": {
                "source": "galileo_docs",
                "category": "product_overview"
            }
        },
        {
            "id": "doc2",
            "text": "RAG (Retrieval-Augmented Generation) is a technique that enhances LLM responses by retrieving relevant information from external knowledge sources before generating an answer.",
            "metadata": {
                "source": "ai_techniques",
                "category": "methodology"
            }
        },
        {
            "id": "doc3",
            "text": "Common RAG challenges include hallucinations, retrieval quality issues, and context window limitations. Proper evaluation metrics include relevance, faithfulness, and answer correctness.",
            "metadata": {
                "source": "ai_techniques",
                "category": "challenges"
            }
        },
        {
            "id": "doc4",
            "text": "Vector databases like Pinecone, Weaviate, and Chroma are optimized for storing embeddings and performing similarity searches, making them ideal for RAG applications.",
            "metadata": {
                "source": "tech_stack",
                "category": "databases"
            }
        },
        {
            "id": "doc5",
            "text": "Prompt engineering is crucial for RAG systems. Well-crafted prompts should instruct the model to use retrieved context, avoid making up information, and cite sources when possible.",
            "metadata": {
                "source": "best_practices",
                "category": "prompting"
            }
        }
    ]
    return documents

def rag(query: str):
    documents = retrieve_documents(query)
    
    # Format documents for better readability in the prompt
    formatted_docs = ""
    for i, doc in enumerate(documents):
        formatted_docs += f"Document {i+1} (Source: {doc['metadata']['source']}):\n{doc['text']}\n\n"

    prompt = f"""
    Answer the following question based on the context provided. If the answer is not in the context, say you don't know.
    
    Question: {query}

    Context:
    {formatted_docs}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based only on the provided context."},
                {"role": "user", "content": prompt}
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating response: {str(e)}"

def main():
    st.title("RAG Demo")
    
    # Add debug mode toggle
    debug_mode = st.sidebar.checkbox("Debug Mode", value=False)
    
    if debug_mode:
        st.sidebar.subheader("Debug Information")
        if logging_enabled:
            st.sidebar.success("✅ Galileo logging is enabled")
        else:
            st.sidebar.warning("⚠️ Galileo logging is disabled")
        
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            st.sidebar.success("✅ OpenAI API Key is set")
        else:
            st.sidebar.error("❌ OpenAI API Key is missing")
    
    st.markdown("### Ask a question about Galileo, RAG, or AI techniques")
    st.markdown("This demo uses a simulated RAG system to answer your questions.")
    
    # Make the text input more prominent
    query = st.text_input("Enter your question here:", key="query_input", placeholder="e.g., What is Galileo?")
    
    # Add a submit button for clarity
    submit_button = st.button("Submit Question")
    
    # Process query when button is clicked or Enter is pressed in the text input
    if submit_button or query:
        if query:  # Only process if there's actual text
            with st.spinner("Generating answer..."):
                try:
                    result = rag(query)
                    
                    # Show debug info if debug mode is enabled
                    if debug_mode:
                        st.subheader("Retrieved Documents:")
                        documents = retrieve_documents(query)
                        for i, doc in enumerate(documents):
                            with st.expander(f"Document {i+1} (Source: {doc['metadata']['source']})"):
                                st.write(doc['text'])
                    
                    st.subheader("Answer:")
                    st.write(result)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter a question first.")

if __name__ == "__main__":
    main()
