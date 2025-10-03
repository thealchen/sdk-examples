"""
Supervisor Agent for Brahe Bank Application
"""

import os
from langchain_openai import ChatOpenAI
from langgraph_supervisor import create_supervisor

from .credit_score_agent import create_credit_score_agent
from .credit_card_information_agent import create_credit_card_information_agent

# Define the agents that the supervisor will manage
credit_card_information_agent = create_credit_card_information_agent()
credit_score_agent = create_credit_score_agent()


def create_supervisor_agent():
    """
    Create a supervisor agent that manages all the agents in the Brahe Bank application.
    """
    bank_supervisor_agent = create_supervisor(
        model=ChatOpenAI(model=os.environ["MODEL_NAME"], name="Supervisor"),
        agents=[credit_card_information_agent, credit_score_agent],
        prompt=(
            """
            You are a supervisor managing the following agents:
            - a credit card information agent. Assign any tasks related to information about credit cards to this agent
            - a credit score agent. Assign any tasks related to credit scores to this agent

            When an agent completes a task and returns information to you, relay their complete response
            directly to the user without modification. Do not add generic follow-up phrases like
            "If you have any more questions, feel free to ask!" - simply pass through the agent's answer.

            If the question is not related to credit cards or credit scores, respond with 'I don't know'
            or 'I cannot answer that question'.
            If you need to ask the user for more information, do so in a concise manner.
            """
        ),
        add_handoff_back_messages=True,
        output_mode="full_history",
        supervisor_name="brahe-bank-supervisor-agent",
    ).compile()
    bank_supervisor_agent.name = "brahe-bank-supervisor-agent"

    # Uncomment the following lines to print the compiled graph to the console in Mermaid format
    # print("Compiled Bank Supervisor Agent Graph:")
    # print(bank_supervisor_agent.get_graph().draw_mermaid())

    return bank_supervisor_agent
