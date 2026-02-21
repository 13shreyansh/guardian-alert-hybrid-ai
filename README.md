# 🛡️ Guardian Alert

**Real-time emergency sound detection for vulnerable individuals, powered by on-device AI.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT) [![Hackathon](https://img.shields.io/badge/Hackathon-Google%20DeepMind%20×%20Cactus%20Compute-brightgreen)]() [![On-Device Ratio](https://img.shields.io/badge/On--Device%20Ratio-100%25-blue)]() [![Benchmark Score](https://img.shields.io/badge/Benchmark-82%25-orange)]()

---

## 📺 Demo Video

**Watch our 2-minute pitch and live demonstration:**

[![Guardian Alert Demo](https://img.shields.io/badge/▶%20Watch%20Demo-YouTube-red?style=for-the-badge&logo=youtube)](https://www.youtube.com/playlist?list=PLRjIbTD2eeN5t_PZH_3GQrsMUdV6jLJw4)

---

## 🎯 The Problem

> People with disabilities are **2–4x more likely to die** in emergencies. — *United Nations Office for Disaster Risk Reduction*

**1.3 billion people** worldwide live with a disability. Fire alarms, sirens, and emergency announcements are built for people who can hear, see, and move freely. For everyone else, these life-saving systems are silent.

Guardian Alert was born from a real story. My teammate Krishiv's grandmother lives alone. She's hard of hearing. A fire alarm went off in her building — she didn't hear it. A neighbor found her just in time. **Not everyone is that lucky.**

## 💡 The Solution

Guardian Alert turns **any smartphone** into an always-on, AI-powered safety guardian. It listens for dangerous sounds and instantly alerts users and caregivers through personalized, multi-modal notifications.

### Why Cactus Compute + FunctionGemma?

For someone who is deaf and alone in a burning building, a 15-second cloud API response is not fast enough.

| | On-Device (Cactus) | Cloud AI |
|---|---|---|
| **Latency** | <50ms ⚡ | 15,000ms+ 🐌 |
| **Privacy** | Audio never leaves device 🔒 | Audio sent to servers |
| **Offline** | Works without internet ✅ | Requires connectivity ❌ |
| **Cost** | Free inference | API costs per call |

We use **Cactus Compute** to run Google's **FunctionGemma-270M-IT** model directly on the device. Sub-50ms decisions. Complete privacy. Works offline.

---

## 🏗️ Architecture
