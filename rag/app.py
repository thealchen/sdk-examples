import os
import streamlit as st
from galileo import (log, openai) # The Galileo OpenAI client wrapper is all you need!

from dotenv import load_dotenv

load_dotenv()

client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@log(span_type="retriever")
def retrieve_documents(query: str):
    documents = [
        {
            "id": "1",
            "text": "This is a test document",
            "metadata": {
                "source": "test"
            }
        }
    ]
    return documents

def rag(query: str):
    documents = retrieve_documents(query)

    prompt = f"""
    Answer the following question based on the context provided: {query}

    Context:
    {documents}
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}],
    )
    return response.choices[0].message.content.strip()

def main():
    st.title("RAG Demo")
    query = st.text_input("Enter a question")
    if query:
        result = rag(query)
        st.write(result)
