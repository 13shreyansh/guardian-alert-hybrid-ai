"""Debug remaining failing cases."""
import sys
sys.path.insert(0, "cactus/python/src")
from main import (
    _extract_label, _extract_time_str, _extract_song_title,
    _extract_message_content, _extract_name_after_prep,
    _extract_location, _extract_query,
    _match_tool, _build_tool_keywords, _universal_extract_args,
    _make_call_from_text
)

# Tool definitions matching benchmark
TOOLS = {
    "get_weather": {"name": "get_weather", "description": "Get current weather for a location", "parameters": {"type": "object", "properties": {"location": {"type": "string", "description": "City name"}}, "required": ["location"]}},
    "set_alarm": {"name": "set_alarm", "description": "Set an alarm for a given time", "parameters": {"type": "object", "properties": {"hour": {"type": "integer", "description": "Hour to set the alarm for"}, "minute": {"type": "integer", "description": "Minute to set the alarm for"}}, "required": ["hour", "minute"]}},
    "send_message": {"name": "send_message", "description": "Send a message to a contact", "parameters": {"type": "object", "properties": {"recipient": {"type": "string", "description": "Name of the person to send the message to"}, "message": {"type": "string", "description": "The message content to send"}}, "required": ["recipient", "message"]}},
    "create_reminder": {"name": "create_reminder", "description": "Create a reminder with a title and time", "parameters": {"type": "object", "properties": {"title": {"type": "string", "description": "Reminder title"}, "time": {"type": "string", "description": "Time for the reminder (e.g. 3:00 PM)"}}, "required": ["title", "time"]}},
    "search_contacts": {"name": "search_contacts", "description": "Search for a contact by name", "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Name to search for"}}, "required": ["query"]}},
    "play_music": {"name": "play_music", "description": "Play a song or playlist", "parameters": {"type": "object", "properties": {"song": {"type": "string", "description": "Song or playlist name"}}, "required": ["song"]}},
    "set_timer": {"name": "set_timer", "description": "Set a countdown timer", "parameters": {"type": "object", "properties": {"minutes": {"type": "integer", "description": "Number of minutes"}}, "required": ["minutes"]}},
}

tool_names = set(TOOLS.keys())
tool_required = {t["name"]: set(t["parameters"].get("required", [])) for t in TOOLS.values()}

# ============ music_among_three ============
print("=== music_among_three ===")
text = "Play some jazz music."
tools = [TOOLS["set_alarm"], TOOLS["play_music"], TOOLS["get_weather"]]
kw_map = _build_tool_keywords(tools)
match = _match_tool(text, tools, kw_map)
print(f"  kw match: {[m['name'] for m in match]}")
args = _universal_extract_args(TOOLS["play_music"], text)
print(f"  play_music args: {args}")
print(f"  song_title: {_extract_song_title(text)}")

# ============ reminder_among_four ============
print("\n=== reminder_among_four ===")
text = "Remind me to call the dentist at 2:00 PM."
tools = [TOOLS["get_weather"], TOOLS["send_message"], TOOLS["create_reminder"], TOOLS["set_alarm"]]
kw_map = _build_tool_keywords(tools)
match = _match_tool(text, tools, kw_map)
print(f"  kw match: {[m['name'] for m in match]}")
args = _universal_extract_args(TOOLS["create_reminder"], text)
print(f"  create_reminder args: {args}")
call = _make_call_from_text(TOOLS["create_reminder"], text, tool_names, tool_required)
print(f"  make_call result: {call}")

# ============ message_among_four ============
print("\n=== message_among_four ===")
text = "Text Dave saying I'll be late."
tools = [TOOLS["get_weather"], TOOLS["set_timer"], TOOLS["send_message"], TOOLS["play_music"]]
kw_map = _build_tool_keywords(tools)
match = _match_tool(text, tools, kw_map)
print(f"  kw match: {[m['name'] for m in match]}")
# Check each tool extraction
for t in tools:
    args = _universal_extract_args(t, text)
    valid = _make_call_from_text(t, text, tool_names, tool_required)
    print(f"  {t['name']}: extracted={args}, valid={valid}")

# ============ reminder_and_message ============
print("\n=== reminder_and_message (split test) ===")
text = "Remind me about groceries at 5:00 PM and text Lisa saying see you tonight."
from main import _split_query, _is_multi_intent, _resolve_pronouns
tools = [TOOLS["create_reminder"], TOOLS["send_message"], TOOLS["get_weather"], TOOLS["set_alarm"]]
parts = _split_query(text)
print(f"  parts: {parts}")
kw_map = _build_tool_keywords(tools)
for p in parts:
    match = _match_tool(p, tools, kw_map)
    print(f"  '{p}' → match: {[m['name'] for m in match]}")
    for m in match:
        args = _universal_extract_args(m, p)
        print(f"    {m['name']} args from sub-query: {args}")

# ============ search_and_message ============
print("\n=== search_and_message (split test) ===")
text = "Find Tom in my contacts and send him a message saying happy birthday."
tools = [TOOLS["search_contacts"], TOOLS["send_message"], TOOLS["get_weather"], TOOLS["play_music"]]
parts = _split_query(text)
print(f"  parts: {parts}")
resolved = _resolve_pronouns(parts)
print(f"  resolved: {resolved}")
kw_map = _build_tool_keywords(tools)
for p in resolved:
    match = _match_tool(p, tools, kw_map)
    print(f"  '{p}' → match: {[m['name'] for m in match]}")
    for m in match:
        args = _universal_extract_args(m, p)
        print(f"    {m['name']} args from sub-query: {args}")
