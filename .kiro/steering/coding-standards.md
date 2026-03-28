---
inclusion: always
---

# VetClaim AI — Coding Standards

This is a hackathon project with developers of varying experience levels.
Prioritize clarity and readability over cleverness.

## General Rules
- Write comments that explain WHY, not just what the code does
- Keep functions small and single-purpose — one job per function
- Use descriptive variable names (no single-letter names outside of loops)
- Prefer explicit over implicit — don't rely on magic or hidden behavior
- If something is a workaround or a known limitation, leave a comment saying so

## Python Style
- Follow PEP 8 (4-space indentation, snake_case for variables/functions, PascalCase for classes)
- Use type hints on all function signatures — helps teammates understand data flow at a glance
- Use Pydantic models for any structured data passed between agents (see Data Models below)
- Use f-strings for string formatting
- Keep imports at the top of each file, grouped: stdlib → third-party → local

## Example: well-commented tool function
```python
def cfr_lookup(diagnostic_code: str) -> dict:
    """
    Look up a VA diagnostic code in CFR Title 38 Part 4.

    The CFR (Code of Federal Regulations) Title 38 Part 4 defines the exact
    symptom criteria required for each rating level (0%, 10%, 20%, etc.).
    We use a bundled JSON file so the LLM cannot hallucinate rating thresholds —
    all numeric values come from this authoritative source.

    Args:
        diagnostic_code: e.g. "8045" (TBI) or "9411" (PTSD)

    Returns:
        dict with keys: condition_name, cfr_section, rating_criteria
        Returns an error dict if the code is not found.
    """
    data = load_cfr_data()  # loads cfr38_part4.json once and caches it

    if diagnostic_code not in data:
        # Unknown codes should be surfaced to the user, not silently ignored.
        # Veterans should request their full C-file to find the correct code.
        return {
            "error": f"Diagnostic code {diagnostic_code} not found in reference data.",
            "action": "Request your full C-file from the VA to verify this code."
        }

    return data[diagnostic_code]
```

## Pydantic Data Models
Define shared data shapes in a central `models.py` so every agent uses the same structure.

```python
from pydantic import BaseModel
from typing import Optional

class Condition(BaseModel):
    condition_name: str
    diagnostic_code: str
    rating_assigned: int          # percentage, e.g. 30
    denial_reason: Optional[str]  # None if service connection was granted
    exam_date: Optional[str]      # ISO date string, e.g. "2024-03-15"

class Flag(BaseModel):
    condition: str
    flag_type: str                # UNDER_RATED | WRONG_CODE | MISSING_NEXUS | TDIU_ELIGIBLE | PACT_ACT
    current_rating: int
    potential_rating: int
    cfr_section: str              # e.g. "38 CFR § 4.130, DC 9411"
    legal_basis: str              # plain-English explanation of the legal argument
    confidence_score: float       # 0.0–1.0, set by the Advocate Agent
```

## ADK Agent Instructions
- Write agent `instruction` strings as clear, numbered steps
- Tell the agent exactly what keys to read from session state and what keys to write
- Never ask the agent to invent or estimate numeric values — always use a tool call for numbers
- End every agent instruction with the expected output format

```python
# Good — explicit, numbered, tells the agent exactly what to do
instruction="""
You are auditing a VA disability claim for rating errors.

Steps:
1. Read the list of conditions from session.state['parsed_claim']['conditions']
2. For each condition, call cfr_lookup_tool with the diagnostic_code
3. Compare the rating_assigned to the symptom criteria returned
4. If the veteran's documented symptoms match a HIGHER rating level, flag as UNDER_RATED
5. Call pact_act_tool for each condition to check presumptive eligibility
6. Call tdiu_check_tool once with the full list of ratings

Write your results to session.state['flag_table'] as a list of Flag objects.
"""
```

## Error Handling
- Always handle the case where a tool returns an error dict — don't let it crash the pipeline
- Surface errors to the user with a helpful message, not a raw stack trace
- Use try/except around file I/O and API calls; log the error and continue where possible

```python
result = cfr_lookup(code)
if "error" in result:
    print(f"⚠️  {result['error']}")
    print(f"   Suggestion: {result['action']}")
    continue  # skip this condition and process the rest
```

## Environment & Secrets
- All API keys go in `.env` — never hardcode them
- Load with `python-dotenv`: `from dotenv import load_dotenv; load_dotenv()`
- `.env` is in `.gitignore` — never commit it
- Use `os.getenv("GOOGLE_API_KEY")` to access keys

## What NOT to Do
- Don't add features not in the PRD — scope creep kills hackathon projects
- Don't use async/await unless you have a specific reason — keep it synchronous for readability
- Don't store PII (veteran names, claim numbers) to disk — session memory only
- Don't claim the output is legal advice — always include the disclaimer
