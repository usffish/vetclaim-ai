"""
VetClaim Backend Server — Flask API on port 5001.

Routes:
  POST /api/upload          — accept PDFs, start pipeline, return job_id
  GET  /api/stream/<job_id> — SSE stream of pipeline progress
  GET  /api/result/<job_id> — return completed audit JSON
  GET  /api/download        — serve a filled PDF by ?path= query param
  GET  /api/status          — health check
"""

from __future__ import annotations

import sys

# ---------------------------------------------------------------------------
# Python version guard — google-adk requires 3.13+.
# If launched by Anaconda or any older interpreter, re-exec using the venv.
# ---------------------------------------------------------------------------
if sys.version_info < (3, 13):
    import os as _os
    from pathlib import Path as _Path
    _root = _Path(__file__).resolve().parent.parent
    _venv_py = _root / "venv" / "bin" / "python3"          # macOS / Linux
    if not _venv_py.exists():
        _venv_py = _root / "venv" / "Scripts" / "python.exe"  # Windows
    if _venv_py.exists():
        _os.execv(str(_venv_py), [str(_venv_py)] + sys.argv)
    else:
        sys.exit(
            f"ERROR: Python {sys.version} is too old (need 3.13+) and no venv "
            f"found at {_root / 'venv'}.\n"
            "Run: python3.13 -m venv venv && venv/bin/pip install -r requirements.txt"
        )

import json
import os
import queue
import tempfile
import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

# ---------------------------------------------------------------------------
# sys.path — ensure project root is importable so agent modules resolve
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
# Also insert backend dir so `from schemas import ...` works inside agents
_BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_BACKEND_DIR))

from flask import Flask, Response, jsonify, request, send_file, abort
from flask_cors import CORS
from werkzeug.utils import secure_filename

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__)

# Allow CORS origins from env (comma-separated) or fall back to localhost dev default
_CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")]
CORS(app, origins=_CORS_ORIGINS)

_OUTPUT_DIR = _BACKEND_DIR / "output"
_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
_JOB_TTL_SECONDS = 60 * 60  # evict completed/errored jobs after 1 hour

# ---------------------------------------------------------------------------
# Job store
# ---------------------------------------------------------------------------

import time as _time

@dataclass
class JobRecord:
    job_id: str
    status: Literal["running", "complete", "error"]
    upload_dir: Path
    result: dict | None = None
    error: str | None = None
    events: queue.Queue = field(default_factory=queue.Queue)
    created_at: float = field(default_factory=_time.time)


jobs: dict[str, JobRecord] = {}


def _evict_old_jobs() -> None:
    """Remove completed/errored jobs older than TTL to prevent unbounded memory growth."""
    cutoff = _time.time() - _JOB_TTL_SECONDS
    to_delete = [
        jid for jid, job in jobs.items()
        if job.status in ("complete", "error") and job.created_at < cutoff
    ]
    for jid in to_delete:
        jobs.pop(jid, None)

# ---------------------------------------------------------------------------
# Pipeline thread
# ---------------------------------------------------------------------------

def _run_pipeline(job: JobRecord) -> None:
    """Background thread: parse → audit → fill forms, emitting SSE events."""

    def emit(step: str, status: str) -> None:
        payload = json.dumps({"step": step, "status": status})
        job.events.put(payload)

    try:
        # Step 1 — Parse documents
        emit("parsing_documents", "Parsing uploaded documents...")
        from agents.parser_agent import VAClaimParser
        parser = VAClaimParser(pdf_dir=str(job.upload_dir))
        parsed_claim = parser.extract_all()

        # Step 2 — Run audit (LLM + rule-based)
        emit("running_audit", "Running AI audit on your claim...")
        from agents.auditor_agent import run_full_audit
        result = run_full_audit(parsed_claim)

        # Step 3 — Form filling happens inside run_full_audit; emit milestone
        emit("filling_forms", "Filling VA forms...")

        # Step 4 — Complete
        job.result = result
        job.status = "complete"
        emit("complete", "Audit complete. Redirecting to results...")

    except Exception as exc:  # noqa: BLE001
        job.status = "error"
        job.error = str(exc)
        payload = json.dumps({"step": "error", "status": f"Pipeline error: {exc}"})
        job.events.put(payload)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/api/upload", methods=["POST"])
