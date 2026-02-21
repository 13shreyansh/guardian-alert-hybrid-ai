"""Quick test for the 3 remaining failing cases."""
import sys, os
sys.path.insert(0, "cactus/python/src")
os.environ["CACTUS_NO_CLOUD_TELE"] = "1"
from main import generate_hybrid

TOOLS = {
    "get_weather": {"name": "get_weather", "description": "Get current weather for a location", "parameters": {"type": "object", "properties": {"location": {"type": "string", "description": "City name"}}, "required": ["location"]}},
    "set_alarm": {"name": "set_alarm", "description": "Set an alarm for a given time", "parameters": {"type": "object", "properties": {"hour": {"type": "integer", "description": "Hour to set the alarm for"}, "minute": {"type": "integer", "description": "Minute to set the alarm for"}}, "required": ["hour", "minute"]}},
    "send_message": {"name": "send_message", "description": "Send a message to a contact", "parameters": {"type": "object", "properties": {"recipient": {"type": "string", "description": "Name of the person to send the message to"}, "message": {"type": "string", "description": "The message content to send"}}, "required": ["recipient", "message"]}},
    "create_reminder": {"name": "create_reminder", "description": "Create a reminder with a title and time", "parameters": {"type": "object", "properties": {"title": {"type": "string", "description": "Reminder title"}, "time": {"type": "string", "description": "Time for the reminder (e.g. 3:00 PM)"}}, "required": ["title", "time"]}},
    "play_music": {"name": "play_music", "description": "Play a song or playlist", "parameters": {"type": "object", "properties": {"song": {"type": "string", "description": "Song or playlist name"}}, "required": ["song"]}},
    "set_timer": {"name": "set_timer", "description": "Set a countdown timer", "parameters": {"type": "object", "properties": {"minutes": {"type": "integer", "description": "Number of minutes"}}, "required": ["minutes"]}},
}

import json

# Test reminder_and_message
print("=== reminder_and_message ===")
result = generate_hybrid(
    [{"role": "user", "content": "Remind me about groceries at 5:00 PM and text Lisa saying see you tonight."}],
    [TOOLS["create_reminder"], TOOLS["send_message"], TOOLS["get_weather"], TOOLS["set_alarm"]]
)
print(f"  calls: {json.dumps(result['function_calls'], indent=2)}")
print(f"  num_calls: {len(result['function_calls'])}")
print(f"  time: {result['total_time_ms']:.1f}ms")

# Test timer_music_reminder
print("\n=== timer_music_reminder ===")
result = generate_hybrid(
    [{"role": "user", "content": "Set a 15 minute timer, play classical music, and remind me to stretch at 4:00 PM."}],
    [TOOLS["set_timer"], TOOLS["play_music"], TOOLS["create_reminder"], TOOLS["get_weather"], TOOLS["send_message"]]
)
print(f"  calls: {json.dumps(result['function_calls'], indent=2)}")
print(f"  num_calls: {len(result['function_calls'])}")
print(f"  time: {result['total_time_ms']:.1f}ms")

# Test music_among_three
print("\n=== music_among_three ===")
result = generate_hybrid(
    [{"role": "user", "content": "Play some jazz music."}],
    [TOOLS["set_alarm"], TOOLS["play_music"], TOOLS["get_weather"]]
)
print(f"  calls: {json.dumps(result['function_calls'], indent=2)}")
print(f"  time: {result['total_time_ms']:.1f}ms")
