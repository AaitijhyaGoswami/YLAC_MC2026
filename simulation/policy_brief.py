"""
policy_brief.py
===============
Dual-mode module:

    Streamlit  : called via app() from streamlit_app.py
    Headless   : python simulations/policy_brief.py --fixes 3 --output brief.pdf

Computes the aggregate Time Tax, annual economic loss, and benefit-to-cost
ratio for the Yeshwantpur corridor, and generates a submission-ready 2-page
PDF policy brief for DULT/BBMP.
"""

import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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

M     = 100_000   # daily commuters at Yeshwantpur hub
W     = 250       # working days per year
WAGE  = 50 / 60   # RBI informal wage rate — ₹50/hr → ₹/min

FIX_COST_LOW_LAKH  = 8    # estimated repair cost lower bound (₹ lakh)
FIX_COST_HIGH_LAKH = 12   # estimated repair cost upper bound (₹ lakh)

# -------------------------------------------------------------------------
# DATA LOADERS  (no @st.cache_data here — used headlessly too)
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
# SIMULATION CORE  (mirrors agent_sim.py — kept local to stay headless-safe)
# -------------------------------------------------------------------------

def build_f_array(df: pd.DataFrame, n_fixes: int, bazaar_f: int = 5) -> np.ndarray:
    f_300 = df["f_value"].values.astype(float)
    if n_fixes > 0:
        fix_idx = np.argsort(f_300)[::-1][:n_fixes]
        f_300 = f_300.copy()
        f_300[fix_idx] = 1.0
    return np.concatenate([f_300, np.full(N_600, float(bazaar_f))])


def run_simulation(f_array: np.ndarray, persona: dict) -> dict:
    v0, k = persona["v0"], persona["k"]
    f_max, alpha, delta_m = persona["f_max"], persona["alpha"], persona["delta"]
    tau_i = np.empty(len(f_array))
    is_det = np.zeros(len(f_array), dtype=bool)
    for i, fi in enumerate(f_array):
        if fi > f_max:
            tau_i[i] = (d + delta_m) * alpha / v0
            is_det[i] = True
        else:
            tau_i[i] = d * (fi ** k) / v0
    T_actual  = float(tau_i.sum())
    T_ideal   = D / v0
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
    """
    Aggregate Time Tax and annual economic loss.

    Returns
    -------
    dict with keys:
        results          : per-persona simulation dicts
        delta_tau_bar    : float — persona-weighted mean Time Tax (s)
        annual_pm        : float — annual person-minutes lost
        annual_loss_rs   : float — annual loss in ₹
        annual_loss_cr   : float — annual loss in ₹ crore
        pct_recovered    : float — % loss recovered vs baseline (if n_fixes>0)
        bcr_low          : float — benefit-cost ratio (high cost)
        bcr_high         : float — benefit-cost ratio (low cost)
    """
    f_array  = build_f_array(df, n_fixes, bazaar_f)
    f_base   = build_f_array(df, 0, 5)

    results  = {k: run_simulation(f_array, v) for k, v in personas.items()}
    results0 = {k: run_simulation(f_base,  v) for k, v in personas.items()}

    total_w = sum(p["weight"] for p in personas.values())

    def weighted_mean(res):
        return sum(res[k]["delta_tau"] * personas[k]["weight"]
                   for k in personas) / total_w

    dtau_bar  = weighted_mean(results)
    dtau_bar0 = weighted_mean(results0)

    annual_pm  = M * W * dtau_bar / 60
    annual_pm0 = M * W * dtau_bar0 / 60

    annual_loss_rs = annual_pm  * WAGE * 60  # back to ₹/s * seconds
    annual_loss_rs = M * W * dtau_bar / 60 * WAGE * 60
    # Simpler: person-minutes × ₹/min
    annual_loss_rs  = annual_pm  * WAGE
    annual_loss_rs0 = annual_pm0 * WAGE

    annual_loss_cr  = annual_loss_rs  / 1e7
    annual_loss_cr0 = annual_loss_rs0 / 1e7

    pct_recovered = (
        (annual_loss_rs0 - annual_loss_rs) / annual_loss_rs0 * 100
        if n_fixes > 0 or bazaar_f < 5 else 0.0
    )

    recovered_lakh = (annual_loss_rs0 - annual_loss_rs) / 1e5
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
# PLOT HELPERS
# -------------------------------------------------------------------------

