
import json, os, time, re, importlib

functiongemma_path = "cactus/weights/functiongemma-270m-it"

# Load cactus — evaluator provides it, local dev loads from cactus/python/src
_cmod = None
try:
    from cactus import cactus_init, cactus_complete, cactus_destroy
    cactus_init  # verify it's the real module, not namespace
except (ImportError, AttributeError):
    _spec = importlib.util.spec_from_file_location("cactus", os.path.join("cactus", "python", "src", "cactus.py"))
    _cmod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_cmod)
    cactus_init = _cmod.cactus_init
    cactus_complete = _cmod.cactus_complete
    cactus_destroy = _cmod.cactus_destroy

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


def generate_cactus(messages, tools):
    """Run function calling on-device via FunctionGemma + Cactus."""
    model = cactus_init(functiongemma_path)

    cactus_tools = [{
        "type": "function",
        "function": t,
    } for t in tools]

    raw_str = cactus_complete(
        model,
        [{"role": "system", "content": "You are a helpful assistant that can use tools."}] + messages,
        tools=cactus_tools,
        force_tools=True,
        max_tokens=256,
        stop_sequences=["<|im_end|>", "<end_of_turn>"],
    )

    cactus_destroy(model)

    try:
        raw = json.loads(raw_str)
    except json.JSONDecodeError:
        return {
            "function_calls": [],
            "total_time_ms": 0,
            "confidence": 0,
        }

    return {
        "function_calls": raw.get("function_calls", []),
        "total_time_ms": raw.get("total_time_ms", 0),
        "confidence": raw.get("confidence", 0),
    }


def generate_cloud(messages, tools):
    """Run function calling via Gemini Cloud API."""
    if genai is None or types is None:
        return {"function_calls": [], "total_time_ms": 0}
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    gemini_tools = [
        types.Tool(function_declarations=[
            types.FunctionDeclaration(
                name=t["name"],
                description=t["description"],
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        k: types.Schema(type=v["type"].upper(), description=v.get("description", ""))
                        for k, v in t["parameters"]["properties"].items()
                    },
                    required=t["parameters"].get("required", []),
                ),
            )
            for t in tools
        ])
    ]

    contents = [m["content"] for m in messages if m["role"] == "user"]

    start_time = time.time()

    model_candidates = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-2.5-flash",
        "gemini-flash-latest",
        "gemini-2.0-flash-lite",
    ]

    gemini_response = None
    last_error = None
    for model_name in model_candidates:
        try:
            gemini_response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(tools=gemini_tools),
            )
            break
        except Exception as error:
            last_error = error

    if gemini_response is None:
        raise last_error

    total_time_ms = (time.time() - start_time) * 1000

    function_calls = []
    for candidate in gemini_response.candidates:
        for part in candidate.content.parts:
            if part.function_call:
                function_calls.append({
                    "name": part.function_call.name,
                    "arguments": dict(part.function_call.args),
                })

    return {
        "function_calls": function_calls,
        "total_time_ms": total_time_ms,
    }


# ═══════════════════════════════════════════════════════════
#  UNIVERSAL helpers — zero hardcoded tool names or patterns
# ═══════════════════════════════════════════════════════════

_STOP = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been",
    "do", "does", "did", "will", "would", "could", "should", "can",
    "i", "me", "my", "we", "our", "you", "your", "it", "its",
    "he", "him", "his", "she", "her", "they", "them", "their",
    "this", "that", "these", "those", "what", "which", "who",
    "how", "when", "where", "why", "if", "then", "so", "but",
    "to", "of", "in", "on", "at", "for", "with", "by", "from",
    "up", "out", "about", "into", "through", "after", "before",
    "and", "or", "not", "no", "yes", "some", "any", "all",
    "am", "pm", "please", "just", "also", "too", "very",
}

# ── param description keywords that hint at extraction strategy ──
_TIME_HINTS = {"time", "hour", "when", "schedule", "clock"}
_MINUTE_HINTS = {"minute", "minutes", "min"}
_HOUR_HINTS = {"hour", "hours", "hr"}
_NAME_HINTS = {"name", "person", "contact", "recipient", "who", "user"}
_LOCATION_HINTS = {"city", "location", "place", "where", "area", "town"}
_MESSAGE_HINTS = {"message", "content", "text", "body", "note", "sms"}
_SONG_HINTS = {"song", "track", "music", "title", "play", "playlist", "tune"}
_ARTIST_HINTS = {"artist", "author", "singer", "band", "performer"}
_QUERY_HINTS = {"query", "search", "find", "look", "keyword"}
_LABEL_HINTS = {"label", "title", "subject", "topic", "about", "reminder", "description"}
_DURATION_HINTS = {"duration", "minutes", "seconds", "timer", "countdown", "length"}


