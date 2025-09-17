# AWS Strands Agent Framework Documentation

## 📁 Key Files Overview

| File | Purpose | Key Functions |
|------|---------|---------------|
| `simple_strands/app_voice.py` | Main Flask server with voice interface | Lines 862-887: Voice endpoint |
| `simple_strands/waymo_rider_agent_v2.py` | Strands agent implementation | Lines 286-330: Agent creation |
| `simple_strands/google_places_agent.py` | Google Places integration | Lines 205-225: Places tools |
| `simple_strands/DEVELOPER_GUIDE.md` | Technical implementation guide | Architecture details |

### Import Locations

| What | Where | Line |
|------|-------|------|
| Strands Agent | `waymo_rider_agent_v2.py` | Line 9: `from strands import Agent, tool` |
| OpenAI Model | `waymo_rider_agent_v2.py` | Line 10: `from strands.models.openai import OpenAIModel` |
| Flask Setup | `app_voice.py` | Lines 11-13: Flask, CORS imports |
| Google API Key | `waymo_rider_agent_v2.py` | Line 33: `os.environ.get("GOOGLE_API_KEY")` |
| Web Speech API | `app_voice.py` | Lines 452-505: JavaScript implementation |
| TTS Implementation | `app_voice.py` | Lines 410-449: speak() function |

## 🎯 What is Strands?

AWS Strands is an AI agent orchestration framework that enables building intelligent, tool-enabled agents. It acts as the **conductor** that coordinates between:
- **Language Models** (OpenAI, Claude, etc.)
- **Tools** (functions that agents can call)
- **Business Logic** (your application code)

Think of Strands as a smart assistant manager that knows when to use which tool and how to combine results to answer complex queries.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERACTION LAYER                   │
│  Voice Input (Web Speech API) ←→ Text Input ←→ Quick Chips  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                      FLASK WEB SERVER                        │
│                   (app_voice.py - Port 5004)                 │
│  • Handles HTTP requests                                     │
│  • Manages session state                                     │
│  • Routes to appropriate handlers                            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   STRANDS AGENT LAYER                        │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          Intent Mapping Agent (Per Request)          │   │
│  │                                                       │   │
│  │  • Model: OpenAI GPT-3.5-turbo                       │   │
│  │  • Temperature: 0.3 (consistent mapping)             │   │
│  │  • System Prompt: Place category expert              │   │
│  │  • Input: "I need coffee"                            │   │
│  │  • Output: "coffee_shop"                             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Agent Lifecycle:                                            │
│  1. Created fresh for each request                           │
│  2. Initialized with OpenAI model                            │
│  3. Executes intent classification                           │
│  4. Cleaned up after use                                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                      TOOLS LAYER                             │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ @tool            │  │ @tool            │                │
│  │ search_places()  │  │ get_destination()│                │
│  │                  │  │                  │                │
│  │ Calls Google     │  │ Returns current  │                │
│  │ Places API       │  │ Waymo location   │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ @tool            │  │ @tool            │                │
│  │ calculate_dist() │  │ format_speech()  │                │
│  │                  │  │                  │                │
│  │ Haversine dist   │  │ Natural language │                │
│  │ calculation      │  │ generation       │                │
│  └──────────────────┘  └──────────────────┘                │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL APIs                             │
│                                                              │
│  • Google Places API (5M+ businesses)                        │
│  • OpenAI API (GPT-3.5 for intent)                          │
│  • Web Speech API (Browser STT/TTS)                         │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Request Flow Walkthrough

### Step 1: Voice Input Capture
```
User speaks: "I need coffee near my destination"
     ↓
Web Speech API (Browser)
     ↓
Transcript: "I need coffee near my destination"
     ↓
POST /api/voice
```

### Step 2: Agent Creation & Intent Mapping (One-Shot Classification)

**⚠️ Important Note:** The function `extract_place_intent` (lines 79-95) is **NOT USED** - it's placeholder code.

**The ACTUAL implementation uses OpenAI for one-shot classification:**

📍 **File:** `simple_strands/app_voice.py:879-887`
```python
# Per-request agent creation (app_voice.py)
intent_mapper = create_intent_mapping_agent()  # Fresh OpenAI instance

# One-shot classification - single API call
result = intent_mapper(f"What Google Places category best matches: '{user_text}'?")
place_type = str(result).strip()  # Returns: "coffee_shop"
```

