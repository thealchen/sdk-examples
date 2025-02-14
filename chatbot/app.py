import os
import streamlit as st
from galileo import openai # The Galileo OpenAI client wrapper is all you need!

from dotenv import load_dotenv

load_dotenv()

client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

prompt = f"Tell me about Newton’s first law."
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "system", "content": prompt}],
)

print(response.choices[0].message.content.strip())
