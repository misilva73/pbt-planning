#!/usr/bin/env python3
"""Generate the PBT roadmap Gantt as one clickable SVG strip per row.

Why strips? GitHub renders SVGs as images but strips links/scripts from an
embedded SVG, and strips CSS/bgcolor from table cells. So to get BOTH real
colour bars AND per-deliverable clickability, we render the chart as one SVG
per row (identical geometry + fork lines drawn through each strip) and stack
them in the README, wrapping each deliverable strip in a normal Markdown link.

Outputs:
  roadmap/assets/rows/_axis.svg        month/year axis + fork markers
  roadmap/assets/rows/_thread-a.svg    thread band headers
  roadmap/assets/rows/_thread-b.svg
  roadmap/assets/rows/_legend.svg      workstream legend + milestone note
  roadmap/assets/rows/<ID>.svg         one per deliverable
It also rewrites the block between <!-- GANTT:START --> and <!-- GANTT:END -->
in roadmap/README.md.

Edit ROWS / DETAIL / MILESTONES below and re-run:
    python3.12 roadmap/scripts/gen_gantt.py

Month index: 1 = 2026-07, 2 = 2026-08, ... 24 = 2028-06, 26 = 2028-08.
"""

import os

N_MONTHS = 26

# workstream -> (bar fill, darker accent, display name)
WORKSTREAMS = {
    "specs":    ("#7c3aed", "#5b21b6", "Specs"),
    "tests":    ("#0891b2", "#155e75", "Tests"),
    "clients":  ("#16a34a", "#166534", "Client implementation"),
    "outreach": ("#ea580c", "#9a3412", "Ecosystem outreach"),
}

# ("thread", title) band header, or ("bar", id, label, workstream, start, end)
ROWS = [
    ("thread", "THREAD A · TRIE DESIGN"),
    ("bar", "A-S1", "A-S1  EIP-8297 spec convergence", "specs", 1, 3),
    ("bar", "A-S3", "A-S3  Witness-gas recalibration", "specs", 19, 21),
    ("bar", "A-S4", "A-S4  EIP-8297 spec freeze", "specs", 7, 9),
    ("bar", "A-T1", "A-T1  EEST test-suite port", "tests", 2, 7),
    ("bar", "A-T2", "A-T2  Tree / key-derivation vectors", "tests", 1, 6),
    ("bar", "A-T3", "A-T3  Genesis conformance & sync", "tests", 7, 12),
    ("bar", "A-T4", "A-T4  Hardware-matrix benchmarks", "tests", 13, 18),
    ("bar", "A-C1", "A-C1  Client tree implementations", "clients", 2, 8),
    ("bar", "A-C2", "A-C2  PBT-native state sync", "clients", 7, 11),
    ("bar", "A-C3", "A-C3  Multi-client genesis devnets", "clients", 8, 12),
    ("bar", "A-C4", "A-C4  Snapshot serving & verification", "clients", 9, 13),
    ("bar", "A-O1", "A-O1  Tree-spec socialization / ACD", "outreach", 1, 9),
    ("thread", "THREAD B · MIGRATION"),
    ("bar", "B-S1", "B-S1  Offline-migration EIP (new)", "specs", 1, 4),
    ("bar", "B-S2", "B-S2  Preimage & snapshot manifest", "specs", 1, 4),
    ("bar", "B-S3", "B-S3  BAL-replay spec", "specs", 5, 6),
    ("bar", "B-S4", "B-S4  Readiness gate & activation", "specs", 15, 20),
    ("bar", "B-T1", "B-T1  Conversion / replay vectors", "tests", 3, 9),
    ("bar", "B-T2", "B-T2  Full-cycle devnet w/ swap", "tests", 9, 14),
    ("bar", "B-T3", "B-T3  Dual-check verification at scale", "tests", 16, 22),
    ("bar", "B-C1", "B-C1  Converter (prototype)", "clients", 4, 9),
    ("bar", "B-C2", "B-C2  BAL-replay engine", "clients", 7, 11),
    ("bar", "B-C3", "B-C3  Snapshot production pipeline", "clients", 8, 13),
    ("bar", "B-C4", "B-C4  Production rehearsals", "clients", 13, 18),
    ("bar", "B-C5", "B-C5  Testnet migrations + shadow fork", "clients", 19, 21),
    ("bar", "B-C6", "B-C6  Mainnet window (block N)", "clients", 22, 24),
    ("bar", "B-C7", "B-C7  Swap at fork S & aftermath", "clients", 24, 26),
    ("bar", "B-O1", "B-O1  Proof-consumer coordination", "outreach", 1, 24),
    ("bar", "B-O3", "B-O3  Shadow roots & readiness", "outreach", 13, 24),
    ("bar", "B-O4", "B-O4  Activation comms & fork-S", "outreach", 20, 24),
]