📍 **File:** `simple_strands/waymo_rider_agent_v2.py:286-330`
```python
def create_intent_mapping_agent():
    """Create OpenAI-powered agent for one-shot place category classification"""

    model = OpenAIModel(
        model_id="gpt-3.5-turbo",
        temperature=0.3,  # Low temperature = consistent classification
        max_tokens=100
    )

    agent = Agent(
        name="Place Intent Mapper",
        model=model,
        tools=[],  # No tools - pure LLM classification
        system_prompt=f"""You are an expert at understanding what type of place a user is looking for.

Your ONLY job is to map user requests to the most appropriate Google Places API category.

Available Google Places categories:
{json.dumps(GOOGLE_PLACES_TYPES, indent=2)}

Instructions:
1. Analyze the user's request carefully
2. Return ONLY the category key (e.g., "coffee_shop", "restaurant")

Examples:
- "I need caffeine" → "coffee_shop"
- "Where can I grab breakfast?" → "breakfast_restaurant"
- "Looking for somewhere to eat" → "restaurant"

Remember: Return ONLY the category key, nothing else."""
    )

    return agent
```

**How One-Shot Classification Works:**
1. User says: "I need coffee"
2. System sends to GPT-3.5: "What Google Places category best matches: 'I need coffee'?"
3. GPT-3.5 (with system prompt containing all categories) returns: "coffee_shop"
4. Single API call = One-shot classification ✅

### Step 3: Tool Execution via Strands

📍 **File:** `simple_strands/waymo_rider_agent_v2.py:122-209`
```python
# The @tool decorator makes functions callable by agents
@tool
def search_places_with_ai(user_request, destination, radius=1500):
    """Search Google Places near destination"""

    # 1. Get place type from intent (line 144)
    place_type = map_to_google_place_type(user_request)

    # 2. Call Google Places API (lines 147-167)
    response = requests.post(
        "https://places.googleapis.com/v1/places:searchNearby",
        headers={"X-Goog-Api-Key": GOOGLE_API_KEY},
        json={
            "includedTypes": [place_type],
            "locationRestriction": {
                "circle": {
                    "center": destination,
                    "radius": radius
                }
            }
        }
    )

    # 3. Process and sort results (lines 176-201)
    places = parse_places(response.json())
    return sorted(places, key=lambda x: x['distance'])
```

### Step 4: Response Generation

📍 **File:** `simple_strands/app_voice.py:725-802`
```
Places Found: [Starbucks, Peet's, Blue Bottle]
     ↓
Natural Language Generation (generate_natural_speech() function)
     ↓
"I found 3 coffee shops near Mission District.
 The closest is Starbucks, just 5 minutes away."
     ↓
Web Speech Synthesis (TTS) - Browser JavaScript lines 410-449
     ↓
Audio Output to User
```

## 🎭 Agent Orchestration Patterns

### 1. **Single-Purpose Agent Pattern** (Current Implementation)

📍 **Implementation:** `simple_strands/app_voice.py:879-887`
```
Request → Create Agent → Execute → Destroy Agent → Response

Benefits:
• No state pollution between requests
• Clean error boundaries
• Predictable resource usage
• No connection pooling issues
```

### 2. **Tool Composition Pattern**

📍 **Example:** `simple_strands/google_places_agent.py:205-225`
```python
# Strands allows agents to chain tools
agent = Agent(
    tools=[
        get_destination,      # First: Get location
        search_places,        # Second: Find places
        calculate_distances,  # Third: Sort by distance
        format_response      # Fourth: Generate speech
    ]
)

# Agent automatically orchestrates the flow
result = agent("Find coffee shops")
```

### 3. **Fallback Pattern**

📍 **Implementation:** `simple_strands/waymo_rider_agent_v2.py:330-380`
```python
def intelligent_place_search(query):
    try:
        # Primary: AI-powered intent mapping
        intent_agent = create_intent_mapping_agent()
        category = intent_agent(query)
    except Exception:
        # Fallback: Keyword matching (lines 235-283)
        category = match_by_keywords(query)

    return search_places(category)
```

## 📊 Real-World Example Flow

**User says:** "I'm exhausted, need somewhere to grab an espresso"

### 1. Intent Classification Phase
```
Input: "I'm exhausted, need somewhere to grab an espresso"
                    ↓
Strands Agent Analysis:
- Keywords: "exhausted", "espresso"
- Context: Tired user needs caffeine
- Category Match: coffee_shop (95% confidence)
                    ↓
Output: "coffee_shop"
```

### 2. Search Execution Phase
```
Google Places API Request:
{
  "includedTypes": ["coffee_shop"],
  "maxResultCount": 5,
  "locationRestriction": {
    "circle": {
      "center": {"lat": 37.7749, "lng": -122.4194},
      "radius": 1500
    }
  }
}
                    ↓
Results: 5 coffee shops found
```

### 3. Distance Calculation Phase
```
For each place:
  Haversine Distance = calculate_distance(
    user_lat, user_lng,
    place_lat, place_lng
  )

Sort by distance ascending
```

