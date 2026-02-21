import sys, os, json
sys.path.insert(0, "cactus/python/src")
os.environ["CACTUS_NO_CLOUD_TELE"] = "1"

from cactus import cactus_init, cactus_complete, cactus_destroy

functiongemma_path = "cactus/weights/functiongemma-270m-it"

TOOL_CREATE_REMINDER = {
    "name": "create_reminder",
    "description": "Create a reminder with a title and time",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Reminder title"},
            "time": {"type": "string", "description": "Time for the reminder (e.g. 3:00 PM)"},
        },
        "required": ["title", "time"],
    },
}

TOOL_SEND_MESSAGE = {
    "name": "send_message",
    "description": "Send a message to a contact",
    "parameters": {
        "type": "object",
        "properties": {
            "recipient": {"type": "string", "description": "Name of the person to send the message to"},
            "message": {"type": "string", "description": "The message content to send"},
        },
        "required": ["recipient", "message"],
    },
}

TOOL_GET_WEATHER = {
    "name": "get_weather",
    "description": "Get current weather for a location",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City name"}
        },
        "required": ["location"],
    },
}

TOOL_SET_ALARM = {
    "name": "set_alarm",
    "description": "Set an alarm for a given time",
    "parameters": {
        "type": "object",
        "properties": {
            "hour": {"type": "integer", "description": "Hour to set the alarm for"},
            "minute": {"type": "integer", "description": "Minute to set the alarm for"},
        },
        "required": ["hour", "minute"],
    },
}

TOOL_SET_TIMER = {
    "name": "set_timer",
    "description": "Set a countdown timer",
    "parameters": {
        "type": "object",
        "properties": {
            "minutes": {"type": "integer", "description": "Number of minutes"},
        },
        "required": ["minutes"],
    },
}

TOOL_PLAY_MUSIC = {
    "name": "play_music",
    "description": "Play a song or playlist",
    "parameters": {
        "type": "object",
        "properties": {
            "song": {"type": "string", "description": "Song or playlist name"},
        },
        "required": ["song"],
    },
}

TOOL_SEARCH_CONTACTS = {
    "name": "search_contacts",
    "description": "Search for a contact by name",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Name to search for"},
        },
        "required": ["query"],
    },
}

def run_model(query, tools, label=""):
    model = cactus_init(functiongemma_path)
    cactus_tools = [{"type": "function", "function": t} for t in tools]
    raw_str = cactus_complete(
        model,
        [{"role": "system", "content": "You are a helpful assistant that can use tools."},
         {"role": "user", "content": query}],
        tools=cactus_tools,
        force_tools=True,
        max_tokens=256,
        stop_sequences=["<|im_end|>", "<end_of_turn>"],
    )
    cactus_destroy(model)
    print(f"\n=== {label} ===")
    print(f"Query: {query}")
    print(f"Tools: {[t['name'] for t in tools]}")
    print(f"Raw output: {raw_str}")
    try:
        parsed = json.loads(raw_str)
        print(f"Parsed calls: {json.dumps(parsed.get('function_calls', []), indent=2)}")
    except:
        print("Failed to parse JSON")

# Test failing cases
print("="*60)
print("DEBUGGING FAILING CASES")
print("="*60)

# 1. reminder_meeting (easy, F1=0, cloud) - single tool
run_model("Remind me about the meeting at 3:00 PM.", [TOOL_CREATE_REMINDER], "reminder_meeting (easy)")

# 2. reminder_among_four (medium, F1=0, on-device) - 4 tools
run_model("Remind me to call the dentist at 2:00 PM.", 
          [TOOL_GET_WEATHER, TOOL_SEND_MESSAGE, TOOL_CREATE_REMINDER, TOOL_SET_ALARM],
          "reminder_among_four (medium)")

# 3. message_among_four (medium, F1=0, cloud) - 4 tools
run_model("Text Dave saying I'll be late.",
          [TOOL_GET_WEATHER, TOOL_SET_TIMER, TOOL_SEND_MESSAGE, TOOL_PLAY_MUSIC],
          "message_among_four (medium)")

# 4. search_and_message (hard, F1=0.50) - multi-intent
run_model("Find Tom in my contacts and send him a message saying happy birthday.",
          [TOOL_SEARCH_CONTACTS, TOOL_SEND_MESSAGE, TOOL_GET_WEATHER, TOOL_PLAY_MUSIC],
          "search_and_message (hard, full)")

# 5. alarm_10am (easy, cloud) - should be easy
run_model("Set an alarm for 10 AM.", [TOOL_SET_ALARM], "alarm_10am (easy)")

# 6. message_alice (easy, cloud) - should be easy
run_model("Send a message to Alice saying hello.", [TOOL_SEND_MESSAGE], "message_alice (easy)")

# Also test sub-parts for multi-intent
print("\n" + "="*60)
print("SUB-PART TESTS")
print("="*60)

run_model("Find Tom in my contacts", [TOOL_SEARCH_CONTACTS], "search sub-part")
run_model("send him a message saying happy birthday", [TOOL_SEND_MESSAGE], "message sub-part")
run_model("Remind me about groceries at 5:00 PM", [TOOL_CREATE_REMINDER], "reminder sub-part")
run_model("text Lisa saying see you tonight", [TOOL_SEND_MESSAGE], "message sub-part 2")
