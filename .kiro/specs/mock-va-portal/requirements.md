# Requirements Document

## Introduction

The Mock VA Portal is a static HTML/CSS demo website for VetClaim AI (HackUSF 2026).
It simulates the VA eBenefits portal and serves as the bookends of the live demo:

1. The veteran opens the mock VA portal and sees their denied claims — establishing the problem
2. The veteran navigates to the VetClaim AI application (a separate website) where the audit
   and appeal submission happen automatically in the background
3. The veteran returns to the mock VA portal and sees a confirmation that the appeal documents
   were successfully submitted, along with an official report/confirmation number

The mock portal does NOT contain the VetClaim AI audit logic, processing screen, or results
page — those belong to the VetClaim application. The portal's only job is to make the
before-and-after story tangible for judges.

## Glossary

- **Mock_Portal**: The static HTML/CSS demo website in `mock_va_portal/`
- **Dashboard**: `index.html` — the VA eBenefits benefits summary showing denied claims
- **Confirmation_Page**: `confirmation.html` — the VA portal page showing successful appeal submission
- **VetClaim_App**: The separate VetClaim AI application website (not part of this repo)
- **Demo_Veteran**: James R. Wilson, U.S. Army, Post-9/11, Iraq 2003 (OIF), 30% combined rating, 6 conditions (4 granted, 2 denied)
- **Report_Number**: A mock VA confirmation number generated when appeal documents are received (e.g. VA-2026-NOD-048821)
- **NOD**: Notice of Disagreement — the formal appeal document submitted by VetClaim AI
- **USWDS**: U.S. Web Design System — the design language used by VA.gov
- **Disclaimer**: The required legal notice that this is a demo not affiliated with the VA

---

## Requirements

### Requirement 1: Dashboard — Denied Claims View

**User Story:** As a demo presenter, I want the VA dashboard to clearly show the veteran's denied claims, so that judges immediately understand the problem VetClaim AI solves before we switch to the app.

#### Acceptance Criteria

1. THE Dashboard SHALL display the Demo_Veteran's combined disability rating as 30% in a prominent rating banner using VA navy blue (`#112e51`) and gold (`#f9c642`) numerals.
2. THE Dashboard SHALL display the Demo_Veteran's current monthly payment as $524.31.
3. THE Dashboard SHALL display a rated conditions table with exactly 6 conditions, where the 2 denied conditions (Sleep Apnea DC 6847 and Respiratory Condition DC 6604) are visually prominent — using a red "Denied" label and a distinct row style to draw the judge's eye.
4. THE Dashboard SHALL display a callout banner above or near the denied conditions that reads: "2 of your conditions were denied. You may be eligible to appeal." with a link or button labeled "Learn about your options."
5. THE Dashboard SHALL display the Demo_Veteran's service information: U.S. Army, March 1991 – November 2003, Gulf War / Post-9/11, Iraq (OIF) 2003, Honorable discharge.
6. THE Dashboard SHALL display an appeal deadline card showing January 9, 2027 as the NOD deadline.
7. THE Dashboard SHALL display a claim documents section listing the Rating Decision Letter (Jan 9, 2026), C&P Exam Results (Dec 2025), DBQ — PTSD (Dec 2025), DBQ — TBI (Dec 2025).
8. THE Dashboard SHALL include the Disclaimer in the footer.
9. THE Dashboard SHALL NOT display any VetClaim AI branding, links, or call-to-action banners — the VA portal has no knowledge of VetClaim AI. The presenter switches to the VetClaim app manually between tabs.

---

### Requirement 2: Confirmation Page — Appeal Submitted

**User Story:** As a demo presenter, I want a VA portal confirmation page that shows the appeal documents were successfully received, so that judges see the end-to-end result of VetClaim AI's automatic submission.

#### Acceptance Criteria

1. THE Confirmation_Page SHALL display a prominent success banner with a green checkmark and the message: "Your appeal documents have been received by the VA."
2. THE Confirmation_Page SHALL display the Report_Number (VA-2026-NOD-048821) in a large, clearly readable format as the primary reference for the submission.
3. THE Confirmation_Page SHALL display a submission summary table listing the documents received: Notice of Disagreement (NOD) — 3 issues, Supporting Evidence Summary, and CFR Title 38 Legal Citations Brief.
4. THE Confirmation_Page SHALL display the submission timestamp: March 28, 2026 at 11:47 AM EST.
5. THE Confirmation_Page SHALL display the conditions under appeal: PTSD (DC 9411), Respiratory Condition/Burn Pit Exposure (DC 6604), and TBI (DC 8045).
6. THE Confirmation_Page SHALL display the next steps the VA will take: acknowledgment letter within 5 business days, assignment to a VA reviewer, and estimated decision timeline of 4–6 months.
7. THE Confirmation_Page SHALL display a "Submitted by: VetClaim AI on behalf of James R. Wilson" attribution line to make clear the app did this automatically.
8. THE Confirmation_Page SHALL include a link back to the Dashboard labeled "← Return to My Benefits."
9. THE Confirmation_Page SHALL include the Disclaimer in the footer.