### 4. Response Generation Phase
```
Template Selection:
- Single result → Specific recommendation
- Multiple results → Top 3 with comparison
- No results → Apologetic with alternatives

Generated: "Great news! I found 5 coffee shops nearby.
           Blue Bottle Coffee is closest at just 3 minutes walk,
           and it has 4.5 stars."
```

## 🔧 Key Strands Features Used

### 1. **Tool Decoration**

📍 **Files with @tool decorators:**
- `waymo_rider_agent_v2.py:97-112` - map_to_google_place_type
- `waymo_rider_agent_v2.py:114-119` - get_waymo_destination
- `waymo_rider_agent_v2.py:122-209` - search_places_with_ai
- `google_places_agent.py:43-205` - Multiple place search tools

```python
@tool  # This decorator makes the function callable by agents
def search_places(query: str, location: dict) -> list:
    """Search for places near a location"""
    # Implementation
```

### 2. **Model Abstraction**

📍 **Import locations:**
- `waymo_rider_agent_v2.py:10` - OpenAIModel import
- `google_places_agent.py:7` - Alternative model imports

```python
# Strands supports multiple models
from strands.models.openai import OpenAIModel
from strands.models.anthropic import ClaudeModel
from strands.models.bedrock import BedrockModel

# Easy to switch between models
model = OpenAIModel(model_id="gpt-4")  # or gpt-3.5-turbo
```

### 3. **Agent Lifecycle Management**

📍 **Implementation:** `app_voice.py:879-887`
```python
# Creation (line 880)
agent = Agent(name="Intent Mapper", model=model, tools=[])

# Execution (line 883)
result = agent(user_input)

# Cleanup (line 887)
del agent  # Frees resources
```

### 4. **System Prompts**

📍 **Location:** `waymo_rider_agent_v2.py:301-320`
```python
system_prompt = """
You are an expert at understanding place requests.
Available categories: restaurant, coffee_shop, bar...
Return ONLY the category key.
"""

agent = Agent(system_prompt=system_prompt)
```

## 🚀 Performance Optimizations

### 1. **Per-Request Agent Creation**
- **Problem:** Reusing agents caused connection hanging
- **Solution:** Create fresh agent per request
- **Result:** 100% reliability for consecutive requests

### 2. **Timeout Handling**
```python
# Prevent hanging on slow API calls
signal.alarm(5)  # 5-second timeout
try:
    result = agent(query)
finally:
    signal.alarm(0)  # Cancel alarm
```

### 3. **Fallback Strategies**
```python
# Three-tier fallback system
try:
    # Tier 1: AI Agent
    category = ai_agent(query)
except TimeoutError:
    # Tier 2: Keyword matching
    category = keyword_match(query)
except Exception:
    # Tier 3: Default
    category = "restaurant"
```

## 📈 Benefits of Strands Architecture

1. **Separation of Concerns**
   - Business logic separate from AI logic
   - Tools are reusable across agents
   - Easy to test individual components

2. **Scalability**
   - Stateless agents scale horizontally
   - No shared state between requests
   - Cloud-native design

3. **Flexibility**
   - Easy to swap LLM providers
   - Add new tools without changing core logic
   - Gradual migration paths

4. **Reliability**
   - Graceful degradation with fallbacks
   - Timeout protection
   - Error boundaries at each layer

## 🎯 When to Use Strands

### Good Fit:
- ✅ Need to combine multiple APIs/tools
- ✅ Want LLM to decide which tools to use
- ✅ Building conversational interfaces
- ✅ Need structured outputs from natural language

### Not Ideal For:
- ❌ Simple keyword matching (overkill)
- ❌ Real-time/low-latency requirements (<100ms)
- ❌ Deterministic workflows (use regular code)

## 🔮 Future Enhancements

1. **Multi-Agent Collaboration**
```python
planning_agent = Agent(name="Planner", ...)
search_agent = Agent(name="Searcher", ...)
summary_agent = Agent(name="Summarizer", ...)

# Agents work together
plan = planning_agent("User wants coffee and lunch")
results = search_agent(plan)
response = summary_agent(results)
```

2. **Memory/Context Persistence**
```python
agent = Agent(
    memory=RedisMemory(),  # Remember user preferences
    context_window=10       # Last 10 interactions
)
```

3. **Streaming Responses**
```python
async for chunk in agent.stream(query):
    yield chunk  # Real-time response generation
```

## 📚 Summary

Strands acts as the **orchestration layer** that:
1. **Interprets** natural language into structured intents
2. **Decides** which tools to use and when
3. **Executes** tool calls in the right order
4. **Combines** results into coherent responses
5. **Handles** errors gracefully with fallbacks

It's not just calling APIs - it's intelligently coordinating between multiple services to solve complex user requests in a natural, conversational way.