# Implementation Plan: Mock VA Portal

## Overview

Core implementation files are complete (`index.html`, `confirmation.html`, `style.css`, `va_api.js`, `confirmation.js`, `server.py`). Remaining work is the test suite (pytest unit tests, hypothesis property tests, JS fast-check property tests, static HTML checks) and final demo verification.

## Tasks

- [x] 1. Build Flask backend (server.py)
  - Implement POST /submit-appeal, GET /submissions, GET /submissions/<id>/pdf
  - Implement generate_confirmation_number()
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 2. Build dashboard frontend (index.html + va_api.js)
  - Implement initVABranchVerification() and startSubmissionPolling()
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Build confirmation page (confirmation.html + confirmation.js)
  - Implement renderConfirmation(), fetchSubmission(), fetchForm10182Details(), renderError()
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9_

- [x] 4. Build shared stylesheet (style.css)
  - VA design tokens, responsive breakpoints at 900px and 600px
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 6.1, 6.2, 7.1, 7.2, 7.3_

- [x] 5. Write Python unit tests for server.py
  - Create `mock_va_portal/tests/test_server.py` using pytest
  - Test `generate_confirmation_number()` returns a string matching `VA-\d{4}-NOD-\d{6}`
  - Test POST /submit-appeal with a valid PDF returns 201 and a confirmation_number field
  - Test POST /submit-appeal with no file returns 400
  - Test POST /submit-appeal with empty filename returns 400
  - Test GET /submissions returns an empty list on a fresh server instance
  - Test GET /submissions/<id>/pdf returns 404 for an unknown submission ID
  - _Requirements: 2.2, 2.3_

  - [x] 5.1 Write property test for confirmation number format (P1)
    - **Property 1: Confirmation number format invariant**
    - Use `hypothesis` — generate N calls to `generate_confirmation_number()`, assert all match `^VA-\d{4}-NOD-\d{6}$`
    - Tag: `Feature: mock-va-portal, Property 1: confirmation number format invariant`
    - Run minimum 100 examples
    - **Validates: Requirements 2.2**

  - [x] 5.2 Write property test for submit-appeal round trip (P2)
    - **Property 2: Submit-appeal round trip**
    - Use `hypothesis` — generate random veteran names and condition strings, POST each to /submit-appeal, assert the returned confirmation_number appears in GET /submissions
    - Tag: `Feature: mock-va-portal, Property 2: submit-appeal round trip`
    - Run minimum 100 examples
    - **Validates: Requirements 2.2, 2.3**

- [x] 6. Write static HTML validation tests
  - Create `mock_va_portal/tests/test_html_static.py` using pytest
  - Parse `index.html` and `confirmation.html` with Python's `html.parser`

  - [x] 6.1 Write property test for disclaimer on all pages (P6)
    - **Property 6: Disclaimer present on all pages**
    - For each HTML file in the portal, assert footer contains `"Demo mock portal — VetClaim AI HackUSF 2026. Not affiliated with the U.S. Department of Veterans Affairs."`
    - Tag: `Feature: mock-va-portal, Property 6: disclaimer present on all pages`
    - **Validates: Requirements 1.8, 2.9, 8.1**

  - [x] 6.2 Write property test for no external stylesheets (P7)
    - **Property 7: No external stylesheet dependencies**
    - For each HTML file, assert no `<link rel="stylesheet">` href starts with `http://` or `https://`
    - Tag: `Feature: mock-va-portal, Property 7: no external stylesheet dependencies`
    - **Validates: Requirements 6.2**

  - Additional static checks (examples):
    - `index.html` contains "30%", "$524.31", and exactly 6 `<tr>` rows in the conditions table
    - `index.html` contains exactly 2 elements with class `table-row--denied`
    - Both pages contain the US government banner text
    - Both pages contain "Signed in as James R. Wilson"
    - `style.css` contains `#112e51`, `#005ea2`, `#2e8540`, `#b50909`
    - `style.css` contains a `@media` rule for `max-width: 900px`
    - `va_api.js` does not contain any hardcoded API key string
    - _Requirements: 1.1, 1.2, 1.3, 4.1, 4.4, 4.5, 4.6, 6.2_

