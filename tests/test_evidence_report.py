from pathlib import Path

import pytest

from scripts.build_evidence_report import local_path, render_report


def manifest(**changes):
    return {
        "schema_version": 1, "title": '<img src="https://bad.test/a" onerror="alert(1)">',
        "summary": "Synthetic verification only", "generated_at": "2026-09-15T00:00:00Z",
        "starting_revision": "fixture", "revision": "fixture", "runtime": "fixture",
        "readiness": [{"name": "Engineering", "status": "NOT_RUN", "detail": "Unverified"}],
        "checks": [{"id": "A23", "requirement": "Escape HTML", "status": "NOT_RUN"}],
        **changes,
    }


def test_report_escapes_all_external_text_and_embeds_local_documents(tmp_path):
    raw = '</pre><script src="https://bad.test/a"></script>'
    (tmp_path / "record.md").write_text(raw, encoding="utf-8")
    report = render_report(manifest(documents=["record.md"], limitations=[raw]), tmp_path)
    assert '<script' not in report
    assert '<img src="https:' not in report
    assert '&lt;script src=' in report
    assert 'href="#document-1"' in report
    assert "default-src 'none'" in report
    assert 'NOT_RUN' in report
    assert 'class="badge pass"' not in report


@pytest.mark.parametrize("name", ["../outside.md", "https://bad.test/a", "C:/secret.txt", "/secret.txt", "missing.md"])
def test_report_refuses_external_or_absent_evidence(tmp_path, name):
    with pytest.raises(ValueError):
        local_path(tmp_path, name)


def test_report_refuses_unknown_status_and_active_image_payload(tmp_path):
    with pytest.raises(ValueError, match="Unrecognized evidence state"):
        render_report(manifest(readiness=[{"name": "x", "status": "probably fine", "detail": "x"}]), tmp_path)
    (tmp_path / "payload.png").write_bytes(b'<svg onload="alert(1)"></svg>')
    with pytest.raises(ValueError, match="PNG"):
        render_report(manifest(screenshots=[{"path": "payload.png", "alt": "x", "caption": "x"}]), tmp_path)
