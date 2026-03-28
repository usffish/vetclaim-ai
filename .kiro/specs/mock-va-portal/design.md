# Design Document — Mock VA Portal

## Overview

The Mock VA Portal is a demo web application that simulates the VA eBenefits portal for the VetClaim AI hackathon demo. It provides the "before" and "after" bookends of the live demo story: a veteran sees their denied claims on the dashboard, the VetClaim AI app runs in a separate tab and submits an appeal, then the veteran returns to the portal and sees a confirmation page showing the appeal was received.

The portal is not a static site — it includes a Flask backend that receives PDF submissions from the VetClaim AI app and serves them back to the confirmation page. The frontend makes live calls to two VA sandbox APIs to demonstrate real VA data connectivity.

### Design Goals

- Look convincingly like VA.gov to judges who may not know the real site
- Receive a PDF from the VetClaim AI app and display it on the confirmation page
- Make live VA API calls to prove real integration, with graceful fallback if APIs are unreachable
- Work reliably in a hackathon environment (no database, no auth, no build step, no CDN dependencies)

---

## Architecture

The system has three layers:

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser (Presenter's laptop)                                   │
│                                                                 │
│  index.html + va_api.js          confirmation.html + confirmation.js │
│  ├─ polls /submissions (3s)      ├─ fetches /submissions        │
│  └─ calls VA Benefits Ref API   └─ calls VA Forms API          │
└──────────────┬──────────────────────────────┬───────────────────┘
               │ HTTP (localhost:5050)         │ HTTP (localhost:5050)
               ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Flask Server (server.py, port 5050)                            │
│  ├─ POST /submit-appeal  ← VetClaim AI app sends PDF here       │
│  ├─ GET  /submissions    → returns in-memory list               │
│  └─ GET  /submissions/<id>/pdf → serves stored PDF              │
│                                                                 │
│  In-memory store: submissions[]                                 │
│  Disk store: mock_va_portal/submissions/*.pdf                   │
└─────────────────────────────────────────────────────────────────┘
               ▲
               │ multipart/form-data POST (cross-origin)
┌──────────────┴──────────────────────────────────────────────────┐
│  VetClaim AI App (separate port)                                │
│  Sends: file (PDF), veteran_name, conditions                    │
└─────────────────────────────────────────────────────────────────┘
```

External API calls go directly from the browser to VA sandbox:

```
Browser → https://sandbox-api.va.gov/services/benefits-reference-data/v1/service-branches
Browser → https://sandbox-api.va.gov/services/va_forms/v0/forms?query=10182
```

### Key Architectural Decisions

**Flask server instead of static files** — The portal needs to receive a PDF binary from the VetClaim app (a different origin) and serve it back. This requires a server. A static file host cannot accept POST requests or store files.

**In-memory submission store** — A Python list is sufficient for a hackathon demo. No database setup, no migrations, no connection strings. The tradeoff is that submissions are lost on server restart, which is acceptable.

**CORS enabled globally** — The VetClaim app runs on a different localhost port. Flask-CORS allows cross-origin POSTs without browser security errors.

**Polling instead of WebSockets** — A 3-second `setInterval` poll is simpler to implement and debug than a WebSocket connection. Latency of up to 3 seconds is imperceptible in a live demo.

**API keys in HTML meta tags** — The frontend JS reads keys from `<meta name="va-api-key">` rather than hardcoding them. This keeps keys out of JS source while avoiding a build step or server-side templating.

---

## Components and Interfaces

### server.py — Flask Backend

The backend is a single Python file with three routes.

**POST /submit-appeal**

Accepts multipart/form-data from the VetClaim AI app.

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | PDF binary | yes | The NOD appeal PDF |
| `veteran_name` | string | no | Defaults to "James R. Wilson" |
| `conditions` | string | no | Comma-separated condition names |

Returns:
```json
{
  "success": true,
  "confirmation_number": "VA-2026-NOD-048821",
  "message": "Appeal documents received. Confirmation: VA-2026-NOD-048821"
}
```

Errors: `400` if no file is provided or filename is empty.

**GET /submissions**

Returns the full in-memory submissions list, most recent first (reversed).

```json
[
  {
    "id": "VA-2026-NOD-048821",
    "confirmation_number": "VA-2026-NOD-048821",
    "veteran_name": "James R. Wilson",
    "conditions": "PTSD (DC 9411), Respiratory Condition (DC 6604), TBI (DC 8045)",
    "submitted_at": "March 28, 2026 at 11:47 AM EST",
    "pdf_filename": "VA-2026-NOD-048821.pdf",
    "documents": [...]
  }
]
```

**GET /submissions/\<id\>/pdf**

Looks up the submission by ID, finds the PDF on disk, and returns it with `Content-Type: application/pdf` and inline disposition so the browser renders it in an `<iframe>`.

Returns `404` if the submission ID is not found or the PDF file is missing from disk.

---

### va_api.js — Dashboard Frontend Logic

Two responsibilities, each in its own function:

**`initVABranchVerification()`** — Called on `DOMContentLoaded`. Fetches `/service-branches` from the VA Benefits Reference Data API, finds the entry matching `"ARMY"`, updates the `#va-service-branch` element with the official description, and appends a `✓ VA Verified` badge. On any error, falls back to the string `"Army"` with no badge.

**`startSubmissionPolling()`** — Called on `DOMContentLoaded`. Sets a 3-second interval that GETs `/submissions` from the Flask server. Tracks seen submission IDs in a `Set` to avoid re-showing the same banner. When a new submission is detected, calls `showSubmissionBanner()` to inject a green notification banner into `#submission-notification`.

API key is read from `<meta name="va-api-key">` in the HTML head.

---

### confirmation.js — Confirmation Page Logic

**`init()`** — Entry point, called on `DOMContentLoaded`. Reads the submission ID from the URL query string (`?id=VA-2026-NOD-XXXXXX`). If no ID is present, loads the most recent submission instead (allows the presenter to navigate directly to `confirmation.html` without clicking through from the dashboard).

**`fetchSubmission(submissionId)`** — GETs `/submissions` and finds the matching record. Returns `null` if the list is empty or the ID is not found.

**`fetchForm10182Details()`** — Calls the VA Forms API (`/forms?query=10182`) to get live metadata for VA Form 10182 (Notice of Disagreement). Returns form name, title, last revision date, page count, and official PDF URL. Falls back to `null` on any error.

**`renderConfirmation(submission)`** — Builds the full confirmation page HTML from the submission object and injects it into `#confirmation-content`. Calls `fetchForm10182Details()` in parallel. Embeds the PDF via an `<iframe>` pointing to `/submissions/<id>/pdf`.

**`renderError(message)`** — Shows a centered error card with a return link if the submission cannot be loaded.

---

### index.html — Dashboard Page

Static HTML shell. Contains:
- US government banner
- VA header with nav and "Signed in as James R. Wilson"
- Rating banner (30%, $524.31, Decision Final)
- `#submission-notification` div (empty until `va_api.js` injects a banner)
- Rated conditions table (6 rows, 2 with `table-row--denied` class)
- Denied callout banner
- Sidebar: service info (`#va-service-branch`), appeal deadline card, claim documents
- Footer with disclaimer
- `<meta name="va-api-key">` and `<meta name="va-forms-api-key">` tags

---

### confirmation.html — Confirmation Page Shell

Minimal HTML shell. Contains only the chrome (banner, header, footer) and a `#confirmation-content` div with a loading placeholder. All content is injected by `confirmation.js`.

---

### style.css — Shared Stylesheet

Single file, no external dependencies. USWDS-inspired design tokens:

| Token | Value | Usage |
|---|---|---|
| VA navy | `#112e51` | Headers, nav backgrounds |
| VA blue | `#005ea2` | Links |
| VA gold | `#f9c642` | Rating numerals accent |
| Granted green | `#2e8540` | Service connected decisions |
| Denied red | `#b50909` | Denied decisions |

Responsive breakpoints: `900px` (two-column → single column), `600px` (rating banner stacks vertically).

---

## Data Models

### Submission Object (in-memory, Python dict)

```python
{
    "id": str,                  # same as confirmation_number, e.g. "VA-2026-NOD-048821"
    "confirmation_number": str, # "VA-YYYY-NOD-XXXXXX"
    "veteran_name": str,        # from POST form field, default "James R. Wilson"
    "conditions": str,          # comma-separated, e.g. "PTSD (DC 9411), ..."
    "submitted_at": str,        # human-readable, e.g. "March 28, 2026 at 11:47 AM EST"
    "pdf_filename": str,        # filename on disk, e.g. "VA-2026-NOD-048821.pdf"
    "documents": [
        {
            "name": str,        # e.g. "Notice of Disagreement (NOD)"
            "form": str,        # e.g. "Form 10182"
            "pages": int        # e.g. 4
        }
    ]
}
```

### Confirmation Number Format

`VA-{YYYY}-NOD-{XXXXXX}` where `YYYY` is the current year and `XXXXXX` is a 6-digit random decimal string. Generated by `generate_confirmation_number()` in `server.py`.

### VA Forms API Response (relevant fields)

```javascript
{
  data: [{
    attributes: {
      form_name: "VA10182",
      title: "Decision Review Request: Board Appeal...",
      last_revision_on: "2022-03-15",
      pages: 3,
      url: "https://www.vba.va.gov/pubs/forms/VBA-10182-ARE.pdf",
      form_details_url: "https://www.va.gov/find-forms/about-form-10182/"
    }
  }]
}
```

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Confirmation number format invariant

*For any* call to `generate_confirmation_number()`, the returned string must match the pattern `VA-\d{4}-NOD-\d{6}`.

**Validates: Requirements 2.2**

### Property 2: Submit-appeal round trip

*For any* valid multipart POST to `/submit-appeal` containing a PDF file, the returned `confirmation_number` must appear in the response from a subsequent GET to `/submissions`.

**Validates: Requirements 2.2, 2.3**

### Property 3: Confirmation page renders all submission fields

*For any* submission object with a `confirmation_number`, `submitted_at`, `conditions`, `veteran_name`, and `documents` list, the HTML string produced by `renderConfirmation` must contain each of those values.

**Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.7**

### Property 4: VA branch API success path shows badge

*For any* VA Benefits Reference Data API response that contains an item with `code === "ARMY"`, calling `initVABranchVerification` must result in the `#va-service-branch` element showing the item's `description` and a sibling element with class `va-verified-badge` being present in the DOM.

**Validates: Requirements 3.2**

### Property 5: VA branch API failure path shows fallback without badge

*For any* error condition from the VA Benefits Reference Data API (network failure, non-2xx status, malformed JSON), calling `initVABranchVerification` must result in the `#va-service-branch` element showing `"Army"` and no `va-verified-badge` element being present.

**Validates: Requirements 3.3**

### Property 6: Disclaimer present on all pages

*For any* HTML page in the portal (`index.html`, `confirmation.html`), the footer must contain the string `"Demo mock portal — VetClaim AI HackUSF 2026. Not affiliated with the U.S. Department of Veterans Affairs."`.

**Validates: Requirements 1.8, 2.9, 8.1**

### Property 7: No external stylesheet dependencies

*For any* HTML page in the portal, all `<link rel="stylesheet">` elements must reference local files only — no `http://` or `https://` URLs.

**Validates: Requirements 6.2**

---

## Error Handling

**VA API unreachable** — Both `initVABranchVerification` and `fetchForm10182Details` wrap their fetch calls in `try/catch`. On any error, they fall back to static content and log a warning to the console. The demo continues without the `✓ VA Verified` badge.

**Flask server not running** — `startSubmissionPolling` silently swallows fetch errors (server not yet started is expected before the demo). `confirmation.js` catches the error and calls `renderError()` with a human-readable message telling the presenter to start `server.py`.

**Submission not found** — If the `?id=` query param points to a non-existent submission, `fetchSubmission` returns `null` and `renderError()` is shown. If no ID is given and the submissions list is empty, the same error state is shown.

**PDF missing from disk** — The `/submissions/<id>/pdf` route returns `404` if the file is not on disk. The `<iframe>` in the confirmation page will show a browser-native error, and a fallback `<p>` tag inside the iframe offers a direct download link.

**Empty or missing file in POST** — `/submit-appeal` returns `400` with a descriptive JSON error message if `file` is absent or has an empty filename.

---

## Testing Strategy

### Dual Testing Approach

Unit tests cover specific examples, static content checks, and error conditions. Property-based tests verify universal behaviors across generated inputs.

### Unit Tests

Focus areas:
- `generate_confirmation_number()` returns a string matching the expected format (example)
- `POST /submit-appeal` with a valid PDF returns 201 and a confirmation number (example)
- `POST /submit-appeal` with no file returns 400 (example)
- `GET /submissions` returns an empty list on a fresh server (example)
- `GET /submissions/<id>/pdf` returns 404 for an unknown ID (example)
- `index.html` contains the 30% rating, $524.31 payment, and 6 condition rows (example)
- `index.html` contains exactly 2 rows with class `table-row--denied` (example)
- Both HTML pages contain the US government banner (example)
- Both HTML pages contain "Signed in as James R. Wilson" (example)
- `style.css` contains `#112e51`, `#005ea2`, `#2e8540`, `#b50909` (example)
- `style.css` contains a `@media` rule for `max-width: 900px` (example)
- `va_api.js` does not contain any hardcoded API key string (example)

### Property-Based Tests

Use `hypothesis` (Python) for server-side properties and `fast-check` (JavaScript) for frontend properties.

Each property test must run a minimum of 100 iterations.

**Tag format:** `Feature: mock-va-portal, Property {N}: {property_text}`

| Property | Test | Library |
|---|---|---|
| P1: Confirmation number format | Generate N calls to `generate_confirmation_number()`, assert all match regex | hypothesis |
| P2: Submit-appeal round trip | Generate random veteran names and condition strings, POST each, assert confirmation number appears in GET /submissions | hypothesis |
| P3: Confirmation page renders all fields | Generate random submission objects, call `renderConfirmation`, assert all fields present in output HTML | fast-check |
| P4: VA branch API success shows badge | Generate mock API responses with varying branch lists, assert badge appears when ARMY is present | fast-check |
| P5: VA branch API failure shows fallback | Generate various error types (TypeError, non-ok Response), assert fallback text and no badge | fast-check |
| P6: Disclaimer on all pages | Parse each HTML file, assert footer contains disclaimer string | pytest (static) |
| P7: No external stylesheets | Parse each HTML file, assert no link href starts with http | pytest (static) |

### Property Test Configuration

```python
# Example: Property 1 — hypothesis
# Feature: mock-va-portal, Property 1: confirmation number format invariant
from hypothesis import given, settings
import strategies as st

@given(st.none())  # no input needed — function takes no args
@settings(max_examples=100)
def test_confirmation_number_format(_):
    number = generate_confirmation_number()
    assert re.match(r"^VA-\d{4}-NOD-\d{6}$", number)
```

```javascript
// Example: Property 3 — fast-check
// Feature: mock-va-portal, Property 3: confirmation page renders all submission fields
fc.assert(
  fc.property(arbitrarySubmission(), async (submission) => {
    document.getElementById("confirmation-content").innerHTML = "";
    await renderConfirmation(submission);
    const html = document.getElementById("confirmation-content").innerHTML;
    return (
      html.includes(submission.confirmation_number) &&
      html.includes(submission.submitted_at) &&
      html.includes(submission.veteran_name) &&
      submission.documents.every(doc => html.includes(doc.name))
    );
  }),
  { numRuns: 100 }
);
```