- [x] 7. Write JavaScript unit and property tests for frontend logic
  - Create `mock_va_portal/tests/va_api.test.js` and `mock_va_portal/tests/confirmation.test.js`
  - Use a JS test runner (Jest or Vitest) with `fast-check` for property tests
  - Set up a minimal DOM environment (jsdom) so `va_api.js` and `confirmation.js` can be imported

  - [x] 7.1 Write property test for confirmation page renders all fields (P3)
    - **Property 3: Confirmation page renders all submission fields**
    - Use `fast-check` — generate arbitrary submission objects, call `renderConfirmation`, assert output HTML contains `confirmation_number`, `submitted_at`, `veteran_name`, and each `doc.name`
    - Tag: `Feature: mock-va-portal, Property 3: confirmation page renders all submission fields`
    - Run minimum 100 examples (`numRuns: 100`)
    - **Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.7**

  - [x] 7.2 Write property test for VA branch API success path (P4)
    - **Property 4: VA branch API success path shows badge**
    - Use `fast-check` — generate mock API responses with varying branch lists; when ARMY is present, assert `#va-service-branch` shows the description and a `.va-verified-badge` element exists
    - Tag: `Feature: mock-va-portal, Property 4: VA branch API success path shows badge`
    - Run minimum 100 examples
    - **Validates: Requirements 3.2**

  - [x] 7.3 Write property test for VA branch API failure path (P5)
    - **Property 5: VA branch API failure path shows fallback without badge**
    - Use `fast-check` — generate various error conditions (TypeError, non-2xx Response); assert `#va-service-branch` shows `"Army"` and no `.va-verified-badge` is present
    - Tag: `Feature: mock-va-portal, Property 5: VA branch API failure path shows fallback`
    - Run minimum 100 examples
    - **Validates: Requirements 3.3**

- [x] 8. Checkpoint — Ensure all tests pass
  - Run `pytest mock_va_portal/tests/` and the JS test suite
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Verify responsive layout
  - Open `index.html` in a browser and resize to 1440px, 1280px, and 1024px — confirm no horizontal scrollbar
  - Resize to ≤900px — confirm two-column layout collapses to single column
  - Resize to ≤600px — confirm rating banner items stack vertically
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 10. Verify VA API integrations
  - Start `server.py` and open `index.html`
  - Confirm `#va-service-branch` shows the VA-verified description and `✓ VA Verified` badge (requires network access to VA sandbox)
  - Open `confirmation.html` with a valid `?id=` param and confirm the VA Forms API badge appears next to the NOD row
  - _Requirements: 3.1, 3.2_

- [x] 11. Verify full demo flow end-to-end
  - Start `server.py` (`python3 mock_va_portal/server.py`)
  - Open `index.html` in a browser — confirm dashboard loads with denied claims visible
  - POST a PDF to `http://localhost:5050/submit-appeal` (use curl or the VetClaim app)
  - Confirm the green notification banner appears on the dashboard within 3 seconds
  - Click "View Submission →" and confirm the confirmation page renders with the correct confirmation number, timestamp, conditions, documents table, and embedded PDF
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

- [x] 12. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Tasks 1–4 are already complete — marked `[x]`
- Python tests require `pytest` and `hypothesis`: `pip install pytest hypothesis flask flask-cors`
- JS tests require `fast-check` and a DOM environment: `npm install --save-dev vitest fast-check jsdom`
- Run Python tests with: `pytest mock_va_portal/tests/ -v`
- Run JS tests with: `npx vitest --run`
- Property tests validate universal correctness; unit tests validate specific examples and edge cases