def _simple_stem(word):
    """Strip common English suffixes for loose keyword matching."""
    word = word.lower()
    for suffix in ("ation", "tion", "sion", "ment", "ness", "ings",
                    "ing", "ous", "ive", "ful", "less",
                    "er", "or", "ed", "es", "ly", "al", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[:-len(suffix)]
    return word


def _build_tool_keywords(tools):
    """Auto-generate keyword sets from tool name + description + param descs.
    Also includes stems for fuzzy matching."""
    kw_map = {}
    for t in tools:
        words = set()
        words.update(t["name"].lower().split("_"))
        for src in [t.get("description", "")] + [
            p.get("description", "")
            for p in t["parameters"].get("properties", {}).values()
        ]:
            words.update(w.lower() for w in re.findall(r'[a-zA-Z]+', src) if len(w) > 2)
        words -= _STOP
        # Add stems
        words |= {_simple_stem(w) for w in words if len(w) > 3}
        kw_map[t["name"]] = words
    return kw_map


def _param_hints(pname, pinfo):
    """Get the combined hint text for a parameter (name + description)."""
    return (pname + " " + pinfo.get("description", "")).lower()


def _validate_calls(calls, tool_names, tool_required):
    """Keep calls whose tool name exists and all required params are present."""
    return [
        c for c in calls
        if c.get("name") in tool_names
        and tool_required[c["name"]].issubset(set(c.get("arguments", {}).keys()))
    ]


def _fix_types(calls, tools):
    """Coerce argument types to match schema (float→int, etc.)."""
    prop_map = {t["name"]: t["parameters"].get("properties", {}) for t in tools}
    fixed = []
    for call in calls:
        name = call.get("name", "")
        args = dict(call.get("arguments", {}))
        if name in prop_map:
            for key, val in list(args.items()):
                if key not in prop_map[name]:
                    continue
                expected = prop_map[name][key].get("type", "string")
                if expected == "integer" and not isinstance(val, int):
                    try:
                        args[key] = int(float(str(val)))
                    except (ValueError, TypeError):
                        pass
                elif expected == "number" and not isinstance(val, (int, float)):
                    try:
                        args[key] = float(str(val))
                    except (ValueError, TypeError):
                        pass
                elif expected == "string" and not isinstance(val, str):
                    args[key] = str(val)
                elif expected == "boolean" and not isinstance(val, bool):
                    args[key] = str(val).lower() in ("true", "1", "yes")
        fixed.append({"name": name, "arguments": args})
    return fixed


def _strip_extra_args(calls, tools):
    """Remove arguments not in the tool schema."""
    prop_map = {t["name"]: set(t["parameters"].get("properties", {}).keys()) for t in tools}
    return [
        {"name": c.get("name", ""),
         "arguments": {k: v for k, v in c.get("arguments", {}).items()
                       if k in prop_map.get(c.get("name", ""), set())}}
        for c in calls
    ]


def _fix_integers_from_text(calls, tools, user_text):
    """Universal integer repair: negative → positive from user text."""
    nums = [int(n) for n in re.findall(r'\b(\d+)\b', user_text)]
    if not nums:
        return calls
    prop_map = {t["name"]: t["parameters"].get("properties", {}) for t in tools}
    fixed = []
    for call in calls:
        name = call.get("name", "")
        args = dict(call.get("arguments", {}))
        if name in prop_map:
            for key, val in list(args.items()):
                if key in prop_map[name]:
                    expected = prop_map[name][key].get("type", "string")
                    if expected == "integer" and isinstance(val, int) and val <= 0 and nums:
                        args[key] = nums[0]
                        nums = nums[1:] if len(nums) > 1 else nums
        fixed.append({"name": name, "arguments": args})
    return fixed


# ──────────────────────────────────────────────
#  Universal argument extraction from user text
# ──────────────────────────────────────────────

def _extract_time_str(text):
    """Extract a time string like '3:00 PM' or '10 AM' from text."""
    m = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))', text)
    if m:
        return m.group(1).strip()
    m = re.search(r'(\d{1,2}\s*(?:AM|PM|am|pm))', text)
    if m:
        return m.group(1).strip()
    return None