# deliverable id -> detail-page filename (under deliverables/)
DETAIL = {
    "A-S1": "A-S1-eip8297-spec-convergence.md",
    "A-S3": "A-S3-witness-gas-recalibration.md",
    "A-S4": "A-S4-eip8297-spec-freeze.md",
    "A-T1": "A-T1-eest-test-suite-port.md",
    "A-T2": "A-T2-tree-key-derivation-vectors.md",
    "A-T3": "A-T3-pbt-genesis-conformance-sync-tests.md",
    "A-T4": "A-T4-hardware-matrix-benchmarks.md",
    "A-C1": "A-C1-client-tree-implementations.md",
    "A-C2": "A-C2-pbt-native-state-sync.md",
    "A-C3": "A-C3-multiclient-pbt-genesis-devnets.md",
    "A-C4": "A-C4-snapshot-serving-verification.md",
    "A-O1": "A-O1-tree-spec-socialization.md",
    "B-S1": "B-S1-offline-migration-eip.md",
    "B-S2": "B-S2-preimage-snapshot-manifest-spec.md",
    "B-S3": "B-S3-bal-replay-spec.md",
    "B-S4": "B-S4-readiness-gate-activation-params.md",
    "B-T1": "B-T1-conversion-replay-vectors.md",
    "B-T2": "B-T2-full-cycle-devnet-swap.md",
    "B-T3": "B-T3-dual-check-verification-scale.md",
    "B-C1": "B-C1-converter-prototype.md",
    "B-C2": "B-C2-bal-replay-engine.md",
    "B-C3": "B-C3-snapshot-production-pipeline.md",
    "B-C4": "B-C4-production-rehearsals.md",
    "B-C5": "B-C5-testnet-migrations-shadow-fork.md",
    "B-C6": "B-C6-mainnet-window.md",
    "B-C7": "B-C7-swap-fork-s-aftermath.md",
    "B-O1": "B-O1-proof-consumer-coordination.md",
    "B-O3": "B-O3-shadow-root-ecosystem-readiness.md",
    "B-O4": "B-O4-activation-comms.md",
}

# (month boundary, name, colour) — fork sits at the END of that month
MILESTONES = [(12, "H*", "#b45309"), (24, "I*", "#b91c1c")]

# ---- geometry -------------------------------------------------------------
LEFT = 258
COLW = 30
X0 = LEFT
N_MONTHS = 26
ROWH = 26
BARH = 15
AXIS_H = 58
LEGEND_H = 46
RIGHT_PAD = 18
W = LEFT + N_MONTHS * COLW + RIGHT_PAD   # 1056
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"

YEAR_SPANS = [("2026", 1, 6), ("2027", 7, 18), ("2028", 19, 26)]
MONTH_LABELS = (["07", "08", "09", "10", "11", "12"]
                + [f"{m:02d}" for m in range(1, 13)]
                + [f"{m:02d}" for m in range(1, 9)])


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def mx(month):
    return X0 + (month - 1) * COLW


def fork_x(month):
    return mx(month) + COLW


