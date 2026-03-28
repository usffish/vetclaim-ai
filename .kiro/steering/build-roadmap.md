---
inclusion: manual
---

# VetClaim AI — 24-Hour Build Roadmap

This is the execution plan for the hackathon. Work in phases, in order.
Each phase has a clear deliverable — don't move to the next phase until
the current one works end-to-end, even if it's rough.

## Phase 0 — Setup (Hours 0–2)
Goal: Everyone can run the project locally before writing any feature code.

Tasks:
- [ ] Create the project folder structure (see architecture.md)
- [ ] Set up `.env` with `GOOGLE_API_KEY` and `ELEVENLABS_API_KEY`
- [ ] Run `pip install google-adk google-generativeai reportlab pydantic python-dotenv elevenlabs`
- [ ] Verify `adk web` starts at http://localhost:8000
- [ ] Add `.env` and `__pycache__/` to `.gitignore`
- [ ] Create stub files for all agents and tools (empty functions with docstrings)
- [ ] Commit: "chore: project scaffold"

Tip: Use the stub files to unblock teammates — they can start reading/writing
their module even before the data files are ready.

---

## Phase 1 — Parser Agent (Hours 2–7)
Goal: Upload a real VA PDF → get structured JSON out.

Owner suggestion: strongest Python/API developer on the team.

Tasks:
- [ ] Implement `tools/read_document_tool` — load PDF/image bytes, send to Gemini 3 Flash vision
- [ ] Write the parser_agent instruction (see architecture.md for expected output shape)
- [ ] Validate output against the `ParsedClaim` Pydantic model in `models.py`
- [ ] Test with `sample_rating_decision.pdf` — print the JSON to terminal
- [ ] Handle the fallback: if Gemini can't extract a field, return `null` (don't crash)
- [ ] Commit: "feat: parser agent — document ingestion"

Definition of done: Running `python main.py --claim sample.pdf` prints a valid
JSON object with at least: veteran_name, conditions list, combined_rating.

---

## Phase 2 — Auditor Agent + Data Files (Hours 7–12)
Goal: For each condition in the parsed claim, look up the CFR code and produce a flag table.

Owner suggestion: split into two parallel tracks:
- Track A: Build the data files (`data/cfr38_part4.json`, `data/pact_act_conditions.json`)
- Track B: Build the auditor agent and tool functions

### Track A — Data Files
- [ ] `data/cfr38_part4.json` — seed with at least 20 common diagnostic codes:
      PTSD (9411), TBI (8045), lumbar strain (5237), tinnitus (6260),
      hearing loss (6100), sleep apnea (6847), knee (5257/5258/5259),
      hypertension (7101), diabetes (7913), depression (9434)
      Format: `{ "9411": { "condition_name": "PTSD", "cfr_section": "38 CFR § 4.130", "rating_criteria": { "100": "...", "70": "...", ... } } }`
- [ ] `data/pact_act_conditions.json` — seed with burn pit, Agent Orange, Camp Lejeune conditions
- [ ] `data/va_pay_rates_2026.json` — monthly pay by rating (0–100%) and dependent count
- [ ] `data/combined_ratings_table.json` — VA whole-person combined rating lookup table

### Track B — Auditor Agent
- [ ] Implement `tools/cfr_lookup.py` — dict lookup against cfr38_part4.json
- [ ] Implement `tools/pact_act_check.py` — rule-based lookup against pact_act_conditions.json
- [ ] Implement `tools/tdiu_check.py` — CFR §4.16 threshold: 60%+ combined OR single 40%+ condition
- [ ] Write auditor_agent instruction with flag logic
- [ ] Validate output against the `Flag` Pydantic model
- [ ] Commit: "feat: auditor agent + CFR data files"

Definition of done: Auditor produces a flag_table with at least one flag
for the sample claim, with a valid cfr_section citation.

---

## Phase 3 — Advocate Agent + Debate Loop (Hours 12–15)
Goal: Advocate challenges the auditor's flags; loop runs max 3 rounds.

Tasks:
- [ ] Implement `agents/advocate_agent.py` — reviews flag_table, challenges weak citations
- [ ] Wire up `LoopAgent(agents=[auditor_agent, advocate_agent], max_iterations=3)` in orchestrator.py
- [ ] Advocate outputs `validated_flags` with a `confidence_score` (0.0–1.0) per flag
- [ ] If loop ends without consensus, fall back to auditor's flags (log a warning)
- [ ] Test the loop — watch it run 3 rounds in `adk web`
- [ ] Commit: "feat: advocate agent + debate loop"

Definition of done: `adk web` shows the auditor and advocate exchanging
flag assessments across multiple rounds before producing validated_flags.

---

## Phase 4 — PACT Act + TDIU + Pay Lookup (Hours 15–18)
Goal: Surface the benefits veterans don't know they qualify for.

Tasks:
- [ ] Verify `pact_act_check` correctly flags burn pit / Agent Orange / Camp Lejeune conditions
- [ ] Verify `tdiu_check` correctly identifies TDIU eligibility at 60%+ combined or 40%+ single
- [ ] Implement `tools/va_pay_lookup.py` — returns current and potential monthly pay
- [ ] Calculate `annual_pay_difference` = (potential_monthly - current_monthly) * 12
- [ ] This is the headline demo number — make sure it's accurate
- [ ] Commit: "feat: PACT Act scanner + TDIU + pay lookup"