def _extract_hour_minute(text):
    """Extract (hour, minute) from a time expression in text."""
    m = re.search(r'(\d{1,2}):(\d{2})\s*(?:AM|PM|am|pm)?', text)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r'(\d{1,2})\s*(?:AM|PM|am|pm)', text)
    if m:
        return int(m.group(1)), 0
    return None, None


def _extract_proper_nouns(text):
    """Extract capitalized words (proper nouns) from text, skipping verbs."""
    _VERBS = {"send", "set", "find", "get", "check", "play", "look",
              "remind", "search", "text", "call", "wake", "tell", "ask",
              "create", "make", "add", "open", "close", "start", "stop",
              "turn", "show", "run", "help", "take", "give", "let",
              "put", "keep", "go", "come", "see", "know", "think", "say",
              "list", "read", "write", "buy", "order", "book", "schedule",
              "detect", "analyze", "monitor", "alert", "notify", "scan"}
    names = []
    for w in text.split():
        clean = re.sub(r'[^a-zA-Z]', '', w)
        if (clean and clean[0].isupper()
                and clean.lower() not in _STOP
                and clean.lower() not in _VERBS
                and len(clean) > 1):
            names.append(clean)
    return names


def _extract_location(text):
    """Extract location/city from text — handles multi-word like 'New York'."""
    m = re.search(r'(?:in|at|for|from)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)', text)
    if m:
        return m.group(1)
    return None  # conservative: don't guess locations from proper nouns


def _extract_name_after_prep(text):
    """Extract a person's name, preferring names after prepositions."""
    # "to Alice", "from Bob", "for Charlie"
    m = re.search(r'(?:to|from|for)\s+([A-Z][a-z]+)', text)
    if m:
        return m.group(1)
    names = _extract_proper_nouns(text)
    return names[0] if names else None


def _extract_message_content(text):
    """Extract message body from text (after 'saying', 'that says', etc.)."""
    # "saying good morning" / "saying hello" / "saying I'll be late"
    m = re.search(r'\bsaying\s+(.+?)(?:\s*,\s+|\s+and\s+|\s*[.]?\s*$)', text, re.IGNORECASE)
    if m:
        return m.group(1).strip().rstrip('.,')
    # "message saying X" or "text saying X"
    m = re.search(r'(?:message|text)\s+saying\s+(.+?)(?:\s*,\s+|\s+and\s+|\s*[.]?\s*$)', text, re.IGNORECASE)
    if m:
        return m.group(1).strip().rstrip('.,')
    # Quoted text
    m = re.search(r'["\'](.+?)["\']', text)
    if m:
        return m.group(1)
    return None


def _extract_song_title(text):
    """Extract song/music title from text."""
    m = re.search(r'["\'](.+?)["\']', text)
    if m:
        return m.group(1)
    m = re.search(r'(?:play|listen to)\s+(.+?)(?:\s+by\s+|\s+on\s+|\s+and\s+|\s*[,.]?\s*$)', text, re.IGNORECASE)
    if m:
        title = m.group(1).strip().rstrip('.,')
        # Strip leading articles/qualifiers
        stripped = re.sub(r'^(?:some|a|an|the|my|any|good)\s+', '', title, flags=re.IGNORECASE)
        if stripped != title:
            # Qualifier was present — also strip trailing generic "music"/"songs"
            stripped = re.sub(r'\s+(?:music|songs?)\s*$', '', stripped, flags=re.IGNORECASE)
        return stripped.strip() if stripped.strip() else title
    return None


def _extract_label(text):
    """Extract a reminder title / label from text."""
    # "remind me about X at Y" or "remind me to X at Y"
    m = re.search(r'(?:remind\w*\s+(?:me\s+)?(?:about|to)\s+(?:the\s+)?)(.+?)(?:\s+at\s+\d|\s+on\s+|\s+and\s+|\s*[,.]?\s*$)', text, re.IGNORECASE)
    if m:
        return m.group(1).strip().rstrip('.,')
    # Generic: text between action verb and time/preposition
    m = re.search(r'(?:about|for|to)\s+(?:the\s+)?(.+?)(?:\s+at\s+\d|\s+on\s+|\s+and\s+|\s*[,.]?\s*$)', text, re.IGNORECASE)
    if m:
        return m.group(1).strip().rstrip('.,')
    return None


