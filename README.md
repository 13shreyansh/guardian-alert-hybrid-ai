# 🛡️ Guardian Alert — Hybrid AI Emergency Detection

**Powered by Cactus Compute + Google FunctionGemma + Gemini**

> Real-time emergency sound detection for elderly and disabled individuals, using on-device AI for instant response with cloud fallback for complex scenarios.

---

## 🎯 What is Guardian Alert?

Guardian Alert is an **accessibility-first emergency detection system** that listens for dangerous sounds — glass breaking, smoke alarms, screams, falls — and instantly alerts caregivers via SMS, screen flash, and voice alerts.

**Why it matters:** For elderly individuals living alone or people with hearing impairments, a smoke alarm going off could be life-threatening if undetected. Guardian Alert acts as an always-on AI guardian that processes sounds **locally in under 50ms** — no internet required for 90%+ of cases.

**Key Innovation:** Our **hybrid AI routing** ensures:
- 🟢 **On-device (FunctionGemma):** Handles common emergency sounds instantly (~40ms) with zero latency and full privacy
- 🔵 **Cloud fallback (Gemini):** Only activated for ambiguous or complex sound patterns
- 🔒 **Privacy-first:** Audio never leaves the device unless absolutely necessary

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Guardian Alert System                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   🎤 Microphone Input                                        │
│        │                                                      │
│        ▼                                                      │
│   ┌─────────────┐                                            │
│   │   YAMNet     │  Sound Classification                     │
│   │  (TF Lite)   │  "smoke_alarm" → 0.94 confidence          │
│   └──────┬──────┘                                            │
│          │                                                    │
│          ▼                                                    │
│   ┌─────────────────────────────────────────┐                │
│   │      🧠 Hybrid AI Brain (main.py)       │                │
│   │                                          │                │
│   │   ┌───────────────┐  ┌───────────────┐  │                │
│   │   │ FunctionGemma │  │  Gemini Cloud  │  │                │
│   │   │   270M-IT     │  │   2.0 Flash    │  │                │
│   │   │  (On-Device)  │  │  (Fallback)    │  │                │
│   │   │   ~40ms ⚡     │  │   ~500ms 🌐    │  │                │
│   │   └───────┬───────┘  └───────┬───────┘  │                │
│   │           │    Hybrid Router  │          │                │
│   │           └────────┬─────────┘          │                │
│   └────────────────────┼────────────────────┘                │
│                        │                                      │
│                        ▼                                      │
│   ┌─────────────────────────────────────────┐                │
│   │           📱 Alert Actions              │                │
│   │                                          │                │
│   │   📲 Twilio SMS    💡 Screen Flash       │                │
│   │   🔊 Voice Alert   📋 Event Logging      │                │
│   └─────────────────────────────────────────┘                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧠 How the Hybrid Routing Works

Our `generate_hybrid()` function implements intelligent routing between on-device and cloud AI:

1. **FunctionGemma First** — Every query runs through the on-device FunctionGemma-270M-IT model via Cactus Compute
2. **JSON Repair** — If the model produces valid tool selection but broken JSON, we salvage the tool name and rebuild
3. **Smart Retries** — Focused tool presentation + rephrased prompts to maximize on-device success
4. **Post-Processing** — Type fixing, argument extraction, and validation ensure correct function calls
5. **Cloud Fallback** — Only when the on-device model genuinely cannot handle the query

**Result:** 100% on-device ratio on the hackathon evaluation with 91.1% F1 accuracy.

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **On-Device AI** | [Cactus Compute](https://cactuscompute.com) | Local ML inference engine |
| **Local Model** | FunctionGemma-270M-IT | On-device function calling (40ms) |
| **Cloud Model** | Gemini 2.0 Flash | Fallback for complex queries |
| **Sound Detection** | YAMNet (TensorFlow Lite) | Audio event classification |
| **Frontend** | React + Vite + Tailwind CSS | Real-time monitoring dashboard |
| **Backend** | Flask + Flask-CORS | REST API server |
| **Alerts** | Twilio SMS API | Emergency SMS notifications |
| **Language** | Python 3.13 | Backend & AI logic |

---

## 🚀 How to Run

### Backend (AI Server)

```bash
# Install dependencies
pip install -r requirements.txt

# Set your Gemini API key (for cloud fallback)
export GEMINI_API_KEY="your-api-key"

# Start the server
python server.py
```

### Frontend (React App)

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173` with the API server at `http://localhost:5000`.

---

## 📊 Hackathon Results

| Metric | Score |
|--------|-------|
| **Total Score** | 82.0% |
| **F1 Accuracy** | 0.9111 |
| **Avg Response Time** | 827ms |
| **On-Device Ratio** | 100% |

---

## 👥 Team

| Name | Role |
|------|------|
| **Shreyansh Agarwal** | Lead — Hybrid AI Architecture, On-device Optimization |
| **Krishiv Kapur** | App Development, Frontend & UX |

---

## 🏆 Built At

**Google DeepMind × Cactus Compute Global Hackathon**
📍 Singapore | 📅 February 21, 2026

---

## 📄 License

MIT License — Built with ❤️ for accessibility
