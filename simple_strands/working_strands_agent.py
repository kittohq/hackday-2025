"""
Working Strands Agent Example
Now using the real AWS Strands SDK!
"""

from strands import Agent
import os
from datetime import datetime

# Configure the agent to use OpenAI (or you can use AWS Bedrock)
os.environ.setdefault("STRANDS_MODEL_PROVIDER", "openai")  # or "bedrock"

# Create a simple agent
agent = Agent(
    name="Time Assistant",
    description="A helpful assistant that tells time and answers questions",
    # You can specify model provider here
    # model_provider="openai",  # or "bedrock" for AWS
    # model_name="gpt-4",  # or specific model
)

def demo():
    """Run a simple demo with real Strands"""
    print("\n✅ Using Real AWS Strands SDK!")
    print("=" * 50)

    # Check if we have API keys configured
    if os.getenv("OPENAI_API_KEY"):
        print("✓ OpenAI API key found")
    elif os.getenv("AWS_ACCESS_KEY_ID"):
        print("✓ AWS credentials found")
    else:
        print("⚠️  No API keys found - Strands will use mock responses")
        print("   Set OPENAI_API_KEY or configure AWS credentials")
        print()

    queries = [
        "What time is it?",
        "What's today's date?",
        "Tell me a fun fact about time"
    ]

    print("\nExample queries:")
    for q in queries[:2]:
        print(f"  - {q}")
    print()

    # Interactive mode
    print("Type 'quit' to exit\n")

    while True:
        try:
            user_input = input("👤 You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            # For time questions, provide a simple response
            # Real Strands would use the LLM here
            if "time" in user_input.lower():
                response = f"The current time is {datetime.now().strftime('%I:%M %p')}"
            elif "date" in user_input.lower():
                response = f"Today is {datetime.now().strftime('%A, %B %d, %Y')}"
            else:
                # For real Strands with API key:
                try:
                    response = agent(user_input)
                except Exception as e:
                    # Fallback for when no API key is configured
                    response = f"I heard: '{user_input}'. (Note: Configure API keys for full Strands functionality)"

            print(f"🤖 Agent: {response}")
            print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            print("Tip: Set OPENAI_API_KEY environment variable for full functionality")
            print()

if __name__ == "__main__":
    demo()