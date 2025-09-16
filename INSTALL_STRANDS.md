# Installing AWS Strands Agents SDK 📦

## Quick Install

```bash
# Install the core Strands SDK
pip install strands-agents

# Install the community tools package (optional but recommended)
pip install strands-agents-tools
```

## Troubleshooting Installation

### If you get "Package not found"

The AWS Strands SDK might not be publicly available yet or requires special access. Here are your options:

### Option 1: Check AWS Prerequisites

1. **Verify AWS Account Access**
```bash
# Make sure you have AWS CLI configured
aws configure list

# If not configured, set it up:
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter your default region (e.g., us-west-2)
```

2. **Check if it's in AWS CodeArtifact**
Some AWS packages are hosted in CodeArtifact instead of PyPI:
```bash
# Login to AWS CodeArtifact (if required)
aws codeartifact login --tool pip --repository strands-agents --domain your-domain

# Then install
pip install strands-agents
```

### Option 2: Install from GitHub

If the package is on GitHub but not PyPI:
```bash
# Clone the repository
git clone https://github.com/strands-agents/strands.git
cd strands

# Install from source
pip install -e .
```

### Option 3: Check Package Name

The package might have a different name:
```bash
# Try variations
pip install aws-strands-agents
pip install strands
pip install aws-strands
```

### Option 4: Use the Mock Version (For Hackathon)

If you can't install the real SDK, the mock version still works great for demos!

The code already includes fallback to mock implementation:
```python
try:
    from strands import Agent
    STRANDS_AVAILABLE = True
except ImportError:
    # Uses mock implementation
    STRANDS_AVAILABLE = False
```

## Verify Installation

```bash
# Check if installed
pip list | grep strands

# Test in Python
python -c "from strands import Agent; print('✅ Strands installed successfully!')"
```

## Required Dependencies

If Strands is installed but not working, ensure you have these:
```bash
pip install boto3  # AWS SDK
pip install pydantic  # Data validation
pip install httpx  # HTTP client
pip install python-dotenv  # Environment variables
```

## For Model Providers

### AWS Bedrock (Recommended)
```bash
# Configure AWS credentials
aws configure

# Test Bedrock access
aws bedrock list-foundation-models
```

### OpenAI
```bash
# Set in .env file
echo "OPENAI_API_KEY=your-key-here" >> .env
```

### Anthropic
```bash
# Set in .env file
echo "ANTHROPIC_API_KEY=your-key-here" >> .env
```

## If Strands is Not Available

The mock implementation provides the same interface, so your code will still work:

**With Real Strands:**
```python
from strands import Agent  # Real SDK
agent = Agent(tools=[...])
response = agent("What time is it?")
```

**With Mock (automatic fallback):**
```python
# Same code! Mock is imported automatically
agent = Agent(tools=[...])  # Uses mock
response = agent("What time is it?")  # Still works!
```

## AWS Internal/Beta Access

If Strands is in beta or internal to AWS:

1. **Check AWS Documentation**
   - Visit: https://strandsagents.com/
   - Look for "Getting Started" or "Installation"

2. **Request Access**
   - May need to join a beta program
   - Contact AWS support for access

3. **Use AWS Workshops**
   - AWS often provides workshop environments with pre-installed tools
   - Check: https://workshops.aws/

## For Your Hackathon

### Quick Decision Tree:

1. **Can install Strands?** → Use it! Production-ready
2. **Can't install?** → Use the mock! Demo still works
3. **Need voice?** → Both real and mock support it

### The Mock Advantage:
- ✅ No dependencies
- ✅ Works offline
- ✅ Same API interface
- ✅ Perfect for demos
- ✅ Can upgrade to real Strands later

## Test Your Setup

```bash
cd /Volumes/t9/github/hackday/simple_strands
python simple_agent.py

# If you see "Using real Strands SDK" → Real version working
# If you see "Strands not installed, using mock" → Mock version working
# Both are fine for the hackathon!
```

## Bottom Line

For your hackathon:
- **Try to install Strands** first
- **If it fails, the mock works perfectly** for demos
- **Focus on building** rather than troubleshooting installation
- **Judges care about the concept**, not whether you're using real or mock AWS SDK