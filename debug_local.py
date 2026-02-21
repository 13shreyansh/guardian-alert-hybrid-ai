import sys, json
sys.path.insert(0, "cactus/python/src")
from cactus import cactus_init, cactus_complete, cactus_destroy

model_path = "cactus/weights/functiongemma-270m-it"

tests = [
    ("timer_5min", "Set a timer for 5 minutes.", [
        {"name":"set_timer","description":"Set a countdown timer",
         "parameters":{"type":"object","properties":{"minutes":{"type":"integer","description":"Number of minutes"}},"required":["minutes"]}}
    ]),
    ("alarm_10am", "Set an alarm for 10 AM.", [
        {"name":"set_alarm","description":"Set an alarm for a given time",
         "parameters":{"type":"object","properties":{"hour":{"type":"integer","description":"Hour"},"minute":{"type":"integer","description":"Minute"}},"required":["hour","minute"]}}
    ]),
    ("search_bob", "Find Bob in my contacts.", [
        {"name":"search_contacts","description":"Search for a contact by name",
         "parameters":{"type":"object","properties":{"query":{"type":"string","description":"Name to search for"}},"required":["query"]}}
    ]),
    ("reminder_meeting", "Remind me about the meeting at 3:00 PM.", [
        {"name":"create_reminder","description":"Create a reminder with a title and time",
         "parameters":{"type":"object","properties":{"title":{"type":"string","description":"Reminder title"},"time":{"type":"string","description":"Time for the reminder"}},"required":["title","time"]}}
    ]),
    ("split_send", "Send a message to Bob saying hi", [
        {"name":"send_message","description":"Send a message to a contact",
         "parameters":{"type":"object","properties":{"recipient":{"type":"string","description":"Name"},"message":{"type":"string","description":"Message"}},"required":["recipient","message"]}},
        {"name":"get_weather","description":"Get weather",
         "parameters":{"type":"object","properties":{"location":{"type":"string","description":"City"}},"required":["location"]}}
    ]),
    ("timer_among_three", "Set a timer for 10 minutes.", [
        {"name":"set_alarm","description":"Set an alarm for a given time",
         "parameters":{"type":"object","properties":{"hour":{"type":"integer","description":"Hour"},"minute":{"type":"integer","description":"Minute"}},"required":["hour","minute"]}},
        {"name":"set_timer","description":"Set a countdown timer",
         "parameters":{"type":"object","properties":{"minutes":{"type":"integer","description":"Number of minutes"}},"required":["minutes"]}},
        {"name":"play_music","description":"Play a song or playlist",
         "parameters":{"type":"object","properties":{"song":{"type":"string","description":"Song or playlist name"}},"required":["song"]}}
    ]),
]

model = cactus_init(model_path)
for name, query, tools in tests:
    cactus_tools = [{"type":"function","function":t} for t in tools]
    raw = cactus_complete(
        model,
        [{"role":"system","content":"You are a helpful assistant that can use tools."},
         {"role":"user","content":query}],
        tools=cactus_tools, force_tools=True, max_tokens=256,
        stop_sequences=["<|im_end|>","<end_of_turn>"]
    )
    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = {"raw": raw[:500]}
    print(f"--- {name} ---")
    print(f"  calls: {json.dumps(parsed.get('function_calls', 'PARSE_FAIL'), indent=4)}")
    print(f"  conf:  {parsed.get('confidence', 'N/A')}")
    print()
cactus_destroy(model)