def upload():
    """Accept PDF files, start pipeline, return job_id with 202."""
    files = request.files.getlist("files")

    if not files or all(f.filename == "" for f in files):
        return jsonify({"error": "No files provided"}), 400

    # Validate sizes before saving anything
    for f in files:
        f.stream.seek(0, 2)  # seek to end
        size = f.stream.tell()
        f.stream.seek(0)     # reset
        if size > _MAX_FILE_SIZE:
            return jsonify({"error": "File too large"}), 413

    # Create per-job temp directory
    job_id = str(uuid.uuid4())
    upload_dir = Path(tempfile.mkdtemp(prefix=f"vetclaim_{job_id}_"))

    # Save only PDF files
    saved = 0
    for f in files:
        if f.filename and f.filename.lower().endswith(".pdf"):
            filename = secure_filename(f.filename)
            f.save(str(upload_dir / filename))
            saved += 1

    if saved == 0:
        return jsonify({"error": "No valid PDF files provided"}), 400

    # Evict stale jobs before adding a new one
    _evict_old_jobs()

    # Create job record and start pipeline thread
    job = JobRecord(job_id=job_id, status="running", upload_dir=upload_dir)
    jobs[job_id] = job

    thread = threading.Thread(target=_run_pipeline, args=(job,), daemon=True)
    thread.start()

    return jsonify({"job_id": job_id}), 202