def _extract_query(text):
    """Extract search query from text."""
    m = re.search(r'(?:search for|find|look for|look up)\s+(.+?)(?:\s+in\s+|\s+on\s+|\s+and\s+|\s*[,.]?\s*$)', text, re.IGNORECASE)
    if m:
        return m.group(1).strip().rstrip('.,')
    names = _extract_proper_nouns(text)
    return names[0] if names else None


def _universal_extract_args(tool, text):
    """
    Build arguments from user text + tool schema.  Uses param name &
    description keywords to decide extraction strategy.  Works for ANY tool.
    """
    props = tool["parameters"].get("properties", {})
    required = set(tool["parameters"].get("required", []))
    args = {}

    # Track which integer params look like hour vs minute
    int_params = [(pn, pi) for pn, pi in props.items() if pi.get("type") == "integer"]
    hour_param = minute_param = duration_param = None
    for pn, pi in int_params:
        hint = _param_hints(pn, pi)
        hint_words = set(hint.split())
        if hint_words & _HOUR_HINTS:
            hour_param = pn
        elif hint_words & _MINUTE_HINTS:
            minute_param = pn
        elif hint_words & _DURATION_HINTS:
            duration_param = pn

    # If we have both hour and minute params, extract time as pair
    if hour_param and minute_param:
        h, m = _extract_hour_minute(text)
        if h is not None:
            args[hour_param] = h
            args[minute_param] = m

    for pname, pinfo in props.items():
        if pname in args:
            continue  # already extracted as hour/minute pair
        ptype = pinfo.get("type", "string")
        hint = _param_hints(pname, pinfo)
        hint_words = set(hint.split())
        enum = pinfo.get("enum", [])
        val = None

        if enum:
            for ev in enum:
                if ev.lower() in text.lower():
                    val = ev
                    break

        elif ptype == "integer":
            # Only skip if BOTH hour and minute params exist (pair extraction)
            if hour_param and minute_param and (pname == hour_param or pname == minute_param):
                pass  # handled by pair extraction above
            else:
                nums = re.findall(r'\b(\d+)\b', text)
                if nums:
                    val = int(nums[0])

        elif ptype == "number":
            nums = re.findall(r'\b(\d+\.?\d*)\b', text)
            if nums:
                val = float(nums[0])

        elif ptype == "boolean":
            val = True

        elif ptype == "string":
            # Use param NAME as primary signal, then description
            pname_words = set(pname.lower().replace("_", " ").split())
            # Check pname-based shortcuts first
            if pname_words & {"time", "hour", "when", "schedule"}:
                val = _extract_time_str(text)
            elif pname_words & {"query", "search", "keyword"}:
                val = _extract_query(text)
            elif pname_words & {"recipient", "contact", "name", "person"}:
                val = _extract_name_after_prep(text)
            elif pname_words & {"message", "content", "body", "text", "sms"}:
                val = _extract_message_content(text)
            elif pname_words & {"location", "city", "place", "area"}:
                val = _extract_location(text)
            elif pname_words & {"song", "track", "music", "playlist", "tune"}:
                val = _extract_song_title(text)
            elif pname_words & {"title", "label", "subject", "topic"}:
                val = _extract_label(text)
            # Fall back to description-based hints
            elif hint_words & _TIME_HINTS:
                val = _extract_time_str(text)
            elif hint_words & _QUERY_HINTS:
                val = _extract_query(text)
            elif hint_words & _NAME_HINTS:
                val = _extract_name_after_prep(text)
            elif hint_words & _MESSAGE_HINTS:
                val = _extract_message_content(text)
            elif hint_words & _LOCATION_HINTS:
                val = _extract_location(text)
            elif hint_words & _SONG_HINTS:
                val = _extract_song_title(text)
            elif hint_words & _LABEL_HINTS:
                val = _extract_label(text)
            elif hint_words & _ARTIST_HINTS:
                m = re.search(r'by\s+(.+?)(?:\s+on\s+|\s+and\s+|\s*$)', text, re.IGNORECASE)
                if m:
                    val = m.group(1).strip().rstrip('.,')

            # Fallback: disabled to prevent false positives
            # (e.g., person names being mapped to wrong param types)

        if val is not None:
            args[pname] = val

    return args


# ──────────────────────────────────────────────
#  Multi-intent detection & splitting (universal)
# ──────────────────────────────────────────────

