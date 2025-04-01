import os
from dotenv import load_dotenv
from galileo import openai, GalileoLogger
from rich.console import Console
from sentence_transformers import SentenceTransformer
import faiss
from time import perf_counter_ns

load_dotenv()

class Prompts:
    BASIC = """Answer the following question based on the provided documents.
    
Question: {query}

Documents:
{documents}"""

    ENHANCED = """Answer the following question based on the provided documents.

IMPORTANT INSTRUCTIONS:
1. Extract key facts from each document.
2. Organize information systematically.
3. Utilize all relevant details.
4. Prioritize high-relevance sources.

Question: {query}

Documents:
{documents}"""

class DocumentStore:
    def __init__(self):
        self.documents = [
            {
                "text": "The Solar System is the gravitationally bound system of the Sun and the objects that orbit it. It formed 4.6 billion years ago from the gravitational collapse of a giant interstellar molecular cloud.",
                "metadata": {"source": "astronomy", "relevance": "high"}
            },
            {
                "text": "The four inner system planets—Mercury, Venus, Earth and Mars—are terrestrial planets. The four outer planets—Jupiter, Saturn, Uranus, and Neptune—are much larger gas and ice giants.",
                "metadata": {"source": "astronomy", "relevance": "high"}
            },
            {
                "text": "Photosynthesis is the process by which plants convert light energy into chemical energy in the form of glucose. These organisms are called photoautotrophs since they can create their own food.",
                "metadata": {"source": "biology", "relevance": "high"}
            },
            {
                "text": "The evolution of photosynthesis occurred early in Earth's history, appearing between 3.4 and 2.9 billion years ago. This development dramatically changed Earth's atmosphere by introducing oxygen.",
                "metadata": {"source": "biology", "relevance": "low"}
            }
        ]
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self._build_index()

    def _build_index(self):
        texts = [doc["text"] for doc in self.documents]
        self.embeddings = self.encoder.encode(texts)
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(self.embeddings.astype('float32'))

    def search(self, query: str, k: int = 3) -> list:
        query_vector = self.encoder.encode([query])[0].reshape(1, -1)
        _, indices = self.index.search(query_vector.astype('float32'), k)
        return [self.documents[idx] for idx in indices[0]]

def format_documents(documents: list) -> str:
    return "\n\n".join(
        f"Document {i+1} (Source: {doc['metadata']['source']}, Relevance: {doc['metadata']['relevance']}):\n{doc['text']}"
        for i, doc in enumerate(documents)
    )

def query(question: str, enhanced: bool = False):
    logger = GalileoLogger(project="chunk-utilization", log_stream="dev")
    client = openai.OpenAI()
    docs = DocumentStore().search(question)
    
    prompt = (Prompts.ENHANCED if enhanced else Prompts.BASIC).format(
        query=question,
        documents=format_documents(docs)
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content.strip()

def main():
    console = Console()
    console.print("\nChunk Utilization Demo")
    
    while True:
        question = input("\nEnter your question (or 'q' to quit): ").strip()
        if question.lower() in ['q', 'quit', 'exit']:
            break

        console.print("\nBasic Response:")
        console.print(query(question, enhanced=False))
        
        console.print("\nEnhanced Response (with improved chunk utilization):")
        console.print(query(question, enhanced=True))

if __name__ == "__main__":
    main()
