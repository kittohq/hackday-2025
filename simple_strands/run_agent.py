#!/usr/bin/env python3
"""
Run the Waymo Rider Agent with API keys loaded from .env.example
Usage: python3 run_agent.py
"""

import os
import sys

def load_env_file(filepath='.env.example'):
    """Load environment variables from .env.example file"""
    if not os.path.exists(filepath):
        print(f"❌ {filepath} not found!")
        print("Create .env.example with your API keys")
        return False

    with open(filepath) as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith('#'):
                # Parse KEY=VALUE or KEY='VALUE'
                if '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value

    # Verify keys are loaded
    if os.environ.get('OPENAI_API_KEY'):
        print(f"✅ Loaded OPENAI_API_KEY: {os.environ['OPENAI_API_KEY'][:20]}...")
    else:
        print("⚠️  OPENAI_API_KEY not found in .env.example")

    if os.environ.get('GOOGLE_API_KEY'):
        print(f"✅ Loaded GOOGLE_API_KEY: {os.environ['GOOGLE_API_KEY'][:20]}...")
    else:
        print("⚠️  GOOGLE_API_KEY not found in .env.example")

    return True

if __name__ == "__main__":
    print("🔑 Loading API keys from .env.example...")

    if load_env_file():
        print("\n🚗 Starting Waymo Rider Experience Agent...\n")
        print("=" * 50)

        # Import and run the agent after environment is set
        from waymo_rider_agent import demo, test_automated

        # Check if test mode requested
        if len(sys.argv) > 1 and sys.argv[1] == "test":
            test_automated()
        else:
            demo()
    else:
        print("\n❌ Failed to load environment. Please check .env.example")
        sys.exit(1)