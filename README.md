<p align="center">
  <img src="https://img.shields.io/badge/🛡️_Guardian_Alert-On--Device_AI_Emergency_Detection-1e3a5f?style=for-the-badge&labelColor=0d1117" alt="Guardian Alert" />
</p>

<h1 align="center">🛡️ Guardian Alert</h1>

<p align="center">
  <strong>Real-time emergency sound detection for vulnerable individuals, powered by on-device AI.</strong>
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT" /></a>
  <img src="https://img.shields.io/badge/Hackathon-Google%20DeepMind%20×%20Cactus%20Compute-brightgreen" alt="Hackathon" />
  <img src="https://img.shields.io/badge/Benchmark-82%25-orange" alt="Benchmark Score" />
  <img src="https://img.shields.io/badge/On--Device%20Ratio-100%25-blue" alt="On-Device Ratio" />
  <img src="https://img.shields.io/badge/F1%20Score-0.911-success" alt="F1 Score" />
</p>

---

## 📺 Demo Video

<p align="center">
  <a href="https://www.youtube.com/playlist?list=PLRjIbTD2eeN5t_PZH_3GQrsMUdV6jLJw4">
    <img src="https://img.shields.io/badge/▶_Watch_Our_Demo-YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="Watch Demo on YouTube" />
  </a>
</p>

<p align="center"><em>Watch our YouTube video here — live demonstration of Guardian Alert detecting fire alarms and alerting caregivers in real time.</em></p>

---

## 🎯 The Problem

> People with disabilities are **2–4× more likely to die** in emergencies.
>
> — *United Nations Office for Disaster Risk Reduction*

**1.3 billion people** worldwide live with a disability. Fire alarms, sirens, and emergency announcements are designed for people who can hear, see, and move freely. For everyone else, these life-saving systems are **silent**.

**This is personal.** My teammate Krishiv's grandmother lives alone. She's hard of hearing. A fire alarm went off in her building — she didn't hear it. A neighbor found her just in time.

**Not everyone is that lucky.**

---

## 💡 The Solution

Guardian Alert transforms **any smartphone** into an always-on, AI-powered safety guardian. It listens for dangerous sounds and instantly delivers personalized, multi-modal alerts to users and their caregivers.

### Why On-Device AI?

For someone who is deaf and alone in a burning building, a 15-second cloud API round-trip is **not fast enough**.

| | On-Device (Cactus Compute) | Cloud AI |
|:---|:---|:---|
| **Latency** | **<50ms** ⚡ | 15,000ms+ 🐌 |
| **Privacy** | Audio never leaves device 🔒 | Audio sent to servers |
| **Offline** | Works without internet ✅ | Requires connectivity ❌ |
| **Cost** | Free inference | API costs per call |

We run Google's **FunctionGemma-270M-IT** directly on-device via **Cactus Compute**. Sub-50ms decisions. Complete privacy. Works offline. **Lives saved.**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        📱 Guardian Alert App                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   🎤 Microphone (24/7 Listening)                                    │
│         │                                                           │
│         ▼                                                           │
│   ┌─────────────────────────┐                                       │
│   │  YAMNet Sound Classifier │  ← TensorFlow Lite (521 classes)    │
│   │  (On-Device, ~10ms)      │                                      │
│   └────────────┬────────────┘                                       │
│                │                                                    │
│                ▼                                                    │
│   ┌─────────────────────────────────────────────────┐               │
│   │         🧠 Hybrid AI Brain (Agentic)            │               │
│   │                                                  │               │
│   │   ┌──────────────────┐    ┌──────────────────┐  │               │
│   │   │  FunctionGemma   │    │  Gemini 2.0      │  │               │
│   │   │  270M-IT         │───▶│  Flash           │  │               │
│   │   │  (Cactus Compute)│    │  (Cloud Fallback)│  │               │
│   │   │  ~40ms ⚡        │    │  ~800ms          │  │               │
│   │   └──────────────────┘    └──────────────────┘  │               │
│   │              │                                   │               │
│   │              ▼                                   │               │
│   │   ┌──────────────────────────────────────┐      │               │
│   │   │  Agentic Function Calls:             │      │               │
│   │   │  • classify_emergency_sound()        │      │               │
│   │   │  • send_emergency_alert()            │      │               │
│   │   │  • notify_caregiver()                │      │               │
│   │   └──────────────────────────────────────┘      │               │
│   └─────────────────────────────────────────────────┘               │
│                │                                                    │
│                ▼                                                    │
│   ┌─────────────────────────────────────────────────┐               │
│   │         📢 Personalized Alert System            │               │
│   │                                                  │               │
│   │   👁️  Visual  │ 🔊 Audio │ 📳 Haptic │ 💡 Flash │               │
│   │   (Deaf)      │ (Blind) │ (DeafBlind)│ (Low    │               │
│   │               │         │            │  Vision)│               │
│   └─────────────────────────────────────────────────┘               │
│                │                                                    │
│                ▼                                                    │
│   ┌──────────────────────┐                                          │
│   │  📱 SMS + GPS Alert   │  → Emergency contacts get location      │
│   │  (Twilio API)         │                                         │
│   └──────────────────────┘                                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ How the Hybrid Routing Works

