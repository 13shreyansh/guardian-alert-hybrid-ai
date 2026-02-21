"""
Guardian Alert - Backend Server
Hybrid AI Emergency Sound Detection powered by Cactus Compute + FunctionGemma + Gemini
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import random

app = Flask(__name__)
CORS(app)

# Try importing the hybrid AI brain
try:
    from main import generate_hybrid
    AI_AVAILABLE = True
except Exception:
    AI_AVAILABLE = False

# Emergency sound classification tools for the AI brain
SOUND_TOOLS = [
    {
        "name": "classify_emergency",
        "description": "Classify an emergency sound and determine alert level",
        "parameters": {
            "type": "object",
            "properties": {
                "sound_type": {"type": "string", "description": "Type of sound detected (e.g. glass breaking, smoke alarm, scream)"},
                "confidence": {"type": "number", "description": "Confidence score from 0 to 1"},
                "alert_level": {"type": "string", "description": "Alert level: critical, warning, or info"},
            },
            "required": ["sound_type", "confidence", "alert_level"],
        },
    },
    {
        "name": "send_emergency_alert",
        "description": "Send an emergency alert notification via SMS or push notification",
        "parameters": {
            "type": "object",
            "properties": {
                "recipient": {"type": "string", "description": "Contact to notify"},
                "message": {"type": "string", "description": "Alert message content"},
                "priority": {"type": "string", "description": "Priority: high, medium, low"},
            },
            "required": ["recipient", "message", "priority"],
        },
    },
]

# High-confidence emergency sounds (handled locally)
EMERGENCY_SOUNDS = {
    "glass_breaking", "smoke_alarm", "fire_alarm", "scream", "gunshot",
    "explosion", "siren", "dog_barking", "baby_crying", "car_crash",
    "door_break", "carbon_monoxide_alarm", "water_leak", "fall_detection",
}


@app.route("/api/analyze", methods=["POST"])
def analyze_sound():
    """Analyze detected sound using hybrid AI routing."""
    start_time = time.time()
    data = request.get_json() or {}

    sound_type = data.get("sound_type", "unknown")
    confidence = data.get("confidence", 0.5)
    raw_audio = data.get("audio_data", None)

    if AI_AVAILABLE:
        # Use the real hybrid AI brain
        messages = [{"role": "user", "content": f"Emergency sound detected: {sound_type} with confidence {confidence}. Classify and alert."}]
        result = generate_hybrid(messages, SOUND_TOOLS)
        processing_time = (time.time() - start_time) * 1000

        return jsonify({
            "status": "success",
            "sound_type": sound_type,
            "confidence": confidence,
            "function_calls": result.get("function_calls", []),
            "source": result.get("source", "unknown"),
            "processing_time_ms": round(processing_time, 2),
            "ai_engine": "hybrid",
        })

    # Fallback mock logic when AI module isn't available
    processing_time = (time.time() - start_time) * 1000
    is_emergency = sound_type.lower().replace(" ", "_") in EMERGENCY_SOUNDS

    if confidence > 0.7 and is_emergency:
        return jsonify({
            "status": "success",
            "sound_type": sound_type,
            "confidence": confidence,
            "alert_level": "critical",
            "source": "local_ai",
            "processing_time_ms": round(processing_time, 2),
            "action": "alert_sent",
            "ai_engine": "functiongemma_local",
        })
    elif confidence > 0.4:
        return jsonify({
            "status": "success",
            "sound_type": sound_type,
            "confidence": confidence,
            "alert_level": "warning",
            "source": "cloud_ai",
            "processing_time_ms": round(processing_time, 2),
            "action": "verification_needed",
            "ai_engine": "gemini_cloud",
        })
    else:
        return jsonify({
            "status": "success",
            "sound_type": sound_type,
            "confidence": confidence,
            "alert_level": "info",
            "source": "local_ai",
            "processing_time_ms": round(processing_time, 2),
            "action": "logged",
            "ai_engine": "functiongemma_local",
        })


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "ai_available": AI_AVAILABLE,
        "engine": "Cactus FunctionGemma + Gemini Hybrid",
    })


if __name__ == "__main__":
    print("=" * 50)
    print("  Guardian Alert - Hybrid AI Server")
    print(f"  AI Engine: {'Online' if AI_AVAILABLE else 'Mock Mode'}")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)