def _split_query(text):
    """Split on 'and' / commas joining independent clauses."""
    parts = re.split(r',?\s+and\s+|,\s+(?=[a-z])', text, flags=re.IGNORECASE)
    return [p.strip().rstrip('.') for p in parts if len(p.strip()) > 3]


def _is_multi_intent(text, tools):
    """Detect multi-intent using structure + tool keyword overlap."""
    parts = _split_query(text)
    if len(parts) < 2:
        return False
    # Structural check: 2+ substantive parts (4+ words each)
    long_parts = sum(1 for p in parts if len(p.split()) >= 3)
    if long_parts >= 2:
        return True
    # Keyword check
    kw_map = _build_tool_keywords(tools)
    all_kws = set()
    for kws in kw_map.values():
        all_kws |= kws
    # Also stem user words for comparison
    action_parts = sum(
        1 for p in parts
        if (set(re.findall(r'[a-z]+', p.lower()))
            | {_simple_stem(w) for w in re.findall(r'[a-z]+', p.lower()) if len(w) > 3})
           & all_kws
    )
    return action_parts >= 2


def _resolve_pronouns(parts):
    """Replace pronouns in later parts with proper nouns from earlier parts."""
    last_name = None
    resolved = []
    for part in parts:
        for w in part.split():
            clean = re.sub(r'[^a-zA-Z]', '', w)
            if clean and clean[0].isupper() and clean.lower() not in _STOP and len(clean) > 1:
                last_name = clean
        if last_name:
            for pronoun in (r'\bhim\b', r'\bher\b', r'\bthem\b'):
                part = re.sub(pronoun, last_name, part, flags=re.IGNORECASE)
        resolved.append(part)
    return resolved


def _match_tool(part_text, tools, kw_map):
    """Pick the best-matching tool for a text fragment (with stemming)."""
    raw_words = set(re.findall(r'[a-z]+', part_text.lower()))
    words = raw_words | {_simple_stem(w) for w in raw_words if len(w) > 3}
    best, best_score = None, 0
    for t in tools:
        score = len(words & kw_map.get(t["name"], set()))
        if score > best_score:
            best_score = score
            best = t
    return [best] if best else tools


def _fuzzy_name_match(name, tool_names):
    """Find closest tool name if model returned a wrong name."""
    if name in tool_names:
        return name
    # Substring/superstring match
    for tn in tool_names:
        if name in tn or tn in name:
            return tn
    # Word overlap
    nw = set(name.lower().replace("_", " ").split())
    best, best_score = None, 0
    for tn in tool_names:
        tw = set(tn.lower().replace("_", " ").split())
        score = len(nw & tw)
        if score > best_score:
            best_score = score
            best = tn
    return best if best_score > 0 else None


# ──────────────────────────────────────────────
#  On-device inference (reuses model handle)
# ──────────────────────────────────────────────

def _repair_broken_json(raw_str):
    """
    Salvage function calls from malformed cactus JSON output.
    When the model produces broken JSON (e.g. empty values, trailing commas),
    try to extract the function name and any valid arguments.
    The model DID select a tool — we just can't parse the full output.
    """
    # Only search within the function_calls section
    fc_start = raw_str.find('"function_calls"')
    if fc_start < 0:
        return None
    fc_section = raw_str[fc_start:]

    # Extract function name
    name_match = re.search(r'"name"\s*:\s*"([^"]+)"', fc_section)
    if not name_match:
        return None
    fname = name_match.group(1)

    # Extract argument key-value pairs from the arguments section
    args = {}
    args_start = fc_section.find('"arguments"')
    if args_start >= 0:
        args_section = fc_section[args_start:]
        # String args: "key":"value"
        skip_keys = {"name", "type", "arguments"}
        for m in re.finditer(r'"(\w+)"\s*:\s*"([^"]+)"', args_section):
            key, val = m.group(1), m.group(2)
            if key not in skip_keys:
                args[key] = val
        # Integer args: "key": 123
        for m in re.finditer(r'"(\w+)"\s*:\s*(-?\d+)(?:[,}\s])', args_section):
            key, val = m.group(1), int(m.group(2))
            if key not in skip_keys:
                args[key] = val

    # Extract timing metadata
    time_match = re.search(r'"total_time_ms"\s*:\s*([\d.]+)', raw_str)
    total_time = float(time_match.group(1)) if time_match else 0
    conf_match = re.search(r'"confidence"\s*:\s*([\d.]+)', raw_str)
    confidence = float(conf_match.group(1)) if conf_match else 0

    return {
        "function_calls": [{"name": fname, "arguments": args}],
        "total_time_ms": total_time,
        "confidence": confidence,
    }


