"""
Strands Agent using OpenAI explicitly
"""

import os

# Your OpenAI key from environment
# export OPENAI_API_KEY="your-key-here"

# Import and configure Strands
from strands import Agent
from strands.models.openai import OpenAIModel

# Create OpenAI model explicitly (using cheapest model)
model = OpenAIModel(
    model_id="gpt-3.5-turbo",  # Cheapest OpenAI model ($0.0015/1K tokens)
    params={
        # API key is read from OPENAI_API_KEY environment variable
    }
    # Other cheap options: "gpt-4o-mini" is even cheaper!
)

# Create agent with OpenAI model
agent = Agent(
    name="Time Assistant",
    model=model,  # Use the OpenAI model directly
    system_prompt="You are a helpful assistant. Answer questions about time, date, and general topics."
)

def demo():
    print("\n✅ Strands Agent with OpenAI")
    print("=" * 40)

    queries = [
        "What time is it?",
        "What's today's date?",
        "Tell me a joke"
    ]

    for query in queries:
        print(f"\n👤 You: {query}")
        try:
            response = agent(query)
            print(f"🤖 Agent: {response}")
        except Exception as e:
            print(f"Error: {e}")
            # Fallback response
            if "time" in query.lower():
                from datetime import datetime
                print(f"🤖 Agent: The current time is {datetime.now().strftime('%I:%M %p')}")
            elif "date" in query.lower():
                from datetime import datetime
                print(f"🤖 Agent: Today is {datetime.now().strftime('%A, %B %d, %Y')}")

if __name__ == "__main__":
    demo()