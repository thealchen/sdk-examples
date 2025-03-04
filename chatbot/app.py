import os
from galileo import openai # The Galileo OpenAI client wrapper is all you need!

from dotenv import load_dotenv

load_dotenv()

client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), organization=os.environ.get("OPENAI_ORGANIZATION"))

prompt = f"i"
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "system", "content": prompt}],
)

print(response.choices[0].message.content.strip())