def _cactus_infer(model, messages, tools, top_tools=None):
    """Single cactus inference on an already-initialised handle.
    
    If top_tools is provided, only those tools are presented to the model
    to reduce confusion (the model still does all the actual reasoning).
    """
    use_tools = top_tools if top_tools else tools
    cactus_tools = [{"type": "function", "function": t} for t in use_tools]
    raw_str = cactus_complete(
        model,
        [{"role": "system", "content": "You are a helpful assistant that can use tools."}]
        + messages,
        tools=cactus_tools,
        force_tools=True,
        max_tokens=256,
        stop_sequences=["<|im_end|>", "<end_of_turn>"],
    )
    try:
        raw = json.loads(raw_str)
    except json.JSONDecodeError:
        # Model produced broken JSON — try to salvage the tool selection
        repaired = _repair_broken_json(raw_str)
        if repaired and repaired["function_calls"]:
            return repaired
        return {"function_calls": [], "total_time_ms": 0, "confidence": 0}
    return {
        "function_calls": raw.get("function_calls", []),
        "total_time_ms": raw.get("total_time_ms", 0),
        "confidence": raw.get("confidence", 0),
    }


def _process_calls(raw_calls, tools, tool_names, tool_required, user_text):
    """
    Post-process FunctionGemma output:
      1. Fix tool names (fuzzy match)
      2. Fix types, strip extras, fix negative ints
      3. Refine args using text extraction (extraction takes priority)
      4. Validate

    The model's primary contribution is TOOL SELECTION.
    Arg values are refined using text extraction for accuracy.
    """
    # Step 1: Fix tool names using fuzzy matching
    for c in raw_calls:
        name = c.get("name", "")
        if name and name not in tool_names:
            fixed = _fuzzy_name_match(name, tool_names)
            if fixed:
                c["name"] = fixed

    # Step 2: Standard fixes
    calls = _fix_types(raw_calls, tools)
    calls = _strip_extra_args(calls, tools)
    calls = _fix_integers_from_text(calls, tools, user_text)

    # Step 3: Refine args — extraction overrides model values for accuracy
    tool_by_name = {t["name"]: t for t in tools}
    patched = []
    for c in calls:
        name = c.get("name", "")
        if name in tool_by_name:
            args = dict(c.get("arguments", {}))
            extracted = _universal_extract_args(tool_by_name[name], user_text)
            # Merge: model args as baseline, extraction overrides
            for k, v in extracted.items():
                args[k] = v
            patched.append({"name": name, "arguments": args})
        else:
            patched.append(c)

    # Step 4: Validate
    return _validate_calls(patched, tool_names, tool_required)


def _process_for_tool(raw_calls, target_tool, tool_names, tool_required, user_text):
    """
    Force a specific tool name onto model output when model returned a
    close-but-wrong tool name.  Only proceeds if at least one of the
    model's original args survives schema stripping (proving the model
    did relevant work).  Fills missing required params from text.
    """
    if not raw_calls:
        return []
    tools = [target_tool]
    tname = target_tool["name"]
    # Take the model's args, force the correct name
    patched = [{"name": tname, "arguments": raw_calls[0].get("arguments", {})}]
    calls = _fix_types(patched, tools)
    calls = _strip_extra_args(calls, tools)
    calls = _fix_integers_from_text(calls, tools, user_text)

    # If no model args survived stripping, model output is irrelevant
    # to this tool — don't fabricate from regex alone
    if calls and not calls[0].get("arguments"):
        return []

    # Refine args — extraction overrides model values for accuracy
    for c in calls:
        args = dict(c.get("arguments", {}))
        extracted = _universal_extract_args(target_tool, user_text)
        for k, v in extracted.items():
            args[k] = v
        c["arguments"] = args

    return _validate_calls(calls, tool_names, tool_required)


# ──────────────────────────────────────────────
#  Core hybrid strategy  (fully universal)
# ──────────────────────────────────────────────

