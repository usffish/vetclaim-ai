# VetClaim AI - Integration Guide

**Status:** ✅ Auditor Agent + Mock VA Portal Integrated & Ready

## Branches

- **`main`** — Stable (cross-platform git rules)
- **`mohammed`** — Your auditor agent work (pushed to remote)
- **`dev`** — Development branch with all features merged
- **`origin/Ismail`** — Teammate's mock VA portal (merged into dev/mohammed)

---

## What's Integrated

### 1. Auditor Agent (`backend/agents/auditor_agent.py`)
Google ADK `LlmAgent` with 8 tools:
- **cfr_lookup** — Diagnostic code → CFR rating criteria
- **cfr_compare_rating** — Check if assigned rating matches symptoms
- **pact_act_check** — Burn pit/Agent Orange presumptive eligibility
- **tdiu_check** — Total Disability qualification (100% pay)
- **combined_rating** — VA whole-person math validation
- **check_combined_rating_error** — Detect math mistakes in decision
- **va_pay_lookup** — 2026 pay rates by rating + dependents
- **calculate_pay_impact** — Financial impact of rating increase

**Data files:**
- `cfr38_part4.json` — 30 diagnostic codes with full criteria
- `pact_act_conditions.json` — Presumptive conditions by exposure
- `va_pay_rates_2026.json` — Monthly payment schedule
- `combined_ratings_table.json` — VA math formula + lookup table

**Output:** `AuditResult` with 5-10 flags (under-rated, PACT eligible, TDIU, etc.)

### 2. Mock VA Portal (`mock_va_portal/`)
Frontend + backend for demo:
- **`index.html`** — Veteran's eBenefits dashboard (shows denied claims)
- **`confirmation.html`** — Appeal submission confirmation page
- **`server.py`** — Flask backend that receives PDFs from VetClaim app
- **`va_api.js`** — Dashboard JS: polls for submissions, shows green notification

**API Endpoints:**
- `POST /submit-appeal` — VetClaim app POSTs the appeal PDF here
- `GET /submissions` — Frontend polls for new submissions
- `GET /submissions/<id>/pdf` — Serves PDF for display

---

## Full Demo Flow

```
┌────────────────────────────────────────────────────────────┐
│ 1. Start Mock VA Portal                                    │
│    $ cd mock_va_portal && python3 server.py                │
│    → http://localhost:5050 (shows veteran at 30%)         │
└──────────────────┬───────────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────────┐
│ 2. Start VetClaim Auditor                                │
│    - Upload VA Rating Decision Letter (PDF)              │
│    - Auditor parses & analyzes (30 seconds)              │
│    - Generates NOD appeal + $156K financial impact       │
└──────────────────┬───────────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────────┐
│ 3. Submit Appeal to Mock VA Portal                        │
│    import requests                                        │
│    response = requests.post(                              │
│      'http://localhost:5050/submit-appeal',              │
│      files={'file': ('appeal.pdf', pdf_bytes)}           │
│    )                                                       │
└──────────────────┬───────────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────────┐
│ 4. See Confirmation in VA Portal                          │
│    - Switch back to http://localhost:5050                │
│    - Green notification appears (polls every 3 sec)      │
│    - Shows confirmation number (VA-2026-NOD-XXXXXX)      │
│    - Click "View Submission" to see PDF inline           │
└────────────────────────────────────────────────────────────┘
```

---

## Run the Auditor

### Quick Test (Verify Tools Work)

```bash
python3 backend/test_auditor_tools.py
```

This demonstrates:
- PTSD under-rating (30% → 70%)
- PACT Act asthma eligibility
- TDIU qualification
- Combined rating math
- $156K financial impact

Expected output: ✅ ALL TOOL TESTS PASSED

### Run Individual Tools

```python
# CFR lookup
from backend.tools.cfr_lookup import cfr_lookup
print(cfr_lookup("9411"))  # PTSD criteria

# PACT Act check
from backend.tools.pact_act_check import pact_act_check
result = pact_act_check("asthma", ["Iraq", "Afghanistan"], "post-9/11")

# TDIU check
from backend.tools.tdiu_check import tdiu_check
result = tdiu_check([70, 30, 10])  # Ratings

# Pay impact
from backend.tools.va_pay_lookup import calculate_pay_impact
result = calculate_pay_impact(30, 70)  # Current → Potential
```

---

## Run Mock VA Portal

```bash
cd mock_va_portal

# Install Flask
pip install flask flask-cors

# Start server
python3 server.py
# → http://localhost:5050
```

The portal has:
- **Dashboard** (`/`) — Shows veteran's claims + denied callout
- **Confirmation** (`/confirmation`) — Shows submitted appeal

---

## Integration Points

### Parser → Auditor

Teammate's parser outputs `ParsedClaim`:
```python
from backend.agents.parser_agent import VAClaimParser
from backend.schemas import ParsedClaim

parser = VAClaimParser(pdf_dir="backend")
parsed: ParsedClaim = parser.extract_all()
```

Auditor consumes it:
```python
from backend.agents.auditor_agent import auditor_agent

# Send parsed claim to auditor
audit_result = auditor_agent.run_live(context)
```

### Auditor → Mock Portal

POSTs the appeal PDF:
```python
import requests

response = requests.post(
    "http://localhost:5050/submit-appeal",
    files={"file": ("appeal.pdf", pdf_bytes)},
    data={
        "veteran_name": "James Miller",
        "conditions": "PTSD, TBI, Asthma"
    }
)
print(response.json()["confirmation_number"])
# → VA-2026-NOD-048821
```

---

## What Still Needs Building

1. **Main App UI** — Upload PDF, show auditor results, submit button
2. **Advocate Agent** — Debate loop (challenges auditor flags)
3. **Negotiator Agent** — Drafts NOD letter + phone script + forms
4. **Orchestrator** — Wires all agents together (SequentialAgent)
5. **PDF Generator** — ReportLab output (NOD letter + flag table)

---

## Folder Structure

```
vetclaim/
├── backend/
│   ├── agents/
│   │   ├── auditor_agent.py      ✅ Complete
│   │   └── parser_agent.py       ✅ (Teammate)
│   ├── tools/                    ✅ 5 tools complete
│   ├── data/                     ✅ 4 JSON files
│   ├── schemas.py                ✅ Pydantic models
│   └── test_auditor_tools.py     ✅ Demo test
├── mock_va_portal/               ✅ Complete (merged from Ismail)
│   ├── index.html                ✅
│   ├── confirmation.html         ✅
│   ├── server.py                 ✅
│   └── tests/                    ✅
├── RUN.md                        ✅ How to test
├── INTEGRATION.md                ✅ This file
└── .env                          ✅ API keys present
```

---

## Branches Ready

Run from any branch:

```bash
# View all branches
git branch -vv

# Switch to dev (has everything)
git checkout dev

# Switch to mohammed (your work)
git checkout mohammed

# Push any changes
git push origin <branch>
```

---

## Next Steps for Demo

1. ✅ Auditor agent built and tested
2. ✅ Mock VA portal integrated
3. ⏳ Main app UI (Vite/React)
4. ⏳ Advocate + Negotiator agents
5. ⏳ End-to-end orchestrator test

**Demo day:** Upload PDF → See auditor flags → Submit to VA portal → Confirmation