Definition of done: For the demo veteran (30% → 90% scenario), the tool
correctly outputs the monthly and annual pay difference using 2026 rates.

---

## Phase 5 — Negotiation Agent + PDF Output (Hours 18–21)
Goal: Generate the NOD appeal letter, phone script, and benefits summary card as a PDF.

Tasks:
- [ ] Implement `agents/negotiation_agent.py` — drafts NOD letter text using validated_flags
- [ ] NOD letter must include: date, VA regional office address placeholder, veteran info,
      itemized flag table, CFR citations per flag, PACT Act citations where applicable,
      and the legal disclaimer
- [ ] Implement `tools/pdf_generator.py` using ReportLab — letter + phone script + summary card
- [ ] Phone script: opening statement + one specific question per flagged condition
- [ ] Benefits summary card: current rating, potential rating, current pay, potential pay, annual difference
- [ ] Commit: "feat: negotiation agent + PDF generation"

Definition of done: Running the full pipeline produces a downloadable PDF
with the NOD letter, phone script, and benefits summary on separate pages.

---

## Phase 6 — Demo Polish + ElevenLabs Voice (Hours 21–24)
Goal: The demo works flawlessly with 3 real document types, and the debate loop has voice.

ElevenLabs is a prize category — treat this as a required deliverable, not optional.
The Auditor/Advocate debate is the technical centerpiece of the demo. Giving each agent
a distinct voice makes the multi-agent architecture immediately tangible to judges.

### ElevenLabs Integration Tasks
- [ ] Create two ElevenLabs voices (free tier supports this):
      - Auditor: calm, measured, analytical (e.g. "Adam" or "Antoni")
      - Advocate: assertive, confident, slightly combative (e.g. "Arnold" or "Daniel")
- [ ] Implement `tools/voice_output.py`:

```python
from elevenlabs import ElevenLabs, VoiceSettings
import os

# Initialize the client once — reuse across calls
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

# Voice IDs from your ElevenLabs dashboard
AUDITOR_VOICE_ID = "your_auditor_voice_id"
ADVOCATE_VOICE_ID = "your_advocate_voice_id"

def speak(text: str, voice_id: str, output_path: str) -> str:
    """
    Convert text to speech using ElevenLabs and save to a file.
    Called after each agent turn in the debate loop so judges can
    hear the Auditor and Advocate arguing in real time.

    Args:
        text: The agent's output text to speak
        voice_id: ElevenLabs voice ID for this agent
        output_path: Where to save the .mp3 file

    Returns:
        Path to the generated audio file
    """
    audio = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id="eleven_turbo_v2",  # fastest model — important for live demo
        voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.75),
    )
    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    return output_path
```

- [ ] Hook `speak()` into the debate loop in `orchestrator.py` — call after each agent turn
- [ ] Auto-play the audio file after generation (use `subprocess` to call `afplay` on Mac / `aplay` on Linux)
- [ ] For the final NOD letter summary, have the Negotiation Agent read the benefits card aloud
      ("Your potential new rating is 90%. That is $2,241 more per month — for life.")
- [ ] Test the full audio flow end-to-end before the demo

### Other Polish Tasks
- [ ] Test with 3 document formats: Rating Decision Letter, C&P Exam, DBQ
- [ ] Fix any extraction edge cases from real documents
- [ ] Clean up terminal output — make it readable for the live demo
- [ ] Rehearse the 3-minute pitch with the actual demo flow
- [ ] Commit: "feat: ElevenLabs voice layer + demo polish"

## The Demo Script (memorize this)
1. Drop in a real VA Rating Decision Letter
2. Show the terminal running — parser → auditor → advocate debate → negotiation
3. Open the PDF: "Your current rating is 30%. We found 3 issues."
4. Show the benefits summary card: "Potential new rating: 90%. That's $2,241 more per month — for life."
5. Show the first page of the NOD letter with CFR citations
6. If ElevenLabs is wired up, play the auditor/advocate debate audio

---

## If You're Running Behind
Cut in this order — keep the core demo intact:
1. Cut the Jinja2 HTML template (use plain ReportLab text layout)
2. Cut the phone script (keep NOD letter + summary card)
3. Cut the debate loop to 1 iteration (still shows multi-agent architecture)
4. Do NOT cut ElevenLabs — it's a prize category and takes ~1 hour to wire up
5. Never cut: parser → auditor → PDF output — that IS the demo

## Prize Checklist
- [ ] Google ADK prize: uses SequentialAgent + LoopAgent + at least 2 LlmAgents with A2A communication
- [ ] Oracle prize: clear human impact story in the pitch — lead with the veteran persona
- [ ] ElevenLabs prize: Auditor and Advocate have distinct voices; Negotiation Agent reads the benefits card aloud
- [ ] Best Overall: technical depth + emotional demo + clean PDF output

## Why Not Solana or Snowflake
- Solana: no payment, token, or on-chain verification use case — would feel forced
- Snowflake: data warehouse with no persistent storage in v1 — adds setup cost, zero user benefit
- ElevenLabs is the right call: it directly serves the demo and targets a real prize