---

### Requirement 3: VA API Integration — Service Branch Verification

**User Story:** As a demo presenter, I want the portal to make a live call to the VA Benefits Reference Data API, so that judges see VetClaim AI connecting to real VA data infrastructure.

#### Acceptance Criteria

1. THE Dashboard SHALL call the VA Benefits Reference Data API `/service-branches` endpoint on page load to verify the Demo_Veteran's branch code ("ARMY").
2. WHEN the API call succeeds, THE Dashboard SHALL display the VA-verified branch description ("Army") with a green "✓ VA Verified" badge next to it in the Service Information section.
3. WHEN the API call fails or times out, THE Dashboard SHALL fall back to displaying "Army" without the badge, so the demo continues without interruption.
4. THE API key SHALL be injected via a `<meta name="va-api-key">` tag in the HTML, not hardcoded in JavaScript source.
5. THE `va_api.js` file SHALL include comments explaining why the API is being called and what the fallback behavior is.

---

### Requirement 4: Visual Fidelity to VA.gov Design System

**User Story:** As a demo presenter, I want both portal pages to look like the real VA.gov, so that judges immediately recognize the context.

#### Acceptance Criteria

1. THE Mock_Portal SHALL use VA navy blue `#112e51` for all headers and navigation backgrounds.
2. THE Mock_Portal SHALL display the U.S. government banner on every page.
3. THE Mock_Portal SHALL use Source Sans Pro (Helvetica Neue, Arial as fallbacks) across all pages.
4. THE Mock_Portal SHALL use `#005ea2` for all hyperlinks.
5. THE Mock_Portal SHALL use `#2e8540` for granted/success states and `#b50909` for denied/error states.
6. THE Mock_Portal SHALL display "Signed in as James R. Wilson" in the nav on both pages.

---

### Requirement 5: Demo Navigation Flow

**User Story:** As a demo presenter, I want a clear navigation path that matches the demo story, so that I don't click the wrong thing under pressure.

#### Acceptance Criteria

1. THE demo flow SHALL be: Dashboard (`index.html`) → [presenter switches to VetClaim_App] → Confirmation_Page (`confirmation.html`).
2. THE Confirmation_Page SHALL provide a "← Return to My Benefits" link back to `index.html` to allow the presenter to loop the demo.
3. ALL external-looking links on both pages SHALL use `href="#"` so no click navigates away from the demo unexpectedly.
4. THE Dashboard SHALL NOT auto-navigate or link directly to `confirmation.html` — the switch to VetClaim_App and back is a manual presenter action.

---

### Requirement 6: Shared Stylesheet and Offline Operation

**User Story:** As a developer, I want the portal to work fully offline with a single CSS file, so that demo environment issues (no WiFi, blocked CDNs) don't break the presentation.

#### Acceptance Criteria

1. THE Mock_Portal SHALL use a single `style.css` file linked from all pages.
2. THE Mock_Portal SHALL NOT depend on any external CSS frameworks or CDN-hosted resources for layout or styling.
3. THE Mock_Portal SHALL function correctly when opened directly from the filesystem (no local server required) with the exception of the VA API call, which requires network access.

---

### Requirement 7: Responsiveness

**User Story:** As a demo presenter, I want the portal to display correctly on a laptop and projected display.

#### Acceptance Criteria

1. THE Mock_Portal SHALL render without horizontal scrolling at 1024px, 1280px, and 1440px viewport widths.
2. WHEN viewport is 900px or less, THE Mock_Portal SHALL collapse two-column layouts to single column.
3. WHEN viewport is 600px or less, THE Mock_Portal SHALL stack the rating banner items vertically.

---

### Requirement 8: Legal Disclaimer

**User Story:** As a hackathon team, I want a disclaimer on every page so judges know this is a demo.

#### Acceptance Criteria

1. THE Mock_Portal SHALL display in the footer of every page: "Demo mock portal — VetClaim AI HackUSF 2026. Not affiliated with the U.S. Department of Veterans Affairs."
2. THE footer disclaimer SHALL be visually subdued (small font, muted color) so it doesn't distract from the demo content.