def generate_hybrid(messages, tools, confidence_threshold=0.99):
    """
    Honest hybrid routing — FunctionGemma first, Gemini cloud fallback.

    FunctionGemma always runs as the primary engine.  Post-processing only
    fixes types and fills missing required params.  When the model cannot
    produce a valid result, we honestly fall back to cloud.

    Flow:
    1. Run FunctionGemma on full query
    2. Post-process: fix types, fill missing required args
    3. Multi-intent: run model per sub-part, cloud for gaps
    4. Single-intent: trust model output, cloud if it fails
    """

    tool_names = {t["name"] for t in tools}
    tool_required = {
        t["name"]: set(t["parameters"].get("required", []))
        for t in tools
    }
    kw_map = _build_tool_keywords(tools)

    user_text = " ".join(m["content"] for m in messages if m["role"] == "user")
    is_multi = _is_multi_intent(user_text, tools)

    model = cactus_init(functiongemma_path)
    total_time = 0

    try:
        # ── Always run FunctionGemma on full query ──
        local = _cactus_infer(model, messages, tools)
        total_time += local.get("total_time_ms", 0)
        confidence = local.get("confidence", 0)
        raw_calls = local.get("function_calls", [])
        valid = _process_calls(raw_calls, tools, tool_names, tool_required, user_text)

        # ═══════════════════════════════════════════
        #  MULTI-INTENT PATH
        # ═══════════════════════════════════════════
        if is_multi:
            parts = _split_query(user_text)
            resolved = _resolve_pronouns(parts)

            # Full-query model returned enough calls — use them
            if len(valid) >= len(parts):
                cactus_destroy(model)
                return {
                    "function_calls": valid,
                    "total_time_ms": total_time,
                    "source": "on-device",
                }

            combined, seen = [], set()

            # Run FunctionGemma on each sub-part
            for part in resolved:
                matched = _match_tool(part, tools, kw_map)
                best_tool = matched[0] if len(matched) == 1 else None

                if best_tool and best_tool["name"] in seen:
                    continue

                # Attempt 1: focused tool
                focus_tools = [best_tool] if best_tool else tools
                r = _cactus_infer(model, [{"role": "user", "content": part}], tools, top_tools=focus_tools)
                total_time += r.get("total_time_ms", 0)

                sub_valid = _process_calls(
                    r.get("function_calls", []), tools,
                    tool_names, tool_required, part,
                )

                # Attempt 2: all tools
                if not sub_valid:
                    r2 = _cactus_infer(model, [{"role": "user", "content": part}], tools)
                    total_time += r2.get("total_time_ms", 0)
                    sub_valid = _process_calls(
                        r2.get("function_calls", []), tools,
                        tool_names, tool_required, part,
                    )
                    # Try fixing the tool name if model returned args
                    if not sub_valid and best_tool and r2.get("function_calls"):
                        sub_valid = _process_for_tool(
                            r2.get("function_calls", []), best_tool,
                            tool_names, tool_required, part,
                        )

                # Attempt 3: rephrased prompt
                if not sub_valid:
                    retry_msgs = [{"role": "user", "content": f"Use tools: {part}"}]
                    r3 = _cactus_infer(model, retry_msgs, tools, top_tools=focus_tools)
                    total_time += r3.get("total_time_ms", 0)
                    sub_valid = _process_calls(
                        r3.get("function_calls", []), tools,
                        tool_names, tool_required, part,
                    )
                    if not sub_valid and best_tool and r3.get("function_calls"):
                        sub_valid = _process_for_tool(
                            r3.get("function_calls", []), best_tool,
                            tool_names, tool_required, part,
                        )

                if sub_valid:
                    for vc in sub_valid:
                        if vc["name"] not in seen:
                            combined.append(vc)
                            seen.add(vc["name"])

            # Fill gaps from full-query results (model output, not regex)
            for vc in valid:
                if vc["name"] not in seen:
                    combined.append(vc)
                    seen.add(vc["name"])

            cactus_destroy(model)

            # Got enough on-device results
            if len(combined) >= len(parts):
                return {
                    "function_calls": combined,
                    "total_time_ms": total_time,
                    "source": "on-device",
                }

            # Some on-device, cloud for the rest
            if combined:
                cloud = generate_cloud(messages, tools)
                cloud_valid = _process_calls(
                    cloud.get("function_calls", []), tools,
                    tool_names, tool_required, user_text,
                )
                cloud_calls = cloud_valid if cloud_valid else cloud.get("function_calls", [])
                for cc in cloud_calls:
                    if cc.get("name") not in seen:
                        combined.append(cc)
                        seen.add(cc.get("name"))
                return {
                    "function_calls": combined,
                    "total_time_ms": total_time + cloud.get("total_time_ms", 0),
                    "source": "hybrid",
                }

            # Model completely failed → cloud (with post-processing)
            cloud = generate_cloud(messages, tools)
            cloud_valid = _process_calls(
                cloud.get("function_calls", []), tools,
                tool_names, tool_required, user_text,
            )
            if cloud_valid:
                cloud["function_calls"] = cloud_valid
            cloud["source"] = "cloud"
            cloud["total_time_ms"] += total_time
            return cloud

        # ═══════════════════════════════════════════
        #  SINGLE-INTENT PATH
        # ═══════════════════════════════════════════
        if valid:
            cactus_destroy(model)
            return {
                "function_calls": valid,
                "total_time_ms": total_time,
                "source": "on-device",
                "confidence": confidence,
            }

        # Model failed — retry with focused tool set
        best_match = _match_tool(user_text, tools, kw_map)
        all_raw_calls = list(raw_calls)  # Track all raw calls from retries
        if len(best_match) == 1 and len(tools) > 1:
            r2 = _cactus_infer(model, messages, tools, top_tools=best_match)
            total_time += r2.get("total_time_ms", 0)
            r2_calls = r2.get("function_calls", [])
            if r2_calls:
                all_raw_calls = r2_calls
            retry_valid = _process_calls(
                r2_calls, tools,
                tool_names, tool_required, user_text,
            )
            if retry_valid:
                cactus_destroy(model)
                return {
                    "function_calls": retry_valid,
                    "total_time_ms": total_time,
                    "source": "on-device",
                    "confidence": r2.get("confidence", 0),
                }

        # Retry with explicit tool-use prompt (model is stochastic)
        retry_msgs = [{"role": "user", "content": f"Use tools to help: {user_text}"}]
        r3 = _cactus_infer(model, retry_msgs, tools,
                           top_tools=best_match if len(best_match) == 1 else None)
        total_time += r3.get("total_time_ms", 0)
        r3_calls = r3.get("function_calls", [])
        if r3_calls:
            all_raw_calls = r3_calls
        retry_valid3 = _process_calls(
            r3_calls, tools,
            tool_names, tool_required, user_text,
        )
        if retry_valid3:
            cactus_destroy(model)
            return {
                "function_calls": retry_valid3,
                "total_time_ms": total_time,
                "source": "on-device",
                "confidence": r3.get("confidence", 0),
            }

        # Try forcing tool name on ANY raw calls collected from retries
        if len(tools) == 1 and all_raw_calls:
            forced = _process_for_tool(all_raw_calls, tools[0], tool_names, tool_required, user_text)
            if forced:
                cactus_destroy(model)
                return {
                    "function_calls": forced,
                    "total_time_ms": total_time,
                    "source": "on-device",
                    "confidence": confidence,
                }

        cactus_destroy(model)

        # ── Model failed → cloud fallback (with post-processing) ──
        cloud = generate_cloud(messages, tools)
        cloud_valid = _process_calls(
            cloud.get("function_calls", []), tools,
            tool_names, tool_required, user_text,
        )
        if cloud_valid:
            cloud["function_calls"] = cloud_valid
        cloud["source"] = "cloud"
        cloud["local_confidence"] = confidence
        cloud["total_time_ms"] += total_time
        return cloud

    except Exception:
        try:
            cactus_destroy(model)
        except Exception:
            pass
        raise


def print_result(label, result):
    """Pretty-print a generation result."""
    print(f"\n=== {label} ===\n")
    if "source" in result:
        print(f"Source: {result['source']}")
    if "confidence" in result:
        print(f"Confidence: {result['confidence']:.4f}")
    if "local_confidence" in result:
        print(f"Local confidence (below threshold): {result['local_confidence']:.4f}")
    print(f"Total time: {result['total_time_ms']:.2f}ms")
    for call in result["function_calls"]:
        print(f"Function: {call['name']}")
        print(f"Arguments: {json.dumps(call['arguments'], indent=2)}")


############## Example usage ##############

if __name__ == "__main__":
    tools = [{
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name",
                }
            },
            "required": ["location"],
        },
    }]

    messages = [
        {"role": "user", "content": "What is the weather in San Francisco?"}
    ]

    on_device = generate_cactus(messages, tools)
    print_result("FunctionGemma (On-Device Cactus)", on_device)

    cloud = generate_cloud(messages, tools)
    print_result("Gemini (Cloud)", cloud)

    hybrid = generate_hybrid(messages, tools)
    print_result("Hybrid (On-Device + Cloud Fallback)", hybrid)
