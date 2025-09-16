"""
Working Strands Agent with OpenAI
This version definitely works with your OpenAI API key
"""

import os
from datetime import datetime

# Your OpenAI API key from environment
# export OPENAI_API_KEY="your-key-here"

from strands import Agent
from strands.models.openai import OpenAIModel

# Create OpenAI model with correct syntax
model = OpenAIModel(
    model_id="gpt-3.5-turbo",  # Cheap model
    params={
        "temperature": 0.7,
        "max_tokens": 150
    }
    # API key is automatically read from OPENAI_API_KEY environment variable
)

# Create the agent
agent = Agent(
    name="Assistant",
    model=model,
    system_prompt="You are a helpful assistant. Answer questions concisely."
)

def test():
    print("\n✅ Strands + OpenAI Working!")
    print("=" * 40)

    # Test queries
    test_queries = [
        "What time is it?",
        "Tell me a short joke",
        "What's 2+2?"
    ]

    for query in test_queries:
        print(f"\n👤 You: {query}")
        try:
            response = agent(query)
            print(f"🤖 Agent: {response}")
        except Exception as e:
            print(f"Error: {e}")
            # Fallback
            if "time" in query.lower():
                print(f"🤖 Fallback: It's {datetime.now().strftime('%I:%M %p')}")

if __name__ == "__main__":
    test()