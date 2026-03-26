import argparse
import io
import os
import sys
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

# -------------------------------------------------------------------------
# CONSTANTS
# -------------------------------------------------------------------------

D     = 900.0
d     = 12.5
N_300 = 24
N_600 = 48

M    = 100_000   # daily commuters at Yeshwantpur hub
W    = 250       # working days per year
WAGE = 50 / 60  # RBI informal wage rate — ₹50/hr → ₹/min

FIX_COST_LOW_LAKH  = 8
FIX_COST_HIGH_LAKH = 12

# -------------------------------------------------------------------------
# DATA LOADERS
# -------------------------------------------------------------------------

def load_audit_data() -> pd.DataFrame:
    path = os.path.join("data", "audit_log.csv")
    df = pd.read_csv(path)
    assert {"id", "lat", "lon", "f_value"}.issubset(df.columns)
    return df


def load_personas() -> dict:
    path = os.path.join("data", "personas.yaml")
    with open(path, "r") as f:
        return yaml.safe_load(f)


# -------------------------------------------------------------------------
# SIMULATION CORE
# -------------------------------------------------------------------------

def build_f_array(df: pd.DataFrame, n_fixes: int, bazaar_f: int = 5) -> np.ndarray:
    f_300 = df["f_value"].values.astype(float)
    if n_fixes > 0:
        fix_idx = np.argsort(f_300)[::-1][:n_fixes]
        f_300 = f_300.copy()
        f_300[fix_idx] = 1.0
    return np.concatenate([f_300, np.full(N_600, float(bazaar_f))])


def run_simulation(f_array: np.ndarray, persona: dict) -> dict:
    v0, k     = persona["v0"], persona["k"]
    f_max     = persona["f_max"]
    alpha     = persona["alpha"]
    delta_m   = persona["delta"]
    tau_i     = np.empty(len(f_array))
    is_det    = np.zeros(len(f_array), dtype=bool)
    for i, fi in enumerate(f_array):
        if fi > f_max:
            tau_i[i]  = (d + delta_m) * alpha / v0
            is_det[i] = True
        else:
            tau_i[i] = d * (fi ** k) / v0
    T_actual = float(tau_i.sum())
    T_ideal  = D / v0
    return {
        "T_actual":  T_actual,
        "T_ideal":   T_ideal,
        "delta_tau": T_actual - T_ideal,
        "n_detours": int(is_det.sum()),
    }


# -------------------------------------------------------------------------
# ECONOMIC CALCULATIONS
# -------------------------------------------------------------------------

def compute_economics(
    df: pd.DataFrame,
    personas: dict,
    n_fixes: int,
    bazaar_f: int = 5,
) -> dict:
    f_array = build_f_array(df, n_fixes, bazaar_f)
    f_base  = build_f_array(df, 0, 5)

    results  = {k: run_simulation(f_array, v) for k, v in personas.items()}
    results0 = {k: run_simulation(f_base,  v) for k, v in personas.items()}

    total_w = sum(p["weight"] for p in personas.values())

    def weighted_mean(res):
        return sum(
            res[k]["delta_tau"] * personas[k]["weight"] for k in personas
        ) / total_w

    dtau_bar  = weighted_mean(results)
    dtau_bar0 = weighted_mean(results0)

    annual_pm  = M * W * dtau_bar  / 60   # person-minutes
    annual_pm0 = M * W * dtau_bar0 / 60

    annual_loss_cr  = annual_pm  * WAGE / 1e7   # ₹ crore
    annual_loss_cr0 = annual_pm0 * WAGE / 1e7

    pct_recovered = (
        (annual_loss_cr0 - annual_loss_cr) / annual_loss_cr0 * 100
        if annual_loss_cr0 > 0 and (n_fixes > 0 or bazaar_f < 5) else 0.0
    )

    recovered_lakh = (annual_loss_cr0 - annual_loss_cr) * 100  # cr → lakh
    bcr_low  = recovered_lakh / FIX_COST_HIGH_LAKH if n_fixes > 0 else 0.0
    bcr_high = recovered_lakh / FIX_COST_LOW_LAKH  if n_fixes > 0 else 0.0

    return {
        "results":         results,
        "results0":        results0,
        "delta_tau_bar":   dtau_bar,
        "delta_tau_bar0":  dtau_bar0,
        "annual_pm":       annual_pm,
        "annual_pm0":      annual_pm0,
        "annual_loss_cr":  annual_loss_cr,
        "annual_loss_cr0": annual_loss_cr0,
        "pct_recovered":   pct_recovered,
        "bcr_low":         bcr_low,
        "bcr_high":        bcr_high,
        "n_fixes":         n_fixes,
        "bazaar_f":        bazaar_f,
    }


# -------------------------------------------------------------------------
# PLOT HELPERS  (white background — suitable for PDF and screen)
# -------------------------------------------------------------------------