Our hybrid AI architecture maximizes on-device processing while maintaining accuracy:

```
Query → FunctionGemma (on-device, ~40ms)
           │
           ├─ ✅ Valid JSON response → Post-process & return
           │
           ├─ ⚠️ Broken JSON but correct tool → JSON Repair → Return
           │
           ├─ 🔄 Wrong tool → Retry with focused tool list → Return
           │
           ├─ 🔄 Still failing → Retry with rephrased prompt → Return
           │
           └─ ❌ All retries exhausted → Gemini Cloud Fallback → Return
```

1. **FunctionGemma First** — Every query hits the on-device model via Cactus Compute
2. **JSON Repair** — Malformed model output? We salvage the tool selection and rebuild valid JSON
3. **Smart Retries** — Focused tool presentation + rephrased prompts maximize local success
4. **Post-Processing** — Type coercion, argument extraction, and schema validation
5. **Cloud Fallback** — Gemini 2.0 Flash, only when the local model genuinely cannot handle it

**Result:** **100% on-device ratio** on the hackathon benchmark. The cloud fallback exists but was never needed.

---

## 📊 Benchmark Results

<table>
  <tr><td>🏆 <strong>Total Score</strong></td><td><strong>82.0%</strong></td></tr>
  <tr><td>🎯 <strong>F1 Accuracy</strong></td><td><strong>0.911</strong></td></tr>
  <tr><td>⚡ <strong>Avg Response Time</strong></td><td>827ms</td></tr>
  <tr><td>💻 <strong>On-Device Ratio</strong></td><td><strong>100%</strong></td></tr>
</table>

> Scoring formula: `60% × F1 + 15% × time_score + 25% × on_device_ratio`

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|:---|:---|:---|
| **On-Device Engine** | [Cactus Compute](https://cactuscompute.com) | Local ML inference runtime |
| **Local Model** | FunctionGemma-270M-IT | On-device function calling (~40ms) |
| **Cloud Model** | Gemini 2.0 Flash | Fallback for complex/ambiguous queries |
| **Sound Detection** | YAMNet (TensorFlow Lite) | 521-class audio event classification |
| **Frontend** | React + Vite + Tailwind CSS | Real-time monitoring dashboard |
| **Backend** | Flask + Flask-CORS | Hybrid AI REST API server |
| **Alerts** | Twilio SMS API | Emergency SMS with GPS coordinates |

---

## 🚀 How to Run

### Prerequisites

- Python 3.10+
- Node.js 18+
- [Cactus Compute](https://github.com/nicholasgasior/cactus) engine installed separately (provides on-device FunctionGemma inference)
- FunctionGemma-270M-IT model weights (downloaded via Cactus CLI)
- Gemini API key (for cloud fallback only)

> **Note:** If Cactus Compute is not installed, the server automatically runs in fallback mode with simulated AI responses. The full hybrid AI pipeline requires the Cactus engine to be installed separately.

### Backend (AI Server)

```bash
cd guardian-alert-submission
pip install -r requirements.txt
export GEMINI_API_KEY="your-api-key"
python server.py
# → Server running on http://localhost:5050
```

### Frontend (React App)

```bash
cd frontend
npm install
npm run dev -- --host
# → App running on http://localhost:8080
# → Network: http://<your-ip>:8080 (accessible from phone)
```

### Test the API

```bash
curl -X POST http://localhost:5050/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"sound_description":"fire alarm beeping loudly","volume_level":"high","confidence":0.95}'
```

---

## 👥 Team

<table>
  <tr>
    <td align="center"><strong>Shreyansh Agarwal</strong><br/>Hybrid AI Architecture<br/><em>On-device/cloud routing, JSON repair,<br/>FunctionGemma optimization, benchmark tuning</em></td>
    <td align="center"><strong>Krishiv Kapur</strong><br/>App Development & UX<br/><em>React frontend, accessibility features,<br/>YAMNet integration, alert system</em></td>
  </tr>
</table>

<p align="center"><strong>Team Name:</strong> The CS Guys</p>

---

<p align="center">
  <strong>Built for the Google DeepMind × Cactus Compute Global Hackathon 2026</strong><br/>
  <em>Because in an emergency, everyone deserves to be alerted.</em>
</p>