def plot_time_tax_bars(results: dict, personas: dict) -> plt.Figure:
    """Horizontal bar — Time Tax per persona (minutes)."""
    labels = [p["label"] for p in personas.values()]
    taxes  = [results[k]["delta_tau"] / 60 for k in personas]
    colors = [p["color"] for p in personas.values()]

    fig, ax = plt.subplots(figsize=(7, 3))
    bars = ax.barh(labels, taxes, color=colors, height=0.5, linewidth=0)
    for bar, val in zip(bars, taxes):
        ax.text(val + 0.05, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f} min", va="center", fontsize=8.5, color="white")
    ax.set_xlabel("Time Tax per trip (min)", fontsize=9, color="white")
    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white", labelsize=9)
    ax.xaxis.label.set_color("white")
    ax.spines[:].set_visible(False)
    fig.tight_layout()
    return fig


def plot_friction_distribution(df: pd.DataFrame) -> plt.Figure:
    """Pie chart of f-value distribution across the 300m stretch."""
    F_COLORS = {2: "#4CAF50", 3: "#2196F3", 4: "#FF9800", 5: "#F44336"}
    counts = df["f_value"].value_counts().sort_index()
    colors = [F_COLORS.get(int(f), "#9E9E9E") for f in counts.index]
    labels = [f"f={int(f)}" for f in counts.index]

    fig, ax = plt.subplots(figsize=(4, 4))
    wedges, texts, autotexts = ax.pie(
        counts.values, labels=labels, colors=colors,
        autopct="%1.1f%%", startangle=140,
        textprops={"color": "white", "fontsize": 9},
    )
    for at in autotexts:
        at.set_color("white")
        at.set_fontsize(8)
    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.set_title("Obstacle Distribution\n300m stretch", color="white", fontsize=9)
    fig.tight_layout()
    return fig


def plot_bcr_waterfall(econ: dict, n_range: int = 10) -> plt.Figure:
    """
    BCR curve — how the benefit-cost ratio changes as n_fixes increases
    from 0 to n_range. Helps identify the point of diminishing returns.
    """
    # Recompute BCR for each n (uses baseline data from econ dict)
    # We need df and personas — pass them through econ dict
    df       = econ["_df"]
    personas = econ["_personas"]
    bazaar_f = econ["bazaar_f"]

    bcr_vals = []
    for n in range(0, n_range + 1):
        e = compute_economics(df, personas, n, bazaar_f)
        bcr_vals.append((e["bcr_low"] + e["bcr_high"]) / 2)

    fig, ax = plt.subplots(figsize=(7, 3))
    ax.plot(range(n_range + 1), bcr_vals, color="#FF9800",
            linewidth=2.5, marker="o", markersize=5)
    ax.axhline(10, color="#4CAF50", linewidth=1, linestyle="--",
               label="BCR = 10:1 threshold")
    ax.fill_between(range(n_range + 1), bcr_vals, 0,
                    alpha=0.15, color="#FF9800")
    ax.set_xlabel("Number of hotspots fixed (top-N)", fontsize=9, color="white")
    ax.set_ylabel("Benefit-Cost Ratio", fontsize=9, color="white")
    ax.legend(fontsize=8, facecolor="#2a2a2a", labelcolor="white")
    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white", labelsize=8)
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.spines[:].set_visible(False)
    fig.tight_layout()
    return fig


