---
inclusion: always
---

# VetClaim AI — Project Overview

VetClaim AI is an AI-powered VA disability claims auditor built for HackUSF 2026.
It reads VA Rating Decision Letters, C&P Exams, and DBQs, then flags errors,
missing benefits, and PACT Act eligibility — and generates a formal appeal letter.

## The One-Line Pitch
"77% of VA claims are denied on first submission. VetClaim AI audits your claim
in 60 seconds and generates your appeal letter."

## What the App Does (in order)
1. Veteran uploads a VA document (PDF or image)
2. Parser Agent extracts conditions, diagnostic codes, ratings, and denial reasons
3. Auditor Agent cross-references each code against CFR Title 38 Part 4 and flags issues
4. Advocate Agent challenges the Auditor's flags in a debate loop (max 3 rounds)
5. Negotiation Agent drafts a Notice of Disagreement (NOD) appeal letter + phone script + benefits summary

## Key Output
- Formal NOD appeal letter (PDF) with CFR Title 38 legal citations
- VA phone call script with specific questions per flagged issue
- Benefits summary card: current rating vs. potential rating, monthly pay difference

## Audience
This is a hackathon project. Code should be:
- Well commented — explain the "why", not just the "what"
- Readable by developers of all experience levels
- Modular — each agent and tool lives in its own file
- Minimal — no over-engineering; get it working first

## Disclaimer (include on all outputs)
"This tool is informational only and does not constitute legal advice.
Always consult a VSO or VA-accredited attorney before filing."
