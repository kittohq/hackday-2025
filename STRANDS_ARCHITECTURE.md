# AWS Strands Agent Framework Documentation

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

### Step 2: Agent Creation & Intent Mapping
```python
# Per-request agent creation (app_voice.py)
intent_mapper = create_intent_mapping_agent()  # Fresh instance

# Agent configuration (waymo_rider_agent_v2.py)
model = OpenAIModel(
    model_id="gpt-3.5-turbo",
    temperature=0.3,  # Low for consistency
    max_tokens=100
)

agent = Agent(
    name="Place Intent Mapper",
    model=model,
    system_prompt="""Map user requests to Google Places categories..."""
)

# Execute intent classification
result = intent_mapper("What category: 'I need coffee'?")
# Returns: "coffee_shop"
```

### Step 3: Tool Execution via Strands
```python
# The @tool decorator makes functions callable by agents
@tool
def search_places_with_ai(user_request, destination, radius=1500):
    """Search Google Places near destination"""

    # 1. Get place type from intent
    place_type = map_to_google_place_type(user_request)

    # 2. Call Google Places API
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

    # 3. Process and sort results
    places = parse_places(response.json())
    return sorted(places, key=lambda x: x['distance'])
```

### Step 4: Response Generation
```
Places Found: [Starbucks, Peet's, Blue Bottle]
     ↓
Natural Language Generation
     ↓
"I found 3 coffee shops near Mission District.
 The closest is Starbucks, just 5 minutes away."
     ↓
Web Speech Synthesis (TTS)
     ↓
Audio Output to User
```

## 🎭 Agent Orchestration Patterns

### 1. **Single-Purpose Agent Pattern** (Current Implementation)
```
Request → Create Agent → Execute → Destroy Agent → Response

Benefits:
• No state pollution between requests
• Clean error boundaries
• Predictable resource usage
• No connection pooling issues
```

### 2. **Tool Composition Pattern**
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
```python
def intelligent_place_search(query):
    try:
        # Primary: AI-powered intent mapping
        intent_agent = create_intent_mapping_agent()
        category = intent_agent(query)
    except Exception:
        # Fallback: Keyword matching
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
```python
@tool  # This decorator makes the function callable by agents
def search_places(query: str, location: dict) -> list:
    """Search for places near a location"""
    # Implementation
```

### 2. **Model Abstraction**
```python
# Strands supports multiple models
from strands.models.openai import OpenAIModel
from strands.models.anthropic import ClaudeModel
from strands.models.bedrock import BedrockModel

# Easy to switch between models
model = OpenAIModel(model_id="gpt-4")  # or gpt-3.5-turbo
```

### 3. **Agent Lifecycle Management**
```python
# Creation
agent = Agent(name="Intent Mapper", model=model, tools=[])

# Execution
result = agent(user_input)

# Cleanup (automatic with proper scoping)
del agent  # Frees resources
```

### 4. **System Prompts**
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