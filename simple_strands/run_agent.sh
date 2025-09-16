#!/bin/bash
# Run the Waymo Rider Agent with API keys from .env.example

# Load API keys from .env.example
if [ -f ".env.example" ]; then
    export $(grep -v '^#' .env.example | xargs)
    echo "✅ Loaded API keys from .env.example"
else
    echo "❌ .env.example not found!"
    exit 1
fi

# Run the agent
echo "🚗 Starting Waymo Rider Experience Agent..."
python3 waymo_rider_agent.py "$@"