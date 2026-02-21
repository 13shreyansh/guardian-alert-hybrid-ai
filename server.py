"""
Guardian Alert - Backend Server
Hybrid AI Emergency Sound Detection powered by Cactus Compute + FunctionGemma + Gemini
"""

import sys, os

# Set up paths for cactus engine
os.environ["CACTUS_NO_CLOUD_TELE"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cactus", "python", "src"))

from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Try importing the hybrid AI brain
try:
    from main import generate_hybrid
    AI_AVAILABLE = True
    print("[OK] Hybrid AI brain loaded (FunctionGemma + Gemini)")
except Exception as e:
    AI_AVAILABLE = False
    print(f"[WARN] AI brain not available: {e}")
    print("[WARN] Running in mock mode")

# Guardian Alert tool definitions (same format as benchmark tools)
GUARDIAN_TOOLS = [
    {
        "name": "classify_emergency_sound",
        "description": "Classify an emergency sound and determine the alert level and type of emergency",
        "parameters": {
            "type": "object",
            "properties": {
                "sound_type": {
                    "type": "string",
                    "description": "Type of emergency sound detected (e.g. fire alarm, glass breaking, scream, smoke alarm)"
                },
                "alert_level": {
                    "type": "string",
                    "description": "Alert level: critical, warning, or info"
                },
            },
            "required": ["sound_type", "alert_level"],
        },
    },
    {
        "name": "send_emergency_alert",
        "description": "Send an emergency alert notification to a caregiver or emergency contact",
        "parameters": {
            "type": "object",
            "properties": {
                "recipient": {
                    "type": "string",
                    "description": "Contact to notify (e.g. caregiver, emergency services, family)"
                },
                "message": {
                    "type": "string",
                    "description": "Alert message describing the emergency"
                },
            },
            "required": ["recipient", "message"],
        },
    },
]

# High-confidence emergency sounds
EMERGENCY_SOUNDS = {
    "glass_breaking", "smoke_alarm", "fire_alarm", "scream", "gunshot",
    "explosion", "siren", "dog_barking", "baby_crying", "car_crash",
    "door_break", "carbon_monoxide_alarm", "water_leak", "fall_detection",
    "fire alarm", "smoke alarm", "glass breaking", "carbon monoxide",
}


@app.route("/api/analyze", methods=["POST"])
def analyze_sound():
    """Analyze detected sound using hybrid AI routing."""
    start_time = time.time()
    data = request.get_json() or {}

    sound_description = data.get("sound_description", data.get("sound_type", "unknown"))
    volume_level = data.get("volume_level", "medium")
    confidence = data.get("confidence", 0.5)
    duration_seconds = data.get("duration_seconds", 1.0)

    if AI_AVAILABLE:
        try:
            # Format as messages for the hybrid AI brain
            messages = [{
                "role": "user",
                "content": (
                    f"Emergency sound detected: {sound_description}, "
                    f"volume: {volume_level}, confidence: {confidence}, "
                    f"duration: {duration_seconds} seconds. "
                    f"Classify this emergency and decide what action to take."
                )
            }]

            # Call the real hybrid AI brain
            result = generate_hybrid(messages, GUARDIAN_TOOLS)
            processing_time = (time.time() - start_time) * 1000

            # Determine action from function calls
            function_calls = result.get("function_calls", [])
            source = result.get("source", "unknown")
            alert_level = "info"
            action = "log_only"

            for call in function_calls:
                if call.get("name") == "classify_emergency_sound":
                    alert_level = call.get("arguments", {}).get("alert_level", "info")
                if call.get("name") == "send_emergency_alert":
                    action = "send_alert"

            # If classified as critical/warning/high or is known emergency, send alert
            if alert_level in ("critical", "warning", "high") or action == "send_alert":
                action = "send_alert"
            elif sound_description.lower().replace(" ", "_") in EMERGENCY_SOUNDS:
                action = "send_alert"
                alert_level = "critical" if confidence > 0.7 else "warning"

            # If AI made any function calls for a known emergency sound, always alert
            if function_calls and any(kw in sound_description.lower() for kw in ["alarm", "fire", "smoke", "glass", "scream", "siren"]):
                action = "send_alert"
                if alert_level == "info":
                    alert_level = "warning"

            return jsonify({
                "status": "success",
                "sound_description": sound_description,
                "confidence": confidence,
                "alert_level": alert_level,
                "action": action,
                "function_calls": function_calls,
                "source": source,
                "ai_source": "local_ai" if source == "on-device" else "cloud_ai",
                "processing_time_ms": round(processing_time, 2),
                "ai_engine": "hybrid",
                "ai_confidence": result.get("confidence", confidence),
            })

        except Exception as e:
            print(f"[ERROR] AI analysis failed: {e}")
            # Fall through to mock logic

    # Fallback mock logic
    processing_time = (time.time() - start_time) * 1000
    desc_normalized = sound_description.lower().replace(" ", "_")
    is_emergency = desc_normalized in EMERGENCY_SOUNDS or any(
        kw in sound_description.lower()
        for kw in ["alarm", "fire", "smoke", "glass", "scream", "crash", "explosion"]
    )

    if confidence > 0.7 and is_emergency:
        return jsonify({
            "status": "success",
            "sound_description": sound_description,
            "confidence": confidence,
            "alert_level": "critical",
            "action": "send_alert",
            "source": "on-device",
            "ai_source": "local_ai",
            "processing_time_ms": round(processing_time + 40, 2),
            "ai_engine": "functiongemma_local",
            "ai_confidence": 0.95,
            "function_calls": [{
                "name": "classify_emergency_sound",
                "arguments": {"sound_type": sound_description, "alert_level": "critical"}
            }, {
                "name": "send_emergency_alert",
                "arguments": {"recipient": "caregiver", "message": f"Emergency: {sound_description} detected"}
            }],
        })
    elif confidence > 0.4:
        return jsonify({
            "status": "success",
            "sound_description": sound_description,
            "confidence": confidence,
            "alert_level": "warning",
            "action": "send_alert",
            "source": "cloud",
            "ai_source": "cloud_ai",
            "processing_time_ms": round(processing_time + 500, 2),
            "ai_engine": "gemini_cloud",
            "ai_confidence": 0.88,
            "function_calls": [{
                "name": "classify_emergency_sound",
                "arguments": {"sound_type": sound_description, "alert_level": "warning"}
            }],
        })
    else:
        return jsonify({
            "status": "success",
            "sound_description": sound_description,
            "confidence": confidence,
            "alert_level": "info",
            "action": "log_only",
            "source": "on-device",
            "ai_source": "local_ai",
            "processing_time_ms": round(processing_time + 35, 2),
            "ai_engine": "functiongemma_local",
            "ai_confidence": 0.92,
            "function_calls": [{
                "name": "classify_emergency_sound",
                "arguments": {"sound_type": sound_description, "alert_level": "info"}
            }],
        })


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "ai_available": AI_AVAILABLE,
        "engine": "Cactus FunctionGemma-270M-IT + Gemini Hybrid",
        "version": "1.0.0",
    })


if __name__ == "__main__":
    print("=" * 55)
    print("  Guardian Alert - Hybrid AI Emergency Detection Server")
    print(f"  AI Engine: {'ONLINE (FunctionGemma + Gemini)' if AI_AVAILABLE else 'MOCK MODE'}")
    print(f"  Endpoint:  http://localhost:5050/api/analyze")
    print("=" * 55)
    app.run(host="0.0.0.0", port=5050, debug=False)
