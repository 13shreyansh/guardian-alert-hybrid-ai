import sys, json
sys.path.insert(0, "cactus/python/src")
from cactus import cactus_init, cactus_complete, cactus_destroy

model_path = "cactus/weights/functiongemma-270m-it"

# Test the hard cases that failed
tests = [
    ("alarm_and_weather",
     "Set an alarm for 7:30 AM and check the weather in New York.",
     [{"name":"get_weather","description":"Get current weather for a location","parameters":{"type":"object","properties":{"location":{"type":"string","description":"City name"}},"required":["location"]}},
      {"name":"set_alarm","description":"Set an alarm for a given time","parameters":{"type":"object","properties":{"hour":{"type":"integer","description":"Hour to set the alarm for"},"minute":{"type":"integer","description":"Minute to set the alarm for"}},"required":["hour","minute"]}},
      {"name":"send_message","description":"Send a message to a contact","parameters":{"type":"object","properties":{"recipient":{"type":"string","description":"Name"},"message":{"type":"string","description":"Message"}},"required":["recipient","message"]}}]),
    ("sub: set alarm only",
     "Set an alarm for 7:30 AM",
     [{"name":"set_alarm","description":"Set an alarm for a given time","parameters":{"type":"object","properties":{"hour":{"type":"integer","description":"Hour to set the alarm for"},"minute":{"type":"integer","description":"Minute to set the alarm for"}},"required":["hour","minute"]}}]),
    ("sub: weather only",
     "check the weather in New York",
     [{"name":"get_weather","description":"Get current weather for a location","parameters":{"type":"object","properties":{"location":{"type":"string","description":"City name"}},"required":["location"]}}]),
    ("timer_5min",
     "Set a timer for 5 minutes.",
     [{"name":"set_timer","description":"Set a countdown timer","parameters":{"type":"object","properties":{"minutes":{"type":"integer","description":"Number of minutes"}},"required":["minutes"]}}]),
    ("timer_among_three",
     "Set a timer for 10 minutes.",
     [{"name":"set_alarm","description":"Set an alarm for a given time","parameters":{"type":"object","properties":{"hour":{"type":"integer","description":"Hour"},"minute":{"type":"integer","description":"Minute"}},"required":["hour","minute"]}},
      {"name":"set_timer","description":"Set a countdown timer","parameters":{"type":"object","properties":{"minutes":{"type":"integer","description":"Number of minutes"}},"required":["minutes"]}},
      {"name":"play_music","description":"Play a song or playlist","parameters":{"type":"object","properties":{"song":{"type":"string","description":"Song or playlist name"}},"required":["song"]}}]),
    ("reminder_and_message",
     "Remind me about groceries at 5:00 PM and text Lisa saying see you tonight.",
     [{"name":"create_reminder","description":"Create a reminder with a title and time","parameters":{"type":"object","properties":{"title":{"type":"string","description":"Reminder title"},"time":{"type":"string","description":"Time for the reminder (e.g. 3:00 PM)"}},"required":["title","time"]}},
      {"name":"send_message","description":"Send a message to a contact","parameters":{"type":"object","properties":{"recipient":{"type":"string","description":"Name of the person"},"message":{"type":"string","description":"The message content"}},"required":["recipient","message"]}},
      {"name":"get_weather","description":"Get weather","parameters":{"type":"object","properties":{"location":{"type":"string","description":"City"}},"required":["location"]}},
      {"name":"set_alarm","description":"Set an alarm","parameters":{"type":"object","properties":{"hour":{"type":"integer","description":"Hour"},"minute":{"type":"integer","description":"Minute"}},"required":["hour","minute"]}}]),
]

model = cactus_init(model_path)
for name, query, tools in tests:
    cactus_tools = [{"type":"function","function":t} for t in tools]
    raw = cactus_complete(
        model,
        [{"role":"system","content":"You are a helpful assistant with access to tools. Call the most appropriate tool."},
         {"role":"user","content":query}],
        tools=cactus_tools, force_tools=True, max_tokens=256,
        stop_sequences=["<|im_end|>","<end_of_turn>"]
    )
    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = {"raw": raw[:300]}
    print(f"--- {name} ---")
    print(f"  calls: {json.dumps(parsed.get('function_calls', []), indent=4)}")
    print(f"  conf:  {parsed.get('confidence', 'N/A')}")
    print()
cactus_destroy(model)
