# VetClaim AI

AI-powered VA disability claim auditor. Upload your decision letter, DBQ forms, and C&P exam — get back a full audit with identified rating errors, pre-filled VA appeal forms, and one-click portal submission.

![VetClaim AI demo flow](docs/demo.gif)

---

## What it does

1. **Upload** your VA documents (decision letter, DBQ, C&P exam)
2. **AI audit** runs against CFR Title 38 Part 4 — flags under-ratings, wrong codes, PACT Act eligibility, TDIU eligibility, and combined rating math errors
3. **Pre-filled VA forms** (20-0996, 20-0995, 21-526EZ, 21-8940) are generated and ready to download
4. **Submit** directly to the mock VA portal with one click
5. **Call the VA** — AI agent calls your phone, reads a consent disclosure, then requests a claim status update on your behalf

---

## Stack

- **Backend** — Python 3.13, Flask, Google ADK (Gemini 2.0 Flash)
- **Frontend** — React 18, Vite
- **Mock VA Portal** — Flask
- **Calling Agent** — Vapi

---

## Setup

### 1. Prerequisites

- Python 3.13+
- Node.js 18+
- A `GOOGLE_API_KEY` from [Google AI Studio](https://aistudio.google.com)

### 2. Clone and configure

```bash
git clone https://github.com/mtbadri/vetclaim.git
cd vetclaim
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY at minimum
```

### 3. Install dependencies

```bash
# Python (from repo root)
pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

### 4. Run

Open three terminals:

```bash
# Terminal 1 — Backend API (port 5001)
python backend/server.py

# Terminal 2 — Frontend (port 5173)
cd frontend && npm run dev

# Terminal 3 — Mock VA Portal (port 5050)
python mock_va_portal/server.py
```

Then open [http://localhost:5173](http://localhost:5173).

---

## Optional: VA Calling Agent

To enable the calling feature, add to `.env`:

```
VAPI_API_KEY=your_vapi_key
VAPI_PHONE_NUMBER_ID=your_phone_number_id
```

Get keys at [vapi.ai](https://vapi.ai).

---

## Running tests

```bash
# Backend
pytest backend/

# Mock portal JS tests
cd mock_va_portal && npx vitest --run
```

---

## Project structure

```
backend/
  server.py          # Flask API — upload, SSE stream, audit results, Vapi calling
  agents/
    auditor_agent.py # Gemini LlmAgent with 8 CFR/PACT/TDIU tools
    parser_agent.py  # PDF text extraction
    filer_agent.py   # VA form download and AcroForm fill
  tools/             # CFR lookup, combined rating, PACT Act, TDIU, VA pay
  data/              # CFR38 Part 4, PACT Act conditions, VA pay rates 2026

frontend/src/
  App.jsx                        # Page routing
  components/LandingPage.jsx     # Hero + feature overview
  components/UploadPage.jsx      # Drag-and-drop PDF upload
  components/TrackerPage.jsx     # Live SSE pipeline progress
  components/AuditResultsPage.jsx # Findings, forms, portal submission
  components/CallingAgentPage.jsx # VA calling agent UI

mock_va_portal/
  server.py      # Flask — receives appeal PDFs, stores submissions
  index.html     # Veteran dashboard
  confirmation.html # Submission confirmation
```

---

## Disclaimer

VetClaim AI is a document preparation tool built for a hackathon. It does not provide legal or medical advice. Always work with an accredited VSO, attorney, or claims agent for official VA claims.
