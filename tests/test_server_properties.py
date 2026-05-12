"""
Property-based tests for backend/server.py using Hypothesis.

Run with:
    pytest tests/test_server_properties.py
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

# Ensure project root is on sys.path so `from backend.server import app` works
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import pytest
from hypothesis import given, settings, HealthCheck
import hypothesis.strategies as st

# Import the Flask app from backend/server.py
from backend.server import app


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

def pdf_strategy():
    """Generate small synthetic PDF-like bytes with a .pdf filename."""
    return st.builds(
        lambda body: (b"%PDF-1.4\n" + body, "test_file.pdf"),
        body=st.binary(min_size=1, max_size=512),
    )


# ---------------------------------------------------------------------------
# Property 1: Upload returns a job_id for any valid file set
# ---------------------------------------------------------------------------

@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
@given(pdf_files=st.lists(pdf_strategy(), min_size=1, max_size=10))
def test_upload_returns_job_id(pdf_files):
    client = app.test_client()
    data = {}
    file_objects = []
    for i, (content, filename) in enumerate(pdf_files):
        f = io.BytesIO(content)
        file_objects.append(f)
        data.setdefault("files", [])
        data["files"].append((f, f"file_{i}.pdf"))
    response = client.post("/api/upload", data=data, content_type="multipart/form-data")
    for f in file_objects:
        f.close()
    assert response.status_code == 202
    body = response.get_json()
    assert body is not None
    assert "job_id" in body
    assert isinstance(body["job_id"], str)
    assert len(body["job_id"]) > 0


# ---------------------------------------------------------------------------
# Property 2: Empty upload is always rejected
# ---------------------------------------------------------------------------

@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
@given(empty=st.just([]))
def test_empty_upload_rejected(empty):
    client = app.test_client()
    response = client.post("/api/upload", data={}, content_type="multipart/form-data")
    assert response.status_code == 400
    body = response.get_json()
    assert body is not None
    assert "error" in body


# ---------------------------------------------------------------------------
# Property 3: Unknown job_id always returns 404
# ---------------------------------------------------------------------------

from backend.server import jobs as _jobs


@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
@given(job_id=st.text(min_size=1))
def test_unknown_job_id_returns_404(job_id):
    unknown_id = "UNKNOWN_" + job_id
    _jobs.clear()
    client = app.test_client()
    response = client.get(f"/api/result/{unknown_id}")
    assert response.status_code == 404
    body = response.get_json()
    assert body is not None
    assert "error" in body
