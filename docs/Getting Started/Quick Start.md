# Getting Started with Galileo in 2 Minutes

## Prerequisites
Ensure you have Python 3.8+ installed.

## Step 1: Install Dependencies
Create a virtual environment and install the required packages:

```sh
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

## Step 2: Set Up Environment Variables
Create a `.env` file in the project directory and add your OpenAI API key:

```
OPENAI_API_KEY=your-api-key-here
```

## Step 3: Run the Application
Execute the script using Streamlit:

```sh
streamlit run app.py
```

## File Structure
```
/your_project_directory
│── app.py
│── requirements.txt
│── .env
```

## `app.py` - Example Code

```python
import os
import streamlit as st
from galileo import openai  # The Galileo OpenAI client wrapper is all you need!
from dotenv import load_dotenv

load_dotenv()

client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

prompt = f"Tell me about Newton’s first law."
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "system", "content": prompt}],
)

st.write(response.choices[0].message.content.strip())
```

## `requirements.txt`
```
galileo-0.0.1-py3-none-any.whl
streamlit>=1.29.0
openai==1.61.1
pydantic==2.10.6
```

## Next Steps
- Explore other models and prompts.
- Integrate Galileo into your existing projects.
- Check out [Galileo's Documentation](#) for advanced features.

