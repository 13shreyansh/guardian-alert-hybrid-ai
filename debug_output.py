"""See what generate_hybrid actually returns for the 2 failing cases."""
import json, sys
sys.path.insert(0, ".")
from main import generate_hybrid
from benchmark import BENCHMARKS, compute_f1

failing = ["search_and_message", "timer_music_reminder"]

for bench in BENCHMARKS:
    if bench["name"] not in failing:
        continue

    print(f"\n{'='*60}")
    print(f"CASE: {bench['name']}")
    print(f"QUERY: {bench['messages'][0]['content']}")
    
    result = generate_hybrid(bench["messages"], bench["tools"])
    
    print(f"\nPREDICTED ({len(result['function_calls'])} calls):")
    for c in result["function_calls"]:
        print(f"  {c['name']}: {json.dumps(c['arguments'])}")
    
    print(f"\nEXPECTED ({len(bench['expected_calls'])} calls):")
    for c in bench["expected_calls"]:
        print(f"  {c['name']}: {json.dumps(c['arguments'])}")
    
    f1 = compute_f1(result["function_calls"], bench["expected_calls"])
    print(f"\nF1: {f1:.2f}")
    print(f"Time: {result['total_time_ms']:.1f}ms")