def plot_time_tax_bars(results: dict, personas: dict,
                       dark: bool = True) -> plt.Figure:
    """Horizontal bar — Time Tax per persona (minutes)."""
    labels = [p["label"] for p in personas.values()]
    taxes  = [results[k]["delta_tau"] / 60 for k in personas]
    colors = [p["color"] for p in personas.values()]
    bg     = "#1a1a1a" if dark else "white"
    tc     = "white"   if dark else "#333333"

    fig, ax = plt.subplots(figsize=(7, 3))
    bars = ax.barh(labels, taxes, color=colors, height=0.5, linewidth=0)
    for bar, val in zip(bars, taxes):
        ax.text(val + 0.05, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f} min", va="center", fontsize=8.5, color=tc)
    ax.set_xlabel("Time Tax per trip (min)", fontsize=9, color=tc)
    ax.set_facecolor(bg)
    fig.patch.set_facecolor(bg)
    ax.tick_params(colors=tc, labelsize=9)
    ax.xaxis.label.set_color(tc)
    for spine in ax.spines.values():
        spine.set_visible(False if dark else True)
        spine.set_color("#cccccc")
    fig.tight_layout()
    return fig


def plot_friction_distribution(df: pd.DataFrame,
                                dark: bool = True) -> plt.Figure:
    """Pie chart of f-value distribution across the 300m stretch."""
    F_COLORS = {2: "#4CAF50", 3: "#2196F3", 4: "#FF9800", 5: "#F44336"}
    counts = df["f_value"].value_counts().sort_index()
    colors = [F_COLORS.get(int(f), "#9E9E9E") for f in counts.index]
    labels = [f"f={int(f)}" for f in counts.index]
    bg = "#1a1a1a" if dark else "white"
    tc = "white"   if dark else "#333333"

    fig, ax = plt.subplots(figsize=(4, 4))
    _, texts, autotexts = ax.pie(
        counts.values, labels=labels, colors=colors,
        autopct="%1.1f%%", startangle=140,
        textprops={"color": tc, "fontsize": 9},
    )
    for at in autotexts:
        at.set_color(tc)
        at.set_fontsize(8)
    ax.set_facecolor(bg)
    fig.patch.set_facecolor(bg)
    ax.set_title("Obstacle Distribution — 300m stretch",
                 color=tc, fontsize=9)
    fig.tight_layout()
    return fig


def plot_bcr_curve(df: pd.DataFrame, personas: dict,
                   bazaar_f: int, n_range: int = 10,
                   dark: bool = True) -> plt.Figure:
    """BCR vs n_fixes curve."""
    bg = "#1a1a1a" if dark else "white"
    tc = "white"   if dark else "#333333"

    bcr_vals = []
    for n in range(n_range + 1):
        e = compute_economics(df, personas, n, bazaar_f)
        mid = (e["bcr_low"] + e["bcr_high"]) / 2
        bcr_vals.append(mid)

    fig, ax = plt.subplots(figsize=(7, 3))
    ax.plot(range(n_range + 1), bcr_vals, color="#FF9800",
            linewidth=2.5, marker="o", markersize=5)
    ax.axhline(10, color="#4CAF50", linewidth=1, linestyle="--",
               label="BCR = 10:1 threshold")
    ax.fill_between(range(n_range + 1), bcr_vals, 0,
                    alpha=0.15, color="#FF9800")
    ax.set_xlabel("Number of hotspots fixed (top-N)", fontsize=9, color=tc)
    ax.set_ylabel("Benefit-Cost Ratio", fontsize=9, color=tc)
    ax.legend(fontsize=8,
              facecolor="#2a2a2a" if dark else "white",
              labelcolor=tc)
    ax.set_facecolor(bg)
    fig.patch.set_facecolor(bg)
    ax.tick_params(colors=tc, labelsize=8)
    ax.xaxis.label.set_color(tc)
    ax.yaxis.label.set_color(tc)
    for spine in ax.spines.values():
        spine.set_visible(not dark)
        spine.set_color("#cccccc")
    fig.tight_layout()
    return fig


# -------------------------------------------------------------------------
# TABLE STYLE HELPER  (avoids repeating setStyle boilerplate)
# -------------------------------------------------------------------------

