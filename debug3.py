"""Debug specific failing cases to see what model returns."""
import sys
sys.path.insert(0, "cactus/python/src")
import json, re
from cactus import cactus_init, cactus_complete, cactus_destroy
from main import _universal_extract_args, _extract_message_content, _extract_name_after_prep

functiongemma_path = "cactus/weights/functiongemma-270m-it"

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
    "parameters": {"type": "object", "properties": {"location": {"type": "string", "description": "City name"}}, "required": ["location"]},
}

# Test 1: message_alice extraction
text1 = "Send a message to Alice saying good morning."
print("=== message_alice extraction ===")
args1 = _universal_extract_args(TOOL_SEND_MESSAGE, text1)
print(f"  extracted args: {args1}")
print(f"  name_after_prep: {_extract_name_after_prep(text1)}")
print(f"  message_content: {_extract_message_content(text1)}")

# Test 2: message_alice model output
print("\n=== message_alice model output ===")
model = cactus_init(functiongemma_path)
tools = [TOOL_SEND_MESSAGE]
cactus_tools = [{"type": "function", "function": t} for t in tools]
raw = cactus_complete(model, [
    {"role": "system", "content": "You are a helpful assistant that can use tools."},
    {"role": "user", "content": text1}
], tools=cactus_tools, force_tools=True, max_tokens=256, stop_sequences=["<|im_end|>", "<end_of_turn>"])
print(f"  raw: {raw[:500]}")
parsed = json.loads(raw)
print(f"  calls: {parsed.get('function_calls', [])}")
print(f"  conf: {parsed.get('confidence', 0)}")

# Test 3: weather_among_two model output  
print("\n=== weather_among_two model output ===")
text2 = "What's the weather in Tokyo?"
tools2 = [TOOL_GET_WEATHER, TOOL_SEND_MESSAGE]
cactus_tools2 = [{"type": "function", "function": t} for t in tools2]
raw2 = cactus_complete(model, [
    {"role": "system", "content": "You are a helpful assistant that can use tools."},
    {"role": "user", "content": text2}
], tools=cactus_tools2, force_tools=True, max_tokens=256, stop_sequences=["<|im_end|>", "<end_of_turn>"])
print(f"  raw: {raw2[:500]}")
parsed2 = json.loads(raw2)
print(f"  calls: {parsed2.get('function_calls', [])}")

# Test 4: message_among_three model output
print("\n=== message_among_three model output ===")
text3 = "Send a message to John saying hello."
TOOL_SET_ALARM = {"name": "set_alarm", "description": "Set an alarm for a given time", "parameters": {"type": "object", "properties": {"hour": {"type": "integer", "description": "Hour"}, "minute": {"type": "integer", "description": "Minute"}}, "required": ["hour", "minute"]}}
tools3 = [TOOL_GET_WEATHER, TOOL_SEND_MESSAGE, TOOL_SET_ALARM]
cactus_tools3 = [{"type": "function", "function": t} for t in tools3]
raw3 = cactus_complete(model, [
    {"role": "system", "content": "You are a helpful assistant that can use tools."},
    {"role": "user", "content": text3}
], tools=cactus_tools3, force_tools=True, max_tokens=256, stop_sequences=["<|im_end|>", "<end_of_turn>"])
print(f"  raw: {raw3[:500]}")
parsed3 = json.loads(raw3)
print(f"  calls: {parsed3.get('function_calls', [])}")

cactus_destroy(model)