def svg_doc(h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" '
            f'viewBox="0 0 {W} {h}" font-family="{FONT}">\n'
            + "\n".join(body) + "\n</svg>\n")


def decor(h, zebra=False):
    """Background, gridlines, fork verticals and a bottom separator for a light row."""
    els = [f'<rect x="0" y="0" width="{W}" height="{h}" fill="{"#f8fafc" if zebra else "#ffffff"}"/>']
    for m in range(1, N_MONTHS + 1):
        x = mx(m)
        col = "#cbd5e1" if (m - 1) % 3 == 0 else "#eef2f6"
        els.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{h}" stroke="{col}" stroke-width="1"/>')
    els.append(f'<line x1="{fork_x(N_MONTHS)}" y1="0" x2="{fork_x(N_MONTHS)}" y2="{h}" '
               f'stroke="#cbd5e1" stroke-width="1"/>')
    for month, _, colour in MILESTONES:
        x = fork_x(month)
        els.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{h}" stroke="{colour}" '
                   f'stroke-width="1.5" stroke-dasharray="5 4" stroke-opacity="0.4"/>')
    els.append(f'<line x1="0" y1="{h-0.5}" x2="{W}" y2="{h-0.5}" stroke="#e8edf2" stroke-width="1"/>')
    return els


def bar_row(did, label, ws, start, end, zebra):
    fill, accent, _ = WORKSTREAMS[ws]
    els = decor(ROWH, zebra)
    els.append(f'<text x="16" y="{ROWH/2 + 4:.1f}" font-size="11" fill="#1e293b">{esc(label)}</text>')
    bx = mx(start)
    bw = (end - start + 1) * COLW
    by = (ROWH - BARH) / 2
    els.append(f'<rect x="{bx}" y="{by:.1f}" width="{bw}" height="{BARH}" rx="3.5" fill="{fill}"/>')
    els.append(f'<rect x="{bx}" y="{by:.1f}" width="3" height="{BARH}" rx="1.5" fill="{accent}"/>')
    if bw >= 2.6 * COLW:
        els.append(f'<text x="{bx + 9:.1f}" y="{by + BARH/2 + 3.5:.1f}" font-size="10" '
                   f'font-weight="600" fill="#ffffff">{did}</text>')
    else:
        els.append(f'<text x="{bx + bw + 5:.1f}" y="{by + BARH/2 + 3.5:.1f}" font-size="10" '
                   f'font-weight="600" fill="{accent}">{did}</text>')
    return svg_doc(ROWH, els)


def thread_band(title):
    h = ROWH
    els = [f'<rect x="0" y="0" width="{W}" height="{h}" fill="#0f172a"/>']
    for month, _, _ in MILESTONES:
        x = fork_x(month)
        els.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{h}" stroke="#ffffff" '
                   f'stroke-width="1.5" stroke-dasharray="5 4" stroke-opacity="0.35"/>')
    els.append(f'<text x="12" y="{h/2 + 4:.1f}" font-size="11.5" font-weight="700" '
               f'fill="#ffffff" letter-spacing="0.5">{esc(title)}</text>')
    return svg_doc(h, els)


def axis():
    h = AXIS_H
    els = [f'<rect x="0" y="0" width="{W}" height="{h}" fill="#ffffff"/>']
    # year bands
    for label, a, b in YEAR_SPANS:
        x, w = mx(a), (b - a + 1) * COLW
        els.append(f'<rect x="{x}" y="16" width="{w}" height="20" fill="#f1f5f9" stroke="#e2e8f0"/>')
        els.append(f'<text x="{x + w/2:.1f}" y="30" text-anchor="middle" font-size="12" '
                   f'font-weight="600" fill="#334155">{label}</text>')
    # month ticks
    for i, ml in enumerate(MONTH_LABELS):
        els.append(f'<text x="{mx(i+1) + COLW/2:.1f}" y="50" text-anchor="middle" '
                   f'font-size="9.5" fill="#64748b">{ml}</text>')
    els.append('<text x="12" y="30" font-size="12" font-weight="700" fill="#0f172a">Deliverable</text>')
    # fork markers + line stub connecting downward into the first row
    for month, name, colour in MILESTONES:
        x = fork_x(month)
        els.append(f'<line x1="{x}" y1="38" x2="{x}" y2="{h}" stroke="{colour}" '
                   f'stroke-width="1.6" stroke-dasharray="5 4"/>')
        els.append(f'<text x="{x:.1f}" y="11" text-anchor="middle" font-size="11" '
                   f'font-weight="700" fill="{colour}">◆ {name}</text>')
    return svg_doc(h, els)