def _table_style(colors_mod, header_rows=1):
    """Return a TableStyle for ReportLab tables."""
    from reportlab.platypus import TableStyle as TS

    style = [
        # Header row(s)
        ("BACKGROUND",   (0, 0), (-1, header_rows - 1),
         colors_mod.HexColor("#2c2c2c")),
        ("TEXTCOLOR",    (0, 0), (-1, header_rows - 1), colors_mod.white),
        ("FONTNAME",     (0, 0), (-1, header_rows - 1), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 8),
        ("LEADING",      (0, 0), (-1, -1), 11),
        ("GRID",         (0, 0), (-1, -1), 0.3, colors_mod.HexColor("#dddddd")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ]
    # Alternating row backgrounds (data rows only)
    from reportlab.lib import colors as C
    for i in range(header_rows, 99, 2):
        style.append(("BACKGROUND", (0, i), (-1, i),
                       C.HexColor("#f5f5f5")))
    return TS(style)


# -------------------------------------------------------------------------
# PDF GENERATOR
# -------------------------------------------------------------------------

def generate_pdf(
    df: pd.DataFrame,
    personas: dict,
    n_fixes: int,
    bazaar_f: int,
    output_path: str,
) -> None:
    """
    Render a 2-page A4 policy brief PDF using ReportLab.

    Page 1 — Audit findings: statistics table, friction pie, Time Tax bars.
    Page 2 — Economic impact, Lighthouse Proposal table, policy ask.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer,
            Table, Image, HRFlowable, PageBreak,
        )
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
    except ImportError:
        print("ReportLab not installed. Run: pip install reportlab")
        sys.exit(1)

    econ = compute_economics(df, personas, n_fixes, bazaar_f)

    # --- Render charts to PNG bytes (white background for print) ---
    def fig_to_buf(fig: plt.Figure) -> io.BytesIO:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150,
                    bbox_inches="tight", facecolor=fig.get_facecolor())
        buf.seek(0)
        plt.close(fig)
        return buf

    buf_pie  = fig_to_buf(plot_friction_distribution(df, dark=False))
    buf_bars = fig_to_buf(plot_time_tax_bars(econ["results0"], personas, dark=False))

    # --- Document ---
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2.5*cm, rightMargin=2.5*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    ss   = getSampleStyleSheet()
    H1   = ParagraphStyle("H1",  parent=ss["Heading1"],
                           fontSize=14, spaceAfter=4, spaceBefore=0)
    H2   = ParagraphStyle("H2",  parent=ss["Heading2"],
                           fontSize=11, spaceAfter=4, spaceBefore=8)
    BODY = ParagraphStyle("BODY", parent=ss["Normal"],
                           fontSize=9, leading=14, spaceAfter=5)
    SMALL = ParagraphStyle("SMALL", parent=ss["Normal"],
                            fontSize=8, leading=11,
                            textColor=colors.HexColor("#666666"))
    MONO  = ParagraphStyle("MONO", parent=ss["Normal"],
                            fontSize=8, leading=12, fontName="Courier",
                            backColor=colors.HexColor("#f0f0f0"),
                            leftIndent=12, rightIndent=12,
                            spaceAfter=6)

    story = []
    W_FULL = 17 * cm   # usable page width (A4 - margins)

    # ================================================================
    # PAGE 1 — AUDIT FINDINGS
    # ================================================================
    story.append(Paragraph(
        "Escape the Knot: Yeshwantpur Mobility Audit", H1))
    story.append(Paragraph(
        "Student-Led Pedestrian Infrastructure Audit &mdash; "
        "YLAC Mobility Champions 2026 &middot; Bengawalk", SMALL))
    story.append(Paragraph(
        "Survey conducted: 7&ndash;8 March 2026 &middot; "
        "900m Yeshwantpur&ndash;Constitution Circle corridor", SMALL))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=colors.HexColor("#cccccc"), spaceAfter=8))

    story.append(Paragraph("1. Audit Findings", H2))
    story.append(Paragraph(
        "The 900m corridor was split into two zones: (a) a 300m stretch from the "
        "South Western Railway exit to Constitution Circle, where 24 obstacles were "
        "geotagged and assigned friction values f &isin; {1,2,3,4,5} per the "
        "Active Mobility Bill rubric; and (b) a 600m Bazaar Street stretch rated "
        "as a continuous f&nbsp;=&nbsp;5 (Systemic Failure) block where the "
        "footpath is entirely absent. The mean friction index "
        "f&#772; = L<sub>eff</sub>/D = 4187.5/900 &asymp; 4.653 means the corridor "
        "imposes 4.65&times; the energetic cost of a Tender S.U.R.E.-compliant path.",
        BODY,
    ))

    # Key statistics table
    stats = [
        ["Metric", "Value"],
        ["Total corridor length",          "900 m"],
        ["Discrete obstacle nodes (300m)", "24 nodes, d = 12.5 m each"],
        ["Continuous f=5 block (600m)",    "Bazaar Street — footpath absent"],
        ["L\u2090\u2091\u2092 (300m)",    "12.5 \u00d7 95 = 1187.5 m"],
        ["L\u2090\u2091\u2092 (600m)",    "600 \u00d7 5 = 3000.0 m"],
        ["L\u2090\u2091\u2092 (total)",   "4187.5 m"],
        ["Mean friction index f\u0305",    "4.653"],
        ["Fails Active Mobility Bill",     "90.3% of corridor"],
        ["Wheelchair inaccessible",        "96.0% of corridor"],
        ["Nodes at f=5 (Systemic Failure)","9 / 24  (37.5%)"],
        ["Nodes at f=4 (Physical Barrier)","8 / 24  (33.3%)"],
        ["Nodes at f=3 (Obstacle Course)", "4 / 24  (16.7%)"],
        ["Nodes at f=2 (Distracted Walk)", "3 / 24  (12.5%)"],
    ]
    t = Table(stats, colWidths=[9*cm, 8*cm])
    t.setStyle(_table_style(colors))
    story.append(t)
    story.append(Spacer(1, 0.4*cm))

    # Charts side by side
    story.append(Paragraph(
        "Obstacle Distribution (300m stretch) and Per-Persona Time Tax", H2))
    chart_row = Table(
        [[Image(buf_pie,  width=7.5*cm, height=7*cm),
          Image(buf_bars, width=8.5*cm, height=5.5*cm)]],
        colWidths=[8*cm, 9*cm],
    )
    story.append(chart_row)

    # ================================================================
    # PAGE 2 — ECONOMIC IMPACT + LIGHTHOUSE PROPOSAL
    # ================================================================
    story.append(PageBreak())

    story.append(Paragraph("2. Methodology: Time Tax Computation", H2))
    story.append(Paragraph(
        "Each path segment of length d = 12.5 m is traversed at an effective "
        "speed governed by the local friction value and the commuter persona &phi;. "
        "Rather than a linear speed reduction, a power-law model is used:", BODY))
    story.append(Paragraph(
        "v_eff(i, \u03c6) = v\u2080(\u03c6) / f_i^k(\u03c6)", MONO))
    story.append(Paragraph(
        "where v\u2080 is the free-walking speed (m/s) and k is the "
        "friction sensitivity exponent. A higher k means the persona loses speed "
        "super-linearly as friction increases &mdash; critical for wheelchair users "
        "and the elderly. Segment traversal time:", BODY))
    story.append(Paragraph(
        "\u03c4_i(\u03c6) = d \u00d7 f_i^k / v\u2080", MONO))
    story.append(Paragraph(
        "If f_i > f_max(\u03c6), the segment is impassable. The agent is rerouted "
        "into the vehicular Right-of-Way (ROW), incurring a geometric detour of "
        "\u03b4 metres and a safety penalty multiplier \u03b1 = 1.5:", BODY))
    story.append(Paragraph(
        "\u03c4_i\u1d3f\u1d3f\u1d42 = (d + \u03b4) \u00d7 \u03b1 / v\u2080", MONO))
    story.append(Paragraph(
        "The Time Tax per trip is the difference between actual and ideal "
        "(fully S.U.R.E.-compliant, f=1 throughout) traversal time:", BODY))
    story.append(Paragraph(
        "\u0394\u03c4(\u03c6) = T_actual \u2212 T_ideal = "
        "(d/v\u2080) \u00d7 (\u03a3 f_i^k \u2212 N)", MONO))

    # Persona parameter table
    story.append(Paragraph("Commuter Persona Parameters", H2))
    persona_rows = [["Persona", "v\u2080 (m/s)", "k", "f_max",
                     "\u03b4 (m)", "Weight", "\u0394\u03c4 baseline (s)"]]
    for key, p in personas.items():
        r0 = econ["results0"][key]
        persona_rows.append([
            p["label"],
            str(p["v0"]),
            str(p["k"]),
            str(p["f_max"]),
            str(p["delta"]),
            f"{p['weight']*100:.0f}%",
            f"{r0['delta_tau']:.0f}",
        ])
    tp = Table(persona_rows,
               colWidths=[4.5*cm, 2*cm, 1.5*cm, 1.5*cm, 1.5*cm, 2*cm, 4*cm])
    tp.setStyle(_table_style(colors))
    story.append(tp)
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("3. Economic Impact", H2))
    story.append(Paragraph(
        "The persona-weighted mean Time Tax is:", BODY))
    story.append(Paragraph(
        "\u0394\u03c4\u0305 = \u03a3(\u03c6) w_\u03c6 \u00d7 \u0394\u03c4(\u03c6) "
        "/ \u03a3 w_\u03c6  =  "
        f"{econ['delta_tau_bar0']:.1f} s/trip  (baseline)", MONO))
    story.append(Paragraph(
        "Aggregated across M = 100,000 daily commuters and W = 250 working days:", BODY))
    story.append(Paragraph(
        f"T_year = M \u00d7 W \u00d7 \u0394\u03c4\u0305 / 60  =  "
        f"{M:,} \u00d7 {W} \u00d7 {econ['delta_tau_bar0']:.1f} / 60  =  "
        f"{econ['annual_pm0']/1e6:.1f}M person-minutes/year", MONO))
    story.append(Paragraph(
        "Converting at the RBI informal wage rate (~\u20b950/hr = \u20b90.833/min):", BODY))
    story.append(Paragraph(
        f"Annual loss = {econ['annual_pm0']/1e6:.1f}M min \u00d7 \u20b90.833/min "
        f"= \u20b9{econ['annual_loss_cr0']:.1f} crore/year", MONO))

    econ_data = [["Metric", "Baseline", f"After {n_fixes} fixes"]]
    econ_data.append([
        "Weighted mean \u0394\u03c4\u0305",
        f"{econ['delta_tau_bar0']:.1f} s",
        f"{econ['delta_tau_bar']:.1f} s",
    ])
    econ_data.append([
        "Annual person-minutes lost",
        f"{econ['annual_pm0']/1e6:.2f}M",
        f"{econ['annual_pm']/1e6:.2f}M",
    ])
    econ_data.append([
        "Annual productivity loss",
        f"\u20b9{econ['annual_loss_cr0']:.2f} Cr",
        f"\u20b9{econ['annual_loss_cr']:.2f} Cr",
    ])
    econ_data.append([
        "Time Tax recovered", "—",
        f"{econ['pct_recovered']:.1f}%",
    ])
    for key, p in personas.items():
        r0 = econ["results0"][key]
        r  = econ["results"][key]
        l0 = M * W * r0["delta_tau"] / 60 * WAGE / 1e7
        l  = M * W * r["delta_tau"]  / 60 * WAGE / 1e7
        econ_data.append([
            f"  {p['label']}  (w={p['weight']})",
            f"\u0394\u03c4={r0['delta_tau']:.0f}s  \u20b9{l0:.2f}Cr",
            f"\u0394\u03c4={r['delta_tau']:.0f}s  \u20b9{l:.2f}Cr",
        ])
    te = Table(econ_data, colWidths=[7*cm, 5*cm, 5*cm])
    te.setStyle(_table_style(colors))
    story.append(te)
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("4. Lighthouse Proposal", H2))
    story.append(Paragraph(
        f"Bringing the top {n_fixes} friction hotspot(s) to Tender S.U.R.E. "
        f"standard (f=1) &mdash; estimated cost "
        f"\u20b9{FIX_COST_LOW_LAKH}&ndash;{FIX_COST_HIGH_LAKH} lakh for drain "
        f"covers and slab repair &mdash; yields the following return:", BODY))

    lh_data = [
        ["Repair cost estimate",
         f"\u20b9{FIX_COST_LOW_LAKH}\u2013{FIX_COST_HIGH_LAKH} lakh"],
        ["Annual productivity recovered",
         f"\u20b9{(econ['annual_loss_cr0']-econ['annual_loss_cr'])*100:.0f} lakh/yr"],
        ["% of Time Tax recovered",
         f"{econ['pct_recovered']:.1f}%"],
        ["Benefit-cost ratio",
         f"{econ['bcr_low']:.1f}:1 \u2013 {econ['bcr_high']:.1f}:1"],
    ]
    tl = Table(lh_data, colWidths=[10*cm, 7*cm])
    tl.setStyle(_table_style(colors))
    story.append(tl)
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("5. Policy Ask", H2))
    story.append(Paragraph(
        "We request that DULT and BBMP initiate a Lighthouse Pilot project at the "
        "Yeshwantpur Mobility Knot, mandating Tender S.U.R.E. Design Standards on "
        "the 900m Constitution Circle&ndash;Railway Station corridor. Specific ask: "
        "(1) replace open box drains with integrated Pipe and Chamber systems; "
        "(2) restore continuous 3m footpath width on Bazaar Street; "
        "(3) install kerb ramps at all crossings per IRC 103 guidelines. "
        "A benefit-to-cost ratio exceeding 10:1 makes this the highest-return "
        "pedestrian investment available at the hub.", BODY))

    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=colors.HexColor("#cccccc"), spaceAfter=6))
    story.append(Paragraph(
        "Submitted by: Aaitijhya Goswami &amp; Prajwal Kagalgomb &middot; "
        "YLAC Mobility Champions 2026 &middot; Partner: Bengawalk &middot; "
        "Field audit: March 7&ndash;8, 2026", SMALL))

    doc.build(story)
    print(f"PDF written to: {output_path}")


# -------------------------------------------------------------------------
# STREAMLIT APP ENTRY POINT
# -------------------------------------------------------------------------

def app():
    import streamlit as st

    @st.cache_data
    def _load_audit():
        return load_audit_data()

    @st.cache_data
    def _load_personas():
        return load_personas()

    st.title("Economic Impact & Policy Brief")
    st.markdown(
        "Aggregates the persona-weighted Time Tax across $M = 100{,}000$ daily "
        "commuters and $W = 250$ working days, converts to economic value at the "
        "RBI informal wage rate (~₹50/hr), and generates a submission-ready "
        "PDF brief for DULT and BBMP."
    )
    st.markdown("---")

    try:
        df       = _load_audit()
        personas = _load_personas()
    except FileNotFoundError as e:
        st.error(f"Missing data file: {e}")
        return

    # -----------------------------------------------------------------------
    # SIDEBAR
    # -----------------------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📄 Policy Brief Controls")

    n_fixes = st.sidebar.slider(
        "Hotspots fixed (top-N) for Lighthouse Proposal:",
        min_value=0, max_value=len(df), value=3, step=1,
        help=(
            "Default is 3 — the Lighthouse Pilot ask. "
            "This is the number of hotspot fixes costed in the PDF brief."
        )
    )

    sure_standards = {
        "Current — f=5 (Systemic Failure)": 5,
        "Partial repair — f=4 (Physical Barrier)": 4,
        "Moderate repair — f=3 (Obstacle Course)": 3,
        "Near compliant — f=2 (Distracted Walk)": 2,
        "Full S.U.R.E. compliance — f=1 (Gold Standard)": 1,
    }
    bazaar_label = st.sidebar.selectbox(
        "Bazaar Street modelled as:",
        options=list(sure_standards.keys()),
        index=0,
    )
    bazaar_f = sure_standards[bazaar_label]

    if n_fixes == 3:
        st.sidebar.caption(
            f"📋 Default Lighthouse Pilot: fix 3 obstacles for "
            f"₹{FIX_COST_LOW_LAKH}–{FIX_COST_HIGH_LAKH} lakh."
        )
    elif n_fixes == 0:
        st.sidebar.caption("📋 Showing baseline surveyed conditions — no fixes applied.")
    else:
        st.sidebar.caption(
            f"📋 Custom scenario: {n_fixes} fix(es). "
            "Adjust to explore different intervention sizes."
        )

    st.sidebar.markdown("---")
    st.sidebar.markdown("**PDF export settings**")
    pdf_fixes  = st.sidebar.number_input(
        "n_fixes for PDF:", min_value=0, max_value=len(df),
        value=n_fixes, step=1,
    )
    pdf_output = st.sidebar.text_input("Filename:", value="brief.pdf")

    # -----------------------------------------------------------------------
    # COMPUTE
    # -----------------------------------------------------------------------
    econ = compute_economics(df, personas, n_fixes, bazaar_f)

    # -----------------------------------------------------------------------
    # HEADLINE METRICS
    # -----------------------------------------------------------------------
    st.markdown("#### Annual Economic Impact — Baseline Conditions")
    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Annual person-minutes lost",
        f"{econ['annual_pm0']/1e6:.2f}M",
        help=f"M × W × Δτ̄ / 60 = {M:,} × {W} × {econ['delta_tau_bar0']:.1f}s / 60",
    )
    col2.metric(
        "Annual productivity loss",
        f"₹{econ['annual_loss_cr0']:.2f} Cr",
        help="Person-minutes × ₹50/hr RBI informal wage rate",
    )
    col3.metric(
        "Weighted mean Time Tax Δτ̄",
        f"{econ['delta_tau_bar0']:.1f} s/trip",
        help="Σ(w_φ × Δτ(φ)) / Σ w_φ across all four personas.",
    )

    st.markdown("---")
    st.markdown("#### Lighthouse Proposal — Impact of Fixes")
    col4, col5, col6 = st.columns(3)
    col4.metric(
        f"Loss after {n_fixes} fix(es)",
        f"₹{econ['annual_loss_cr']:.2f} Cr",
        delta=f"−₹{econ['annual_loss_cr0'] - econ['annual_loss_cr']:.2f} Cr",
        delta_color="normal",
    )
    col5.metric("Time Tax recovered", f"{econ['pct_recovered']:.1f}%")
    col6.metric(
        "Benefit-cost ratio",
        f"{econ['bcr_low']:.1f}–{econ['bcr_high']:.1f} : 1",
        help=f"Annual saving / repair cost (₹{FIX_COST_LOW_LAKH}–{FIX_COST_HIGH_LAKH} lakh)",
    )

    if econ["pct_recovered"] > 0:
        st.success(
            f"Fixing the top {n_fixes} hotspot(s) to "
            "[Tender S.U.R.E.](https://www.janausp.org/portfolio/tender-sure) "
            f"standard recovers **{econ['pct_recovered']:.1f}%** of the annual "
            f"Time Tax at a BCR of **{econ['bcr_low']:.1f}:1 – {econ['bcr_high']:.1f}:1**."
        )

    st.markdown("---")

  # -----------------------------------------------------------------------
    # CHARTS
    # -----------------------------------------------------------------------

    st.markdown("---")
    st.markdown("#### Benefit-Cost Ratio vs Number of Fixes")
    st.caption(
        "Green dashed line = 10:1 threshold. "
        "The curve flattens as lower-friction nodes are reached — "
        "revealing the point of diminishing returns."
    )
    fig_bcr = plot_bcr_curve(df, personas, bazaar_f, dark=True)
    st.pyplot(fig_bcr, use_container_width=True)
    plt.close(fig_bcr)

    st.markdown("---")

# -----------------------------------------------------------------------
    # PER-PERSONA TABLE
    # -----------------------------------------------------------------------
    st.markdown("#### Per-Persona Breakdown")
    rows = []
    for key, p in personas.items():
        r0   = econ["results0"][key]
        r    = econ["results"][key]
        l0   = M * W * r0["delta_tau"] / 60 * WAGE / 1e7
        l    = M * W * r["delta_tau"]  / 60 * WAGE / 1e7
        rows.append({
            "Persona":                          p["label"],
            "Weight":                           f"{p['weight']*100:.0f}%",
            "v₀ (m/s)":                         p["v0"],
            "k":                                p["k"],
            "f_max":                            p["f_max"],
            "Δτ baseline (s)":                  f"{r0['delta_tau']:.0f}",
            f"Δτ after {n_fixes} fix(es) (s)":  f"{r['delta_tau']:.0f}",
            "ROW detours (baseline)":           r0["n_detours"],
            "Annual loss — baseline (₹ Cr)":    f"{l0:.2f}",
            f"Annual loss — fixed (₹ Cr)":      f"{l:.2f}",
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    st.markdown("---")

    # -----------------------------------------------------------------------
    # DETAILED MATH EXPANDER
    # -----------------------------------------------------------------------
    with st.expander("📐 Full mathematical derivation"):

        st.markdown("##### Notation")
        st.markdown("""
        | Symbol | Meaning |
        |--------|---------|
        | $D = 900$ m | Total corridor length |
        | $d = 12.5$ m | Segment length ($D/N$, where $N = 72$ segments) |
        | $N_{300} = 24$ | Discrete obstacle nodes in the 300m stretch |
        | $N_{600} = 48$ | Uniform segments in the 600m Bazaar Street stretch |
        | $f_i \\in \\{1,2,3,4,5\\}$ | Friction value at segment $i$ |
        | $\\phi$ | Commuter persona |
        | $v_0(\\phi)$ | Free-walking speed of persona $\\phi$ (m/s) |
        | $k(\\phi)$ | Friction sensitivity exponent of persona $\\phi$ |
        | $f_{\\text{max}}(\\phi)$ | Impassability threshold — segments above this force ROW detour |
        | $\\delta(\\phi)$ | Mean detour length per impassable segment (m) |
        | $\\alpha = 1.5$ | Velocity penalty multiplier for walking in traffic |
        | $w_\\phi$ | Population share weight of persona $\\phi$ |
        | $M = 100{,}000$ | Daily commuters at Yeshwantpur hub |
        | $W = 250$ | Working days per year |
        """)

        st.markdown("##### Effective Path Length")
        st.markdown(
            "The friction field $f(x, \\phi)$ is treated as a continuous "
            "potential energy barrier. The **Effective Path Length** is its "
            "integral over the corridor:"
        )
        st.latex(
            r"L_{\text{eff}}(\phi) = \int_0^D f(x,\phi)\,dx "
            r"\;\approx\; d\sum_{i=1}^{N} f_i"
        )
        st.markdown(
            "For the Yeshwantpur survey, evaluated numerically over both zones:"
        )
        st.latex(
            r"L_{\text{eff}}^{300} = 12.5 \times "
            r"(9{\times}5 + 8{\times}4 + 4{\times}3 + 3{\times}2) "
            r"= 12.5 \times 95 = 1187.5\text{ m}"
        )
        st.latex(
            r"L_{\text{eff}}^{600} = 600 \times 5 = 3000\text{ m}"
        )
        st.latex(
            r"\bar{f} = \frac{L_{\text{eff}}}{D} = \frac{4187.5}{900} \approx 4.653"
        )

        st.markdown("##### Power-Law Velocity Model")
        st.markdown(
            "A linear speed reduction underestimates the compounding impact on "
            "vulnerable users. Instead, effective speed decays as a power law "
            "in the local friction value:"
        )
        st.latex(
            r"v_{\text{eff}}(i,\,\phi) = \frac{v_0(\phi)}{f_i^{\,k(\phi)}}"
        )
        st.markdown(
            "The exponent $k(\\phi)$ encodes how sensitively the persona responds "
            "to friction. A wheelchair user ($k=1.2$) loses speed super-linearly — "
            "at $f=5$: $v_{\\text{eff}} = 0.8 / 5^{1.2} = 0.117$ m/s, "
            "roughly one-seventh of free-walking speed. "
            "An able-bodied adult ($k=0.6$) at the same node: "
            "$v_{\\text{eff}} = 1.4 / 5^{0.6} = 0.490$ m/s."
        )

        st.markdown("##### Per-Segment Traversal Time")
        st.markdown(
            "For **passable** segments ($f_i \\leq f_{\\text{max}}$):"
        )
        st.latex(
            r"\tau_i(\phi) = \frac{d}{v_{\text{eff}}(i,\phi)} "
            r"= \frac{d \cdot f_i^{\,k(\phi)}}{v_0(\phi)}"
        )
        st.markdown(
            "For **impassable** segments ($f_i > f_{\\text{max}}$), "
            "the agent is rerouted into the vehicular Right-of-Way. "
            "The detour adds a geometric extra length $\\delta$ "
            "and a safety penalty multiplier $\\alpha = 1.5$:"
        )
        st.latex(
            r"\tau_i^{\text{ROW}}(\phi) "
            r"= \frac{(d + \delta(\phi)) \cdot \alpha}{v_0(\phi)}"
        )

        st.markdown("##### Time Tax per Trip")
        st.markdown(
            "Summing over all $N = 72$ segments gives the actual traversal time. "
            "The ideal time assumes $f=1$ throughout "
            "(a fully [Tender S.U.R.E.](https://www.janausp.org/portfolio/tender-sure)"
            "-compliant corridor):"
        )
        st.latex(
            r"T_{\text{actual}}(\phi) = \sum_{i=1}^{N} \tau_i(\phi)"
        )
        st.latex(
            r"T_{\text{ideal}}(\phi) = \frac{D}{v_0(\phi)}"
        )
        st.latex(
            r"\Delta\tau(\phi) = T_{\text{actual}} - T_{\text{ideal}} "
            r"= \frac{d}{v_0(\phi)} \left(\sum_{i=1}^{N} f_i^{\,k(\phi)} - N\right)"
        )

        st.markdown("##### Economic Aggregation")
        st.markdown(
            "The persona-weighted mean Time Tax, aggregated across all $M$ commuters "
            "and $W$ working days, then converted to economic value:"
        )
        st.latex(
            r"\bar{\Delta\tau} = "
            r"\frac{\displaystyle\sum_{\phi} w_\phi \cdot \Delta\tau(\phi)}"
            r"{\displaystyle\sum_{\phi} w_\phi}"
        )
        st.latex(
            r"\mathcal{T}_{\text{year}} = M \cdot W \cdot \bar{\Delta\tau}"
            r"\quad \text{(person-seconds/year)}"
        )
        st.latex(
            r"\text{Annual loss (₹)} = \frac{\mathcal{T}_{\text{year}}}{60} "
            r"\times \frac{50}{60}"
            r"\quad \left(\text{at ₹50/hr} = \frac{50}{60}\text{ ₹/min}\right)"
        )
        st.markdown(
            f"**Evaluated:** $\\bar{{\\Delta\\tau}} = {econ['delta_tau_bar0']:.1f}$ s/trip · "
            f"$\\mathcal{{T}}_{{\\text{{year}}}} = {econ['annual_pm0']/1e6:.2f}$ million person-minutes · "
            f"Annual loss = ₹{econ['annual_loss_cr0']:.2f} Cr"
        )

        st.markdown("##### What-If Delta (Lighthouse Proposal)")
        st.markdown(
            "Fixing the top $n$ hotspots to $f=1$ (S.U.R.E. standard), "
            "where nodes are ranked by $f_j^{k(\\phi)}$ descending:"
        )
        st.latex(
            r"\Delta\tau_{\text{saved}}(n,\phi) = "
            r"\frac{d}{v_0(\phi)} \sum_{j=1}^{n} \left(f_j^{\,k(\phi)} - 1\right)"
        )
        st.latex(
            r"\text{BCR} = \frac{M \cdot W \cdot \Delta\bar{\tau}_{\text{saved}} "
            r"\cdot \tfrac{50}{3600}}{\text{repair cost (₹)}}"
        )
        if n_fixes > 0:
            st.markdown(
                f"**For $n = {n_fixes}$ fixes:** "
                f"Time Tax recovered = {econ['pct_recovered']:.1f}% · "
                f"BCR = {econ['bcr_low']:.1f}:1 – {econ['bcr_high']:.1f}:1"
            )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # PDF DOWNLOAD
    # -----------------------------------------------------------------------
    st.markdown("#### Generate Policy Brief PDF")
    st.markdown(
        "2-page A4 brief formatted for submission to DULT, BBMP, "
        "and the MLA of the Yeshwantpur constituency. "
        "Includes all tables, charts, and the Lighthouse Proposal."
    )
    if st.button("📄 Generate PDF", type="primary"):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            generate_pdf(df, personas, pdf_fixes, bazaar_f, tmp_path)
            with open(tmp_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="⬇️ Download PDF",
                data=pdf_bytes,
                file_name=pdf_output,
                mime="application/pdf",
            )
            st.success("PDF generated successfully.")
        except Exception as e:
            st.error(f"PDF generation failed: {e}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


# -------------------------------------------------------------------------
# CLI ENTRY POINT
# -------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Yeshwantpur policy brief PDF headlessly."
    )
    parser.add_argument("--fixes",    type=int, default=3)
    parser.add_argument("--bazaar-f", type=int, default=5)
    parser.add_argument("--output",   type=str, default="brief.pdf")
    args = parser.parse_args()

    df       = load_audit_data()
    personas = load_personas()
    generate_pdf(df, personas, args.fixes, args.bazaar_f, args.output)