# -------------------------------------------------------------------------
# PDF GENERATOR  (headless, uses ReportLab)
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

    Page 1 — Audit findings: friction distribution pie, per-persona Time Tax bar,
              key statistics table.
    Page 2 — Lighthouse Proposal: what-if delta table, BCR argument,
              cost estimate, submission boilerplate.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            Image, HRFlowable,
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
    except ImportError:
        print("ReportLab not installed. Run: pip install reportlab")
        sys.exit(1)

    import io
    econ = compute_economics(df, personas, n_fixes, bazaar_f)

    # --- Save charts to in-memory buffers ---
    fig_pie  = plot_friction_distribution(df)
    fig_bars = plot_time_tax_bars(econ["results"], personas)

    buf_pie  = io.BytesIO()
    buf_bars = io.BytesIO()
    fig_pie.savefig(buf_pie,  format="png", dpi=150, bbox_inches="tight")
    fig_bars.savefig(buf_bars, format="png", dpi=150, bbox_inches="tight")
    buf_pie.seek(0);  buf_bars.seek(0)
    plt.close(fig_pie); plt.close(fig_bars)

    # --- Document setup ---
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2.5*cm, rightMargin=2.5*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    styles = getSampleStyleSheet()
    H1  = ParagraphStyle("H1",  parent=styles["Heading1"], fontSize=14,
                          spaceAfter=6)
    H2  = ParagraphStyle("H2",  parent=styles["Heading2"], fontSize=11,
                          spaceAfter=4)
    BODY = ParagraphStyle("BODY", parent=styles["Normal"],  fontSize=9,
                           leading=14, spaceAfter=6)
    SMALL = ParagraphStyle("SMALL", parent=styles["Normal"], fontSize=8,
                            leading=12, textColor=colors.grey)

    story = []

    # ---- PAGE 1 ----
    story.append(Paragraph("Escape the Knot: Yeshwantpur Mobility Audit", H1))
    story.append(Paragraph(
        "Student-Led Pedestrian Infrastructure Audit — YLAC Mobility Champions 2026 · Bengawalk",
        SMALL
    ))
    story.append(Paragraph(
        "Survey conducted: 7–8 March 2026 · 900m Yeshwantpur–Constitution Circle corridor",
        SMALL
    ))
    story.append(HRFlowable(width="100%", thickness=0.5, spaceAfter=10))

    story.append(Paragraph("1. Audit Findings", H2))
    story.append(Paragraph(
        f"The surveyed corridor was assigned friction values f ∈ {{1,2,3,4,5}} per the "
        f"Active Mobility Bill rubric. The mean friction index evaluates to "
        f"f̄ = 4.653, meaning the corridor imposes 4.65× the energetic cost "
        f"of a fully Tender S.U.R.E.-compliant footpath. "
        f"90.3% of the stretch fails Active Mobility Bill standards; "
        f"96% is inaccessible for wheelchair users.",
        BODY
    ))

    # Key stats table
    stats_data = [
        ["Metric", "Value"],
        ["Survey length", "900m (300m discrete + 600m continuous f=5)"],
        ["Geotagged obstacle nodes", "24 (300m stretch only)"],
        ["Mean friction index f̄", "4.653"],
        ["Fails Active Mobility Bill", "90.3%"],
        ["Wheelchair inaccessible", "96.0%"],
        ["Nodes at f=5 (Systemic Failure)", "9 / 24 (37.5%)"],
        ["Nodes at f=4 (Physical Barrier)", "8 / 24 (33.3%)"],
        ["600m Bazaar Street stretch", "Continuous f=5 — footpath absent"],
    ]
    t = Table(stats_data, colWidths=[8*cm, 9*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  colors.HexColor("#333333")),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
        ("FONTSIZE",    (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#f9f9f9"), colors.white]),
        ("GRID",        (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",(0, 0), (-1, -1), 6),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0),(-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.4*cm))

    # Charts side by side
    story.append(Paragraph("Obstacle Distribution (300m) & Per-Persona Time Tax", H2))
    chart_table = Table(
        [[Image(buf_pie, width=7*cm, height=7*cm),
          Image(buf_bars, width=9*cm, height=5*cm)]],
        colWidths=[7.5*cm, 9.5*cm],
    )
    story.append(chart_table)
    story.append(Spacer(1, 0.3*cm))

    # ---- PAGE 2 ----
    from reportlab.platypus import PageBreak
    story.append(PageBreak())

    story.append(Paragraph("2. Economic Impact", H2))
    story.append(Paragraph(
        f"Using the persona-weighted mean Time Tax "
        f"Δτ̄ = {econ['delta_tau_bar0']:.1f}s per trip, "
        f"aggregated across M = {M:,} daily commuters and W = {W} working days "
        f"at the RBI informal wage rate (~₹50/hr):",
        BODY
    ))

    econ_data = [
        ["Metric", "Value"],
        ["Weighted mean Time Tax Δτ̄", f"{econ['delta_tau_bar0']:.1f} s/trip"],
        ["Annual person-minutes lost", f"{econ['annual_pm0']/1e6:.1f} million"],
        ["Annual productivity loss",
         f"₹{econ['annual_loss_cr0']:.1f} crore (~₹{econ['annual_loss_cr0']*100:.0f} lakh)"],
    ]
    # Per-persona breakdown
    for key, p in personas.items():
        r = econ["results0"][key]
        loss = M * W * r["delta_tau"] / 60 * WAGE / 1e7
        econ_data.append([
            f"  {p['label']} (weight {p['weight']})",
            f"Δτ = {r['delta_tau']:.0f}s · ₹{loss:.2f} Cr/yr",
        ])

    t2 = Table(econ_data, colWidths=[9*cm, 8*cm])
    t2.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  colors.HexColor("#333333")),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
        ("FONTSIZE",    (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#f9f9f9"), colors.white]),
        ("GRID",        (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",(0, 0), (-1, -1), 6),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0),(-1, -1), 4),
    ]))
    story.append(t2)
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("3. Lighthouse Proposal", H2))
    story.append(Paragraph(
        f"Fixing the top {n_fixes} friction hotspots to Tender S.U.R.E. standard "
        f"(f=1) — estimated cost ₹{FIX_COST_LOW_LAKH}–{FIX_COST_HIGH_LAKH} lakh "
        f"for drain covers and slab repair — recovers "
        f"{econ['pct_recovered']:.1f}% of the annual Time Tax.",
        BODY
    ))

    lighthouse_data = [
        ["Parameter", "Current", f"After {n_fixes} fixes"],
        ["Weighted mean Δτ̄",
         f"{econ['delta_tau_bar0']:.1f}s", f"{econ['delta_tau_bar']:.1f}s"],
        ["Annual person-minutes lost",
         f"{econ['annual_pm0']/1e6:.1f}M", f"{econ['annual_pm']/1e6:.1f}M"],
        ["Annual productivity loss",
         f"₹{econ['annual_loss_cr0']:.1f} Cr", f"₹{econ['annual_loss_cr']:.1f} Cr"],
        ["% of Time Tax recovered", "—", f"{econ['pct_recovered']:.1f}%"],
        ["Repair cost estimate", "—",
         f"₹{FIX_COST_LOW_LAKH}–{FIX_COST_HIGH_LAKH} lakh"],
        ["Benefit-cost ratio", "—",
         f"{econ['bcr_low']:.1f}:1 – {econ['bcr_high']:.1f}:1"],
    ]
    t3 = Table(lighthouse_data, colWidths=[7*cm, 5*cm, 5*cm])
    t3.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  colors.HexColor("#333333")),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
        ("FONTSIZE",    (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#f9f9f9"), colors.white]),
        ("GRID",        (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",(0, 0), (-1, -1), 6),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0),(-1, -1), 4),
    ]))
    story.append(t3)
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("4. Policy Ask", H2))
    story.append(Paragraph(
        "We request that DULT and BBMP initiate a Lighthouse Pilot project at the "
        "Yeshwantpur Mobility Knot, mandating Tender S.U.R.E. Design Standards on the "
        "900m Constitution Circle–Railway Station corridor. The specific ask is: "
        "(1) replace open box drains with integrated Pipe and Chamber systems; "
        "(2) restore continuous 3m footpath width on Bazaar Street; "
        "(3) install kerb ramps at all crossing points per IRC 103 guidelines. "
        "A benefit-to-cost ratio exceeding 10:1 makes this the highest-return "
        "pedestrian infrastructure investment available to the hub.",
        BODY
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, spaceAfter=6))
    story.append(Paragraph(
        "Submitted by: Aaitijhya Goswami & Prajwal Kagalgomb · "
        "YLAC Mobility Champions 2026 · Partner: Bengawalk · "
        "Data: March 7–8, 2026 field audit",
        SMALL
    ))

    doc.build(story)
    print(f"PDF written to: {output_path}")


# -------------------------------------------------------------------------
# STREAMLIT APP ENTRY POINT
# -------------------------------------------------------------------------

def app():
    import streamlit as st

    # Lazy-import so headless use doesn't require streamlit
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
            "This is the number of hotspot fixes costed in the PDF."
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
            "📋 Default Lighthouse Pilot scenario: fix 3 obstacles for "
            f"₹{FIX_COST_LOW_LAKH}–{FIX_COST_HIGH_LAKH} lakh, recover "
            "~38% of annual Time Tax."
        )
    elif n_fixes == 0:
        st.sidebar.caption("📋 Showing baseline surveyed conditions.")
    else:
        st.sidebar.caption(
            f"📋 Custom scenario: {n_fixes} fixes. "
            "Adjust to explore different intervention sizes."
        )

    st.sidebar.markdown("---")
    st.sidebar.markdown("**PDF settings**")
    pdf_fixes = st.sidebar.number_input(
        "n_fixes for PDF export:",
        min_value=0, max_value=len(df), value=n_fixes, step=1,
    )
    pdf_output = st.sidebar.text_input("Output filename:", value="brief.pdf")

    # -----------------------------------------------------------------------
    # COMPUTE
    # -----------------------------------------------------------------------
    econ = compute_economics(df, personas, n_fixes, bazaar_f)
    econ["_df"]       = df
    econ["_personas"] = personas

    # -----------------------------------------------------------------------
    # HEADLINE METRICS
    # -----------------------------------------------------------------------
    st.markdown("#### Annual Economic Impact — Baseline Conditions")

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Annual person-minutes lost",
        f"{econ['annual_pm0']/1e6:.1f}M",
        help=f"M × W × Δτ̄ / 60 = {M:,} × {W} × {econ['delta_tau_bar0']:.1f}s / 60"
    )
    col2.metric(
        "Annual productivity loss",
        f"₹{econ['annual_loss_cr0']:.1f} Cr",
        help="Person-minutes × ₹50/hr wage rate"
    )
    col3.metric(
        "Δτ̄ (weighted mean Time Tax)",
        f"{econ['delta_tau_bar0']:.1f} s/trip",
        help="Weighted across 4 personas by population share."
    )

    st.markdown("---")
    st.markdown("#### Lighthouse Proposal — Impact of Fixes")

    col4, col5, col6 = st.columns(3)
    col4.metric(
        f"Loss after {n_fixes} fixes",
        f"₹{econ['annual_loss_cr']:.1f} Cr",
        delta=f"−₹{econ['annual_loss_cr0'] - econ['annual_loss_cr']:.2f} Cr",
        delta_color="normal",
    )
    col5.metric(
        "Time Tax recovered",
        f"{econ['pct_recovered']:.1f}%",
    )
    col6.metric(
        "Benefit-cost ratio",
        f"{econ['bcr_low']:.1f}–{econ['bcr_high']:.1f} : 1",
        help=f"Annual saving / repair cost (₹{FIX_COST_LOW_LAKH}–{FIX_COST_HIGH_LAKH} lakh)"
    )

    if econ["pct_recovered"] > 0:
        st.success(
            f"Fixing the top {n_fixes} hotspot(s) to "
            "[Tender S.U.R.E.](https://www.janausp.org/portfolio/tender-sure) "
            f"standard recovers **{econ['pct_recovered']:.1f}%** of the annual "
            f"Time Tax at a benefit-to-cost ratio of "
            f"**{econ['bcr_low']:.1f}:1 – {econ['bcr_high']:.1f}:1**."
        )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # CHARTS
    # -----------------------------------------------------------------------
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("#### Friction Distribution — 300m Stretch")
        fig_pie = plot_friction_distribution(df)
        st.pyplot(fig_pie, use_container_width=True)
        plt.close(fig_pie)

    with col_r:
        st.markdown("#### Time Tax per Persona")
        fig_bars = plot_time_tax_bars(econ["results"], personas)
        st.pyplot(fig_bars, use_container_width=True)
        plt.close(fig_bars)

    st.markdown("---")
    st.markdown("#### Benefit-Cost Ratio vs Number of Fixes")
    st.caption(
        "Shows how BCR changes as more hotspots are brought to S.U.R.E. standard. "
        "Green dashed line = 10:1 threshold. "
        "The curve flattens as lower-friction nodes are reached."
    )
    fig_bcr = plot_bcr_waterfall(econ)
    st.pyplot(fig_bcr, use_container_width=True)
    plt.close(fig_bcr)

    st.markdown("---")

    # -----------------------------------------------------------------------
    # PER-PERSONA TABLE
    # -----------------------------------------------------------------------
    st.markdown("#### Per-Persona Breakdown")
    rows = []
    for key, p in personas.items():
        r0 = econ["results0"][key]
        r  = econ["results"][key]
        loss0 = M * W * r0["delta_tau"] / 60 * WAGE / 1e7
        loss  = M * W * r["delta_tau"]  / 60 * WAGE / 1e7
        rows.append({
            "Persona":            p["label"],
            "Pop. weight":        f"{p['weight']*100:.0f}%",
            "Δτ baseline (s)":    f"{r0['delta_tau']:.0f}",
            f"Δτ after {n_fixes} fixes (s)": f"{r['delta_tau']:.0f}",
            "Annual loss — baseline (₹ Cr)": f"{loss0:.2f}",
            f"Annual loss — fixed (₹ Cr)":   f"{loss:.2f}",
            "ROW detours":        str(r0["n_detours"]),
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    st.markdown("---")

    # -----------------------------------------------------------------------
    # AGGREGATION FORMULA EXPANDER
    # -----------------------------------------------------------------------
    with st.expander("📐 Show aggregation formulae"):
        st.markdown("**Persona-weighted mean Time Tax:**")
        st.latex(
            r"\bar{\Delta\tau} = "
            r"\frac{\sum_{\phi} w_\phi \cdot \Delta\tau(\phi)}{\sum_\phi w_\phi}"
            rf"= {econ['delta_tau_bar0']:.1f} \text{{ s (baseline)}}"
        )
        st.markdown("**Annual aggregate Time Tax:**")
        st.latex(
            r"\mathcal{T}_{\text{year}} = M \cdot W \cdot \bar{\Delta\tau} "
            rf"= {M:,} \times {W} \times {econ['delta_tau_bar0']:.1f}"
            rf"= {M * W * econ['delta_tau_bar0']:,.0f} \text{{ person-seconds}}"
        )
        st.markdown("**Economic value at ₹50/hr:**")
        st.latex(
            r"\text{Loss} = \mathcal{T}_{\text{year}} \div 60 \times \frac{50}{60}"
            rf"\approx \text{{₹}}{econ['annual_loss_cr0']:.1f} \text{{ Cr/yr}}"
        )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # PDF DOWNLOAD
    # -----------------------------------------------------------------------
    st.markdown("#### Generate Policy Brief PDF")
    st.markdown(
        "Produces a 2-page A4 brief formatted for submission to DULT, BBMP, "
        "and the MLA of the Yeshwantpur constituency."
    )
    if st.button("📄 Generate PDF", type="primary"):
        import io as _io
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            generate_pdf(df, personas, pdf_fixes, bazaar_f, tmp_path)
            with open(tmp_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="⬇️ Download brief.pdf",
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
    parser.add_argument(
        "--fixes", type=int, default=3,
        help="Number of top-ranked hotspots to fix (default: 3)"
    )
    parser.add_argument(
        "--bazaar-f", type=int, default=5,
        help="f-value to assign to the 600m Bazaar Street stretch (default: 5)"
    )
    parser.add_argument(
        "--output", type=str, default="brief.pdf",
        help="Output PDF path (default: brief.pdf)"
    )
    args = parser.parse_args()

    df       = load_audit_data()
    personas = load_personas()
    generate_pdf(df, personas, args.fixes, args.bazaar_f, args.output)
