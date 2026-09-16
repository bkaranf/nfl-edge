"""Render an offline report from explicit evidence; never infer a passing gate."""
from __future__ import annotations

import argparse
import base64
import html
import json
from pathlib import Path


STATES = {"PASS", "FAIL", "NOT_RUN", "BLOCKED", "IN_PROGRESS", "UNPROVEN"}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURE = b"\xff\xd8\xff"


def local_path(root: Path, name: str) -> Path:
    """Only repository-contained local files can become report evidence."""
    if not isinstance(name, str) or not name or ":" in name or "\\" in name:
        raise ValueError("Evidence paths must be relative repository paths")
    relative = Path(name)
    if relative.is_absolute():
        raise ValueError("Evidence paths must be relative repository paths")
    root = root.resolve()
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("Evidence must stay inside the repository")
    if not resolved.is_file():
        raise ValueError(f"Evidence file is absent: {name}")
    return resolved


def escaped(value: object) -> str:
    return html.escape(str(value), quote=True)


def badge(value: str) -> str:
    if value not in STATES:
        raise ValueError(f"Unrecognized evidence state: {value}")
    return f'<span class="badge {value.lower()}">{escaped(value)}</span>'


def render_report(manifest: dict, root: Path) -> str:
    """All text is escaped. Images are embedded; no remote resource is loaded."""
    if manifest.get("schema_version") != 1:
        raise ValueError("Unsupported report manifest schema")
    root = root.resolve()
    sections = []
    for item in manifest.get("readiness", []):
        sections.append(
            f'<article><h3>{escaped(item["name"])}</h3>{badge(item["status"])}'
            f'<p>{escaped(item["detail"])}</p></article>'
        )
    rows = []
    for item in manifest.get("checks", []):
        evidence = []
        for name in item.get("evidence", []):
            local_path(root, name)
            # Paths are readable locators, not active file/remote navigation.
            evidence.append(f'<code>{escaped(name)}</code>')
        rows.append(
            f'<tr><th scope="row">{escaped(item["id"])}</th>'
            f'<td>{escaped(item["requirement"])}</td><td>{badge(item["status"])}</td>'
            f'<td>{escaped(item.get("detail", ""))}'
            f'<div class="evidence">{"<br>".join(evidence)}</div></td></tr>'
        )
    commands = []
    for item in manifest.get("runs", []):
        evidence = item.get("evidence")
        if evidence:
            local_path(root, evidence)
        commands.append(
            f'<li><strong>{escaped(item["name"])}</strong> {badge(item["status"])}'
            f'<pre>{escaped(item["command"])}</pre><p>{escaped(item["result"])}</p>'
            f'<code>{escaped(evidence or "No evidence file supplied")}</code></li>'
        )
    figures = []
    for item in manifest.get("screenshots", []):
        data = local_path(root, item["path"]).read_bytes()
        mime = ("image/png" if data.startswith(PNG_SIGNATURE) else
                "image/jpeg" if data.startswith(JPEG_SIGNATURE) else None)
        if len(data) > 8_000_000 or mime is None:
            raise ValueError("Screenshots must be PNG or JPEG files of at most 8 MB")
        encoded = base64.b64encode(data).decode("ascii")
        figures.append(
            f'<figure><img src="data:{mime};base64,{encoded}" '
            f'alt="{escaped(item["alt"])}"><figcaption>{escaped(item["caption"])}'
            f'</figcaption></figure>'
        )
    notes = "".join(f'<li>{escaped(note)}</li>' for note in manifest.get("limitations", []))
    refs = []
    for name in manifest.get("documents", []):
        contents = local_path(root, name).read_text(encoding="utf-8-sig")
        # Embed the referenced records so this report remains useful offline and
        # after movement. Details anchors are local links, never external URLs.
        anchor = f"document-{len(refs) + 1}"
        refs.append(
            f'<details id="{anchor}"><summary>{escaped(name)}</summary>'
            f'<pre>{escaped(contents)}</pre></details>'
        )
    nav = " ".join(
        f'<a href="#document-{i + 1}">{escaped(name)}</a>'
        for i, name in enumerate(manifest.get("documents", []))
    )
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>{escaped(manifest["title"])}</title>
<style>
:root{{font-family:system-ui,sans-serif;color:#182d38;background:#f5f7f9;color-scheme:light}}
body{{margin:0}}main{{max-width:1200px;margin:auto;padding:32px 24px 64px}}
h1{{font-size:clamp(1.7rem,4vw,2.5rem);margin-bottom:12px}}h2{{margin-top:36px}}
p,li{{line-height:1.6}}.meta{{color:#405664;overflow-wrap:anywhere}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}}
article,figure,details{{background:white;border:1px solid #cbd5dc;border-radius:10px;padding:18px}}
article h3{{margin-top:0}}.badge{{font-weight:700;display:inline-block;font-size:.8rem;padding:4px 8px;border-radius:5px;background:#e3e8ee;color:#253a4b}}
.pass{{background:#d5f1e4;color:#084c30}}.fail{{background:#fbdcdd;color:#891c22}}
.blocked,.unproven{{background:#fff0cd;color:#65460a}}table{{border-collapse:collapse;width:100%;background:white}}
th,td{{padding:12px;text-align:left;border:1px solid #cbd5dc;vertical-align:top}}
thead{{background:#e8eef2}}.scroll{{overflow-x:auto}}code,pre{{font-family:ui-monospace,monospace}}
pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#f1f4f6;padding:12px}}
.evidence{{margin-top:8px;font-size:.8rem;overflow-wrap:anywhere}}li{{margin-bottom:14px}}
figure{{margin:18px 0}}img{{max-width:100%;height:auto}}figcaption{{padding-top:12px}}
details{{margin:12px 0}}summary{{cursor:pointer;font-weight:650}}a{{color:#075577}}
a:focus-visible,summary:focus-visible{{outline:3px solid #ae4b00;outline-offset:4px}}
nav{{display:flex;flex-wrap:wrap;gap:12px}}@media(max-width:450px){{main{{padding:20px 12px}}th,td{{padding:8px}}}}
</style></head><body><main>
<h1>{escaped(manifest["title"])}</h1><p>{escaped(manifest["summary"])}</p>
<p class="meta">Generated: {escaped(manifest["generated_at"])}<br>
Starting revision: {escaped(manifest["starting_revision"])}<br>
Inspected revision/worktree: {escaped(manifest["revision"])}<br>
Runtime: {escaped(manifest["runtime"])}</p>
<h2>Readiness</h2><div class="cards">{"".join(sections)}</div>
<h2>Acceptance evidence</h2><div class="scroll"><table>
<thead><tr><th>ID</th><th>Requirement</th><th>Status</th><th>Evidence and limits</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div>
<h2>Executed checks</h2><ol>{"".join(commands)}</ol>
<h2>Browser evidence</h2>{"".join(figures) or "<p>No browser evidence included.</p>"}
<h2>Limits and remaining work</h2><ul>{notes}</ul>
<h2>Embedded evidence records</h2><nav>{nav}</nav>{"".join(refs)}
</main></body></html>'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="Repository-relative JSON manifest")
    parser.add_argument("--output", default=".qa/evidence-report.html")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads(local_path(root, args.manifest).read_text(encoding="utf-8-sig"))
    output = (root / args.output).resolve()
    if not output.is_relative_to(root) or output.suffix != ".html":
        parser.error("Output must be an HTML path inside the repository")
    rendered = render_report(manifest, root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
