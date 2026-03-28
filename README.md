# VetClaim AI — HackUSF 2026

AI-powered VA disability claims auditor. Reads VA Rating Decision Letters, flags errors and missing benefits, and automatically submits a Notice of Disagreement appeal.

> "77% of VA claims are denied on first submission. VetClaim AI audits your claim in 60 seconds and generates your appeal letter."

---

## Project Structure

```
vetclaim/
├── mock_va_portal/        # Mock VA eBenefits portal (demo bookends)
│   ├── index.html         # Dashboard — veteran sees denied claims
│   ├── confirmation.html  # Confirmation — appeal submission received
│   ├── style.css          # Shared stylesheet (USWDS-inspired, no CDN)
│   ├── va_api.js          # Dashboard JS: VA API calls + submission polling
│   ├── confirmation.js    # Confirmation JS: loads submission + PDF
│   └── server.py          # Flask backend: receives PDFs from VetClaim app
├── .kiro/
│   ├── specs/             # Feature specs (requirements, design, tasks)
│   └── steering/          # Agent coding standards and architecture guides
├── .env.example           # API key template — copy to .env
└── README.md
```

---

## Mock VA Portal

The mock portal simulates VA.gov for the demo. It has two pages and a Flask backend.

### Run the portal server

```bash
cd mock_va_portal
pip install flask flask-cors
python3 server.py
# → http://localhost:5050
```

### Demo flow

1. Open `http://localhost:5050` — veteran sees 30% rating with 2 denied claims
2. Switch to VetClaim AI app — app audits claim and POSTs the NOD appeal PDF
3. Switch back to VA portal — green notification appears within 3 seconds
4. Click "View Submission" — confirmation page shows the PDF and report number

### VetClaim app integration

POST the generated PDF to the mock VA portal:

```python
import requests

with open("appeal.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:5050/submit-appeal",
        files={"file": ("appeal.pdf", f, "application/pdf")},
        data={
            "veteran_name": "James R. Wilson",
            "conditions": "PTSD (DC 9411), Respiratory Condition (DC 6604), TBI (DC 8045)"
        }
    )

confirmation_number = response.json()["confirmation_number"]
# e.g. "VA-2026-NOD-048821"
```

---

## Setup

```bash
# 1. Copy env template
cp .env.example .env
# Edit .env and add your API keys

# 2. Install dependencies
pip install flask flask-cors

# 3. Run the mock VA portal
cd mock_va_portal && python3 server.py
```

### API Keys needed

| Key | Where to get it |
|-----|----------------|
| `VA_API_KEY` | [VA Benefits Reference Data API sandbox](https://developer.va.gov/explore/api/benefits-reference-data/sandbox-access) |
| `VA_FORMS_API_KEY` | [VA Forms API sandbox](https://developer.va.gov/explore/api/va-forms/sandbox-access) |
| `GOOGLE_API_KEY` | [Google AI Studio](https://aistudio.google.com) |
| `ELEVENLABS_API_KEY` | [ElevenLabs](https://elevenlabs.io) |

---

## Disclaimer

This tool is informational only and does not constitute legal advice. Always consult a VSO or VA-accredited attorney before filing an appeal.

*VetClaim AI — HackUSF 2026*