@app.route("/api/stream/<job_id>", methods=["GET"])
def stream(job_id: str):
    """SSE stream of pipeline progress for a given job."""
    job = jobs.get(job_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404

    def generate():
        while True:
            try:
                payload = job.events.get(timeout=30)
                yield f"data: {payload}\n\n"
                data = json.loads(payload)
                if data.get("step") in ("complete", "error"):
                    break
            except queue.Empty:
                # Send a keep-alive comment so the connection stays open
                yield ": keep-alive\n\n"
                # If job is done but queue is empty, close
                if job.status in ("complete", "error"):
                    break

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/api/result/<job_id>", methods=["GET"])
def result(job_id: str):
    """Return audit result JSON, or 202 if still running, or 404 if unknown."""
    job = jobs.get(job_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404

    if job.status == "running":
        return jsonify({"status": "processing"}), 202

    if job.status == "error":
        return jsonify({"error": job.error or "Pipeline failed"}), 500

    return jsonify(job.result), 200


@app.route("/api/download", methods=["GET"])
def download():
    """Serve a filled PDF by ?path= query param; reject path traversal."""
    file_path = request.args.get("path", "")
    if not file_path:
        abort(400)

    abs_path = os.path.realpath(file_path)
    output_dir = os.path.realpath(str(_OUTPUT_DIR))

    if not abs_path.startswith(output_dir + os.sep) and abs_path != output_dir:
        abort(403)

    if not os.path.isfile(abs_path):
        abort(404)

    return send_file(abs_path, as_attachment=True, download_name=os.path.basename(abs_path))


@app.route("/api/submit-appeal", methods=["POST"])
def submit_appeal():
    """Forward the first filled PDF for a completed job to the mock VA portal."""
    import requests as _req

    data = request.get_json(force=True, silent=True) or {}
    job_id = data.get("job_id")
    if not job_id:
        return jsonify({"error": "job_id required"}), 400

    job = jobs.get(job_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404
    if job.status != "complete" or job.result is None:
        return jsonify({"error": "Job not yet complete"}), 409

    result = job.result
    audit_result = result.get("audit_result", {})
    va_form_links = result.get("va_form_links", [])

    if not va_form_links:
        return jsonify({"error": "No filled forms available to submit"}), 400

    veteran_name = audit_result.get("veteran_name", "Unknown Veteran")
    conditions = ", ".join(
        f"{f.get('condition_name', '')} (DC {f.get('diagnostic_code', '')})"
        for f in audit_result.get("flags", [])
        if isinstance(f, dict) and f.get("condition_name")
    )[:300] or "Service-connected conditions"

    filled_path = va_form_links[0]["filled_path"]
    if not os.path.isfile(filled_path):
        return jsonify({"error": "Filled PDF file not found on disk"}), 500

    # Pass all form numbers so the VA portal can build the correct documents list
    form_numbers = ",".join(link["form_number"] for link in va_form_links)

    try:
        with open(filled_path, "rb") as pdf_fp:
            portal_resp = _req.post(
                "http://localhost:5050/submit-appeal",
                files={"file": (os.path.basename(filled_path), pdf_fp, "application/pdf")},
                data={
                    "veteran_name": veteran_name,
                    "conditions": conditions,
                    "forms": form_numbers,
                },
                timeout=30,
            )
        if portal_resp.ok:
            return jsonify(portal_resp.json()), 201
        return jsonify({"error": f"VA portal returned {portal_resp.status_code}"}), 502
    except Exception as exc:
        return jsonify({"error": f"Could not reach VA portal: {exc}"}), 502


@app.route("/api/start-va-call", methods=["POST"])
def start_va_call():
    """Initiate a Vapi outbound call to the veteran's phone.

    Requires VAPI_API_KEY and VAPI_PHONE_NUMBER_ID in .env.
    The call reads a consent disclosure then connects to the VA on the veteran's behalf.
    """
    import requests as _req

    vapi_key = os.getenv("VAPI_API_KEY", "").strip()
    phone_number_id = os.getenv("VAPI_PHONE_NUMBER_ID", "").strip()

    if not vapi_key or not phone_number_id:
        return jsonify({"error": "VAPI_API_KEY and VAPI_PHONE_NUMBER_ID must be set in .env"}), 503

    data = request.get_json(force=True, silent=True) or {}
    customer_number = data.get("customer_number", "").strip()
    if not customer_number:
        return jsonify({"error": "customer_number is required"}), 400

    full_name   = data.get("full_name", "Veteran")
    last_four   = data.get("last_four_ssn", "")
    claim_date  = data.get("claim_date", "")
    claim_type  = data.get("claim_type", "disability")

    system_prompt = (
        f"You are a VA claims assistant calling on behalf of {full_name}. "
        f"You are calling the VA benefits line (1-800-827-1000) to request a status update "
        f"on their {claim_type} claim"
        + (f" submitted on {claim_date}" if claim_date else "") + ". "
        f"The veteran's last four SSN digits are {last_four}. "
        "First read the consent disclosure: 'This call may be recorded for documentation purposes. "
        "By staying on the line you consent to this recording.' "
        "Then proceed to request the claim status update."
    )

    payload = {
        "phoneNumberId": phone_number_id,
        "customer": {"number": customer_number},
        "assistant": {
            "model": {
                "provider": "google",
                "model": "gemini-2.0-flash",
                "messages": [{"role": "system", "content": system_prompt}],
            },
            "voice": {"provider": "playht", "voiceId": "jennifer"},
            "firstMessage": (
                f"Hello, this is an AI assistant calling on behalf of {full_name} "
                "regarding a VA disability claim. "
                "This call may be recorded for documentation purposes. "
                "By staying on the line you consent to this recording. "
                "I'll now connect to the VA benefits line to request a status update."
            ),
        },
    }

    try:
        resp = _req.post(
            "https://api.vapi.ai/call/phone",
            json=payload,
            headers={"Authorization": f"Bearer {vapi_key}"},
            timeout=15,
        )
        if resp.ok:
            return jsonify({"call_id": resp.json().get("id"), "status": "initiated"}), 201
        return jsonify({"error": f"Vapi returned {resp.status_code}: {resp.text[:200]}"}), 502
    except Exception as exc:
        return jsonify({"error": f"Could not reach Vapi: {exc}"}), 502


@app.route("/calls/<call_id>", methods=["GET"])
def get_call(call_id: str):
    """Proxy a call record lookup from Vapi."""
    import requests as _req

    vapi_key = os.getenv("VAPI_API_KEY", "").strip()
    if not vapi_key:
        return jsonify({"error": "VAPI_API_KEY not set"}), 503

    try:
        resp = _req.get(
            f"https://api.vapi.ai/call/{call_id}",
            headers={"Authorization": f"Bearer {vapi_key}"},
            timeout=10,
        )
        if resp.ok:
            return jsonify(resp.json()), 200
        return jsonify({"error": f"Vapi returned {resp.status_code}"}), 502
    except Exception as exc:
        return jsonify({"error": f"Could not reach Vapi: {exc}"}), 502


@app.route("/api/status", methods=["GET"])
def status():
    """Health check endpoint."""
    return jsonify({"status": "OK", "service": "VetClaim Backend"}), 200


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5001)
