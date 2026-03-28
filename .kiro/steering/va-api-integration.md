---
inclusion: manual
---

# VetClaim AI — VA API Integration Guide

Source: https://developer.va.gov/explore (23 APIs reviewed March 2026)

## APIs That Are Directly Useful

### 1. Veteran Service History and Eligibility API ⭐ HIGH PRIORITY
URL: https://developer.va.gov/explore/api/veteran-service-history-and-eligibility
Auth: Authorization Code Grant + Client Credentials Grant (sandbox available)

What it gives us:
- Veteran's confirmed Title 38 status (are they actually a veteran?)
- Current disability ratings already on file
- Full service history (branch, dates, deployments)

Why it matters for VetClaim AI:
- Service history is required for PACT Act eligibility checks (era + deployment location)
- Current disability ratings let us skip manual parsing for veterans who connect their account
- Replaces the need to ask the veteran to manually enter their service era

Hackathon use: Mock this with the sandbox test users. In the demo, show it
"pulling" the veteran's service history automatically instead of asking them to type it.

---

### 2. Appealable Issues API ⭐ HIGH PRIORITY
URL: https://developer.va.gov/explore/api/appealable-issues
Auth: Authorization Code Grant + Client Credentials Grant (sandbox available)

What it gives us:
- List of a veteran's previously decided issues that are eligible for appeal
- Directly feeds the Auditor Agent — these are the exact conditions to audit

Why it matters for VetClaim AI:
- Instead of parsing a PDF, we can pull the decided issues directly from the VA
- Each issue comes with its decision date, which matters for appeal deadlines
- This is the cleanest possible input for the audit pipeline

Hackathon use: Use sandbox test data to show "connecting to VA" and pulling
appealable issues live — much more impressive than uploading a PDF for the demo.

---

### 3. Benefits Claims API ⭐ HIGH PRIORITY
URL: https://developer.va.gov/explore/api/benefits-claims
Auth: Authorization Code Grant + Client Credentials Grant (sandbox available)

What it gives us:
- Find all existing benefits claims for a veteran
- Auto-establish Intent to File (ITF) — locks in the effective date immediately
- Submit form 21-526EZ (disability compensation claim) programmatically

Why it matters for VetClaim AI:
- Filing an Intent to File the moment a veteran starts an audit protects their
  backdated pay — this is a huge value-add that no other tool does automatically
- In v1.0, we could submit the actual appeal directly through this API

Hackathon use: Show the ITF being auto-filed in the demo — "We just locked in
your effective date. Your backdated pay is now protected."

---

### 4. Decision Reviews API (RESTRICTED — skip for hackathon)
URL: https://developer.va.gov/explore/api/decision-reviews
Auth: RESTRICTED ACCESS — requires VA approval

What it gives us: Submit NOD, Higher-Level Review, Supplemental Claims directly
Why restricted: Requires production approval — not available for hackathon sandbox
Plan: Note this as the v1.0 target. The hackathon generates the PDF; v1.0 submits it.

---

### 5. Benefits Reference Data API ✅ OPEN DATA — use immediately
URL: https://developer.va.gov/explore/api/benefits-reference-data
Auth: OPEN DATA — no key required

What it gives us:
- List of all VA disabilities (with codes) — useful for validating our cfr38_part4.json
- VA medical treatment centers
- Other reference data for benefits claims

Hackathon use: Call this at build time to validate/supplement our bundled JSON data files.

---

### 6. VA Forms API ✅ OPEN DATA — use immediately
URL: https://developer.va.gov/explore/api/va-forms
Auth: OPEN DATA — no key required

What it gives us:
- Current versions of all VA forms (21-526EZ, 10182 NOD form, etc.)
- Links to download the latest PDF versions

Hackathon use: Show the correct, current form version in the phone script output.
Avoids the embarrassing situation of referencing an outdated form number.

---

### 7. VA Facilities API ✅ OPEN DATA — use immediately
URL: https://developer.va.gov/explore/api/va-facilities
Auth: OPEN DATA — no key required

What it gives us:
- VA regional office addresses, phone numbers, hours
- Used to populate the "send your NOD to:" address in the appeal letter

Hackathon use: Look up the veteran's nearest VA regional office by zip code
and auto-populate the NOD letter header. Small detail, big polish.

---

## APIs to Skip
- Address Validation — not relevant
- Clinical Health / Patient Health (FHIR) — health records, not claims
- Community Care Eligibility — outpatient care routing, not disability claims
- Direct Deposit Management — RESTRICTED, not relevant to audit
- Education Benefits — GI Bill, different domain
- Guaranty/Loan APIs — home loans, different domain
- Legacy Appeals API — superseded by Decision Reviews API

---

## Sandbox Setup (do this in Phase 0)

All three priority APIs have sandbox access with test users:
1. Go to each API's sandbox-access page and request a key
2. Test users are provided at /test-users for each API
3. Base URL for sandbox: https://sandbox-api.va.gov

```python
# Example: pull appealable issues for a test veteran
import requests

headers = {
    "Authorization": f"Bearer {sandbox_token}",
    "Content-Type": "application/json"
}

response = requests.get(
    "https://sandbox-api.va.gov/services/appeals/v1/appealable-issues",
    headers=headers,
    params={"icn": test_veteran_icn}  # ICN = Integration Control Number (VA's veteran ID)
)

issues = response.json()["data"]
```

---

## Integration Priority for Demo

For maximum demo impact, wire these up in this order:

1. Appealable Issues API → replaces PDF upload for the "connected" demo flow
2. Veteran Service History → auto-populates service era for PACT Act check
3. Benefits Claims API → auto-file Intent to File at session start
4. VA Facilities API → auto-populate NOD letter regional office address
5. VA Forms API → reference correct form versions in phone script

The PDF upload path stays as the fallback for veterans who don't want to connect
their VA account — both flows should work in the demo.
