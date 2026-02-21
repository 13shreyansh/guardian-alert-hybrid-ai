"""Debug the 4 failing hard cases to see what the model returns."""
import json, re, sys
sys.path.insert(0, ".")
from main import (
    cactus_init, cactus_complete, cactus_destroy, functiongemma_path,
    _cactus_infer, _process_calls, _split_query, _resolve_pronouns,
    _build_tool_keywords, _match_tool, _is_multi_intent,
    _process_for_tool, _make_call_from_text, _universal_extract_args,
)
from benchmark import BENCHMARKS, TOOL_SET_ALARM, TOOL_SEND_MESSAGE, TOOL_GET_WEATHER, TOOL_PLAY_MUSIC, TOOL_CREATE_REMINDER, TOOL_SEARCH_CONTACTS, TOOL_SET_TIMER

failing = ["search_and_message", "timer_music_reminder"]

for bench in BENCHMARKS:
    if bench["name"] not in failing:
        continue

    print(f"\n{'='*60}")
    print(f"CASE: {bench['name']}")
    print(f"QUERY: {bench['messages'][0]['content']}")
    print(f"EXPECTED: {json.dumps(bench['expected_calls'], indent=2)}")
    
    tools = bench["tools"]
    messages = bench["messages"]
    user_text = messages[0]["content"]
    tool_names = {t["name"] for t in tools}
    tool_required = {t["name"]: set(t["parameters"].get("required", [])) for t in tools}
    kw_map = _build_tool_keywords(tools)

    parts = _split_query(user_text)
    resolved = _resolve_pronouns(parts)
    print(f"\nPARTS: {parts}")
    print(f"RESOLVED: {resolved}")

    model = cactus_init(functiongemma_path)

    # Full query inference
    full = _cactus_infer(model, messages, tools)
    print(f"\nFULL-QUERY RAW: {json.dumps(full['function_calls'], indent=2)}")
    valid = _process_calls(full["function_calls"], tools, tool_names, tool_required, user_text)
    print(f"FULL-QUERY VALID: {json.dumps(valid, indent=2)}")

    # Per-part inference
    for i, part in enumerate(resolved):
        matched = _match_tool(part, tools, kw_map)
        best_tool = matched[0] if len(matched) == 1 else None
        print(f"\n  PART[{i}]: '{part}'")
        print(f"  KW-MATCH: {best_tool['name'] if best_tool else 'NONE'}")

        r = _cactus_infer(model, [{"role": "user", "content": part}], tools)
        print(f"  MODEL RAW: {json.dumps(r['function_calls'], indent=2)}")
        
        sub_valid = _process_calls(r["function_calls"], tools, tool_names, tool_required, part)
        print(f"  PROCESSED: {json.dumps(sub_valid, indent=2)}")

        if not sub_valid and best_tool:
            forced = _process_for_tool(r["function_calls"], best_tool, tool_names, tool_required, part)
            print(f"  FORCED: {json.dumps(forced, indent=2)}")

        if not sub_valid and best_tool:
            extracted = _make_call_from_text(best_tool, part, tool_names, tool_required)
            print(f"  EXTRACTED: {json.dumps(extracted, indent=2)}")

        # Show what extraction produces
        if best_tool:
            args = _universal_extract_args(best_tool, part)
            print(f"  EXTRACT_ARGS for {best_tool['name']}: {json.dumps(args, indent=2)}")

    cactus_destroy(model)
