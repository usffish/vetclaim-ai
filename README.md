# VetClaim AI

**An AI-powered VA disability claims assistant that helps veterans identify missed compensation, navigate appeals, and submit the right forms — automatically.**

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB)
![Google ADK](https://img.shields.io/badge/Google_ADK-FF6F00?style=flat-square&logo=google&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-412991?style=flat-square&logo=google&logoColor=white)
![Vapi](https://img.shields.io/badge/Vapi.ai-FF6F00?style=flat-square&logoColor=white)

> Built at HackUSF 2026. Designed for real impact.

---

## The Problem

The VA disability claims process is notoriously complex. Veterans are routinely under-rated, assigned wrong diagnostic codes, or miss out on benefits they're legally entitled to under laws like the PACT Act. The difference between a 70% and 100% rating can be over $2,000/month — for life. Most veterans don't have the legal or medical expertise to catch these errors on their own.

## What VetClaim AI Does

A veteran uploads their VA documents (rating decision, C&P exam, DBQ, personal statement). The app:

1. **Parses** the documents and extracts structured claim data
2. **Audits** every condition against CFR Title 38 Part 4 regulations using an AI agent with specialized tools
3. **Flags** under-ratings, wrong diagnostic codes, PACT Act eligibility, TDIU eligibility, and combined rating math errors
4. **Calculates** the exact monthly and annual dollar impact of each finding
5. **Pre-fills** the correct VA appeal forms (20-0996, 20-0995, 21-526EZ, 21-8940) with the veteran's data
6. **Submits** forms to the VA portal and tracks the claim
7. **Calls the VA** on the veteran's behalf using an AI voice agent via Vapi

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
│  Landing → Upload → Tracker → Results / Calling Agent          │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP / SSE
┌────────────────────────▼────────────────────────────────────────┐
│                    Backend API (Flask, port 5001)               │
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ Parser Agent│  │ Auditor Agent│  │     Filer Agent        │ │
│  │ (pdfplumber)│  │ (Google ADK) │  │ (pypdf + AcroForm)     │ │
│  └─────────────┘  └──────┬───────┘  └────────────────────────┘ │
│                          │ Tool calls                           │
│  ┌───────────────────────▼──────────────────────────────────┐  │
│  │  CFR Lookup │ PACT Act Check │ TDIU Check │ Pay Lookup   │  │
│  │  Combined Rating │ CFR Compare │ Pay Impact Calculator   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                         │ REST
┌────────────────────────▼────────────────────────────────────────┐
│                    Vapi.ai (outbound calls)                     │
│  Backend → Vapi API → AI phone call to VA on veteran's behalf   │
└─────────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│              Mock VA Portal (Flask, port 5050)                  │
│              Simulates VA eBenefits for testing                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite 5, Tailwind CSS |
| Backend | Python, Flask, Google ADK |
| AI / LLM | Google Gemini 2.5 Flash |
| Phone Calls | Vapi.ai (outbound AI calls to VA) |
| PDF Processing | pdfplumber (extraction), pypdf (form filling) |
| Data Validation | Pydantic v2 |
| Testing | pytest (backend), vitest (frontend/portal) |

---

## Key Features

### AI Auditor Agent
Built on **Google ADK** (LlmAgent), the auditor receives raw text from parsed VA documents and calls a suite of specialized tools to audit every condition:

- **CFR Lookup** — retrieves rating criteria at every percentage level for a diagnostic code
- **CFR Compare Rating** — compares the VA's assigned rating against CFR thresholds to detect under-ratings
- **PACT Act Check** — determines if a condition qualifies as a presumptive (no nexus letter required) based on deployment locations and service era
- **TDIU Check** — evaluates eligibility for Total Disability Individual Unemployability under 38 CFR §4.16, which pays at the 100% rate
- **Combined Rating Calculator** — verifies the VA's combined rating using whole-person math (1 - ((1-r1) × (1-r2) × ... × (1-rN))) and flags arithmetic errors
- **VA Pay Lookup** — retrieves 2026 monthly pay rates by rating and dependent status
- **Pay Impact Calculator** — quantifies the monthly and annual dollar value of each finding

The agent outputs structured AuditFlag objects with flag type, CFR citation, confidence score, and dollar impact.

### Flag Types

| Flag | Meaning |
|---|---|
| UNDER_RATED | Assigned rating is lower than symptoms warrant per CFR criteria |
| WRONG_CODE | Condition mapped to incorrect diagnostic code |
| MISSING_NEXUS | Service connection not established; nexus letter needed |
| PACT_ACT_ELIGIBLE | Condition qualifies as presumptive — no nexus required by law |
| TDIU_ELIGIBLE | Veteran qualifies for 100% pay rate due to unemployability |
| COMBINED_RATING_ERROR | VA's combined rating math is incorrect |
| SEPARATE_RATING_MISSED | Condition should be rated separately but was not |

### Hybrid Audit (LLM + Rule-Based)
The LLM agent runs alongside a deterministic rule-based auditor. For example: if a DBQ contains gait keywords ("staggering", "unsteady") but the decision letter assigns 0% for a related condition, the rule-based auditor flags it for vestibular dysfunction (DC 6204) with high confidence. Both results are merged.

### Intelligent Form Filling
VA forms use XFA (XML Forms Architecture), which only renders in Adobe Reader. The filer agent:
1. Strips the XFA layer so the form falls back to AcroForm (works in Preview, Chrome, Firefox)
2. Maps veteran data to exact AcroForm field paths (e.g., form1[0].#subform[2].Veterans_First_Name[0])
3. Patches appearance streams to fix a pypdf rendering bug
4. Automatically selects the right form(s) based on flag types

### Real-Time Pipeline Tracking
The frontend streams pipeline progress via **Server-Sent Events (SSE)** — parsing → auditing → form filling — with live status updates and no polling.

### AI Calling Agent
The Calling Agent page lets veterans initiate an outbound AI phone call to the VA. The veteran enters their phone number, name, last four SSN digits, claim date, and claim type. The backend calls the **Vapi.ai API**, which places a real phone call using a Gemini-powered voice assistant that reads a consent disclosure and requests a claim status update on the veteran's behalf. Call records can be retrieved by call ID.

---

## Project Structure

```
vetclaim/
├── backend/
│   ├── agents/
│   │   ├── auditor_agent.py     # Google ADK LlmAgent — core audit logic
│   │   ├── filer_agent.py       # PDF form downloader and filler
│   │   ├── parser_agent.py      # PDF text extraction and classification
│   │   └── mapping_agent.py     # Gemini-powered field name mapper
│   ├── tools/
│   │   ├── cfr_lookup.py        # CFR Title 38 Part 4 diagnostic code lookup
│   │   ├── combined_rating.py   # VA whole-person combined rating math
│   │   ├── pact_act_check.py    # PACT Act presumptive eligibility check
│   │   ├── tdiu_check.py        # TDIU eligibility under 38 CFR §4.16
│   │   └── va_pay_lookup.py     # 2026 VA disability pay rates
│   ├── voice_agent/
│   │   ├── router.py            # FastAPI WebSocket endpoint /voice/ws
│   │   ├── session.py           # GeminiLiveSession wrapper
│   │   └── models.py            # ClaimContext, TranscriptEntry
│   ├── data/
│   │   ├── cfr38_part4.json     # CFR Title 38 Part 4 rating criteria
│   │   ├── combined_ratings_table.json
│   │   ├── pact_act_conditions.json
│   │   └── va_pay_rates_2026.json
│   ├── schemas.py               # Pydantic models (ParsedClaim, AuditResult, etc.)
│   └── server.py                # Flask API server
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── LandingPage.jsx
│       │   ├── UploadPage.jsx
│       │   ├── TrackerPage.jsx       # SSE pipeline progress
│       │   ├── AuditResultsPage.jsx  # Findings and pre-filled forms
│       │   └── CallingAgentPage.jsx  # Vapi outbound call interface
│       └── App.jsx                   # Page routing
├── mock_va_portal/              # Simulated VA eBenefits portal for testing
├── start.sh                     # One-command startup for all services
└── requirements.txt
```

---

## Getting Started

### Prerequisites

- Python 3.13+
- Node.js 18+
- API keys (see below)

### 1. Clone and configure

```bash
git clone https://github.com/usffish/vetclaim-ai.git
cd vetclaim-ai
cp .env.example .env
# Fill in your API keys in .env
```

### 2. API Keys

| Variable | Where to get it |
|---|---|
| GOOGLE_API_KEY | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| ELEVENLABS_API_KEY | [ElevenLabs](https://elevenlabs.io) |
| VA_API_KEY | [VA Developer Portal](https://developer.va.gov) |
| VA_FORMS_API_KEY | [VA Forms API sandbox](https://developer.va.gov/explore/api/va-forms/sandbox-access) |
| VAPI_API_KEY | [Vapi.ai](https://vapi.ai) |
| VAPI_PHONE_NUMBER_ID | Vapi dashboard — your provisioned phone number ID |

### 3. Start everything

```bash
./start.sh
```

This creates a Python venv, installs dependencies, and starts all three services:

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:5001 |
| Mock VA Portal | http://localhost:5050 |

### 4. Try it with a sample case

Sample veteran documents are in veterans/ (multiple test cases). Upload the PDFs from any veteran folder through the frontend to see the full pipeline in action.

---

## Running Tests

```bash
# Backend
pytest backend/

# Frontend / Mock VA Portal
cd mock_va_portal
npx vitest --run
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/upload | Upload PDFs, start pipeline, returns job_id |
| GET | /api/stream/\<job_id\> | SSE stream of pipeline progress |
| GET | /api/result/\<job_id\> | Completed audit result JSON |
| GET | /api/download?path=... | Download pre-filled VA form PDF |
| POST | /api/submit-appeal | Submit forms to mock VA portal |
| POST | /api/start-va-call | Initiate outbound AI call to VA via Vapi |
| GET | /calls/\<call_id\> | Fetch call record from Vapi |
| GET | /api/status | Health check |

---

## Data Sources

All reference data is stored locally as JSON — no external lookups at runtime:

- **CFR Title 38 Part 4** — Complete diagnostic code database with rating criteria at every percentage level
- **PACT Act Conditions** — Presumptive conditions by exposure category (burn pits, Agent Orange, radiation, etc.)
- **VA Pay Rates 2026** — Monthly disability compensation by rating (0–100%) and dependent status
- **Combined Ratings Table** — VA whole-person math lookup table

---

## Security Notes

- .env is gitignored — never commit API keys
- No PII (veteran name, SSN, claim number) is persisted beyond the session scope
- All audio data is transient — never written to disk
- Path traversal protection on the /api/download endpoint
- CORS origins are configurable via CORS_ORIGINS env var

---

## License

MIT

---

## Author

**Ismail Jhaveri** — [LinkedIn](https://www.linkedin.com/in/ismail-jhaveri-2021/) · [ismailj@usf.edu](mailto:ismailj@usf.edu)