def legend():
    h = LEGEND_H
    els = [f'<rect x="0" y="0" width="{W}" height="{h}" fill="#ffffff"/>']
    els.append('<text x="16" y="20" font-size="10.5" font-weight="700" fill="#0f172a">Workstream</text>')
    lx = 100
    for key in ("specs", "tests", "clients", "outreach"):
        fill, _, name = WORKSTREAMS[key]
        els.append(f'<rect x="{lx}" y="10" width="13" height="13" rx="3" fill="{fill}"/>')
        els.append(f'<text x="{lx+19}" y="20.5" font-size="10.5" fill="#334155">{esc(name)}</text>')
        lx += 34 + int(len(name) * 6.2)
    els.append('<text x="16" y="39" font-size="10" fill="#64748b">'
               '◆ H* (2027-06): spec freeze + shadow period opens  ·  '
               '◆ I* (2028-06): fork S, PBT canonical</text>')
    return svg_doc(h, els)


def month_str(mi):
    val = 2026 * 12 + 6 + (mi - 1)           # 2026-07 == index 1
    return f"{val // 12:04d}-{val % 12 + 1:02d}"


def main():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    rows_dir = os.path.join(base, "assets", "rows")
    os.makedirs(rows_dir, exist_ok=True)

    def write(name, content):
        with open(os.path.join(rows_dir, name), "w") as f:
            f.write(content)

    write("_axis.svg", axis())
    write("_legend.svg", legend())

    md = ['![Timeline: months 2026-07 to 2028-08; forks H* (2027-06) and I* (2028-06)]'
          '(assets/rows/_axis.svg)']

    thread_file = {"A": "_thread-a.svg", "B": "_thread-b.svg"}
    cur = "A"
    zebra = False
    for row in ROWS:
        if row[0] == "thread":
            cur = "A" if "THREAD A" in row[1] else "B"
            write(thread_file[cur], thread_band(row[1]))
            md.append(f'![{esc(row[1])}](assets/rows/{thread_file[cur]})')
            zebra = False
            continue
        _, did, label, ws, start, end = row
        write(f"{did}.svg", bar_row(did, label, ws, start, end, zebra))
        alt = f"{label} · {month_str(start)}→{month_str(end)} · open detail page"
        md.append(f'[![{alt}](assets/rows/{did}.svg)](deliverables/{DETAIL[did]})')
        zebra = not zebra

    write("_legend.svg", legend())
    md.append('![Workstream legend: specs, tests, client implementation, ecosystem outreach; '
              'fork dates](assets/rows/_legend.svg)')

    # patch README between the GANTT markers
    readme = os.path.join(base, "README.md")
    s = open(readme).read()
    start_tag, end_tag = "<!-- GANTT:START", "<!-- GANTT:END -->"
    i = s.index(start_tag)
    i_close = s.index("-->", i) + 3
    j = s.index(end_tag)
    block = "\n" + "\n".join(md) + "\n"
    s = s[:i_close] + block + s[j:]
    open(readme, "w").write(s)

    n_bars = sum(1 for r in ROWS if r[0] == "bar")
    print(f"wrote {n_bars} row strips + axis/legend/2 bands to {rows_dir}")
    print(f"patched {readme} between GANTT markers ({len(md)} image lines)")


if __name__ == "__main__":
    main()
