---
inclusion: manual
---

# VetClaim AI — Architecture & Agent Design

## Stack
- Python 3.11+
- Google ADK 1.27 — agent orchestration (SequentialAgent, LoopAgent, LlmAgent)
- Gemini 3 Flash — primary LLM (vision + text); Gemini 2.5 Flash as fallback
- ReportLab — PDF generation for the NOD appeal letter
- python-dotenv — environment variable management
- Pydantic — data validation for structured agent outputs

## Project Structure
```
vetclaim/
├── agents/
│   ├── parser_agent.py        # Extracts structured data from uploaded VA documents
│   ├── auditor_agent.py       # Looks up CFR codes and builds the flag table
│   ├── advocate_agent.py      # Challenges auditor flags for legal defensibility
│   └── negotiation_agent.py   # Drafts the NOD letter, phone script, and summary
├── tools/
│   ├── cfr_lookup.py          # Looks up a diagnostic code in cfr38_part4.json
│   ├── pact_act_check.py      # Checks PACT Act presumptive eligibility
│   ├── tdiu_check.py          # Calculates TDIU eligibility per CFR §4.16
│   ├── va_pay_lookup.py       # Returns monthly pay from 2026 rate table
│   └── pdf_generator.py       # Generates the final PDF output via ReportLab
├── data/
│   ├── cfr38_part4.json             # Diagnostic codes + rating criteria
│   ├── pact_act_conditions.json     # Presumptive conditions by era/exposure
│   ├── va_pay_rates_2026.json       # Monthly pay by rating + dependents
│   └── combined_ratings_table.json  # VA whole-person combined rating math
├── templates/
│   └── nod_letter.html        # Jinja2 template (used in v1.0, not hackathon)
├── main.py                    # CLI entry point — start here
├── orchestrator.py            # Wires all agents together into the pipeline
└── .env                       # API keys — never commit this file
```

## Agent Pipeline (in execution order)

### 1. Parser Agent (`agents/parser_agent.py`)
- Input: file path to a PDF or image
- Uses Gemini 3 Flash multimodal (vision) to read the document
- Output (session state key `parsed_claim`): structured JSON with:
  - veteran_name, claim_number, service_era
  - conditions: list of {condition_name, diagnostic_code, rating_assigned, denial_reason, exam_date}
  - combined_rating

### 2. Auditor Agent (`agents/auditor_agent.py`)
- Input: `parsed_claim` from session state
- Calls cfr_lookup_tool, pact_act_tool, tdiu_check_tool for each condition
- Output (session state key `flag_table`): list of flags, each with:
  - condition, flag_type, current_rating, potential_rating, cfr_section, legal_basis, confidence_score
- Flag types: UNDER_RATED | WRONG_CODE | MISSING_NEXUS | TDIU_ELIGIBLE | PACT_ACT

### 3. Advocate Agent (`agents/advocate_agent.py`) — runs inside a LoopAgent
- Input: `flag_table` from session state
- Challenges each flag: Is the CFR citation accurate? Is the argument legally defensible?
- Output (session state key `validated_flags`): same structure as flag_table + confidence_score per flag
- Loop runs max 3 iterations. If no consensus, Auditor's flags are canonical.

### 4. Negotiation Agent (`agents/negotiation_agent.py`)
- Input: `validated_flags` from session state
- Calls va_pay_lookup_tool and generate_pdf_tool
- Output: NOD appeal letter PDF + phone script text + benefits summary card

## Orchestrator (`orchestrator.py`)
```python
# The SequentialAgent runs agents in order: parser → debate_loop → negotiator
# The LoopAgent runs auditor + advocate back and forth (max 3 rounds)
orchestrator = SequentialAgent(
    name="vetclaim_orchestrator",
    agents=[parser_agent, debate_loop, negotiation_agent],
)
```

## Session State Keys
All agents communicate through ADK session state — treat it like a shared dictionary.

| Key               | Set by          | Read by                      |
|-------------------|-----------------|------------------------------|
| `parsed_claim`    | parser_agent    | auditor_agent                |
| `flag_table`      | auditor_agent   | advocate_agent               |
| `validated_flags` | advocate_agent  | negotiation_agent            |
| `final_output`    | negotiation_agent | main.py (display + download) |

## Model Usage
- Use `gemini-3-flash` for all agents (best accuracy for document extraction)
- Fall back to `gemini-2.5-flash` only if quota is exceeded
- Do NOT use `gemini-2.0-flash` — it is being retired June 2026
