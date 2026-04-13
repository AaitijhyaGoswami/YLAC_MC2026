"""
policy_brief.py
===============
Economic Impact & Policy Brief module for the Escape the Knot dashboard.
PDF generation has been removed. Streamlit entry point: app()

Economics model notes
---------------------
Baseline: always (n_fixes=0, bazaar_f=5) — surveyed conditions.
Scenario: n_fixes hotspots fixed to f=1, Bazaar Street at bazaar_f.

pct_recovered can be negative: lowering bazaar_f can worsen some personas'
Time Tax. At bazaar_f=4, elderly (k=0.9, f_max=4) and delivery (k=0.75,
f_max=4) become passable but slow (d*4^k/v0) instead of triggering the
cheaper ROW detour ((d+delta)*alpha/v0). This is physically correct.

BCR is only computed when n_fixes > 0. Toggling bazaar_f alone has no
associated repair cost. Repair cost scales linearly with n_fixes at rate
FIX_COST_PER_3_FIXES / 3 per fix, ensuring the BCR curve is monotonic.
"""

import os

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
WAGE = 50 / 60  # RBI informal wage rate — Rs50/hr -> Rs/min

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
    """
    Build the 72-element friction array for the full 900m corridor.
    Segments 0-23  : 300m stretch, discrete nodes from audit_log.csv.
                     Top n_fixes nodes (by descending f_value) set to f=1.
    Segments 24-71 : 600m Bazaar Street stretch, uniform at bazaar_f.
    """
    f_300 = df["f_value"].values.astype(float)
    if n_fixes > 0:
        fix_idx = np.argsort(f_300)[::-1][:n_fixes]
        f_300 = f_300.copy()
        f_300[fix_idx] = 1.0
    return np.concatenate([f_300, np.full(N_600, float(bazaar_f))])


def run_simulation(f_array: np.ndarray, persona: dict) -> dict:
    """
    Power-law friction-velocity model for one persona.

    Passable (f_i <= f_max):  tau_i = d * f_i^k / v0
    Impassable (f_i > f_max): tau_i = (d + delta) * alpha / v0  [ROW detour]

    Note: the ROW detour formula can produce a SMALLER tau than the passable
    formula at moderate f with high k. Example:
      elderly (k=0.9, f_max=4) at f=4:
        passable  tau = 12.5 * 4^0.9 / 0.9 = 57.4s
        ROW @f=5  tau = (12.5+10)*1.5/0.9  = 37.5s
    So lowering Bazaar Street from f=5 to f=4 makes elderly SLOWER. Correct.
    """
    v0    = persona["v0"]
    k     = persona["k"]
    f_max = persona["f_max"]
    alpha = persona["alpha"]
    delta = persona["delta"]

    tau_i  = np.empty(len(f_array))
    is_det = np.zeros(len(f_array), dtype=bool)

    for i, fi in enumerate(f_array):
        if fi > f_max:
            tau_i[i]  = (d + delta) * alpha / v0
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
        "tau_i":     tau_i,
        "is_det":    is_det,
    }


# -------------------------------------------------------------------------
# ECONOMIC MODEL
# -------------------------------------------------------------------------

def compute_economics(
    df: pd.DataFrame,
    personas: dict,
    n_fixes: int,
    bazaar_f: int = 5,
) -> dict:
    """
    Compute all economic metrics for a given scenario vs the fixed baseline.

    Baseline: n_fixes=0, bazaar_f=5 (surveyed conditions, never changes).
    Scenario: n_fixes hotspots fixed, Bazaar Street at bazaar_f.

    pct_recovered: positive = improvement, negative = scenario worsens.
    BCR: only computed when n_fixes > 0. Zero otherwise.
    """
    f_scenario = build_f_array(df, n_fixes, bazaar_f)
    f_baseline = build_f_array(df, 0, 5)          # always surveyed conditions

    res_s = {k: run_simulation(f_scenario, v) for k, v in personas.items()}
    res_b = {k: run_simulation(f_baseline, v) for k, v in personas.items()}

    total_w = sum(p["weight"] for p in personas.values())

    def weighted_mean_dtau(res):
        return sum(
            res[k]["delta_tau"] * personas[k]["weight"] for k in personas
        ) / total_w

    dtau_bar_s = weighted_mean_dtau(res_s)
    dtau_bar_b = weighted_mean_dtau(res_b)

    annual_pm_s = M * W * dtau_bar_s / 60    # person-minutes
    annual_pm_b = M * W * dtau_bar_b / 60

    annual_loss_cr_s = annual_pm_s * WAGE / 1e7   # Rs crore
    annual_loss_cr_b = annual_pm_b * WAGE / 1e7

    pct_recovered = (
        (annual_loss_cr_b - annual_loss_cr_s) / annual_loss_cr_b * 100
        if annual_loss_cr_b > 0 else 0.0
    )

    # BCR only when physical fixes are applied
    if n_fixes > 0:
        cost_low_lakh  = FIX_COST_LOW_LAKH  * n_fixes / 3
        cost_high_lakh = FIX_COST_HIGH_LAKH * n_fixes / 3
        saving_lakh = (annual_loss_cr_b - annual_loss_cr_s) * 100
        bcr_low  = saving_lakh / cost_high_lakh if cost_high_lakh > 0 else 0.0
        bcr_high = saving_lakh / cost_low_lakh  if cost_low_lakh  > 0 else 0.0
    else:
        bcr_low = bcr_high = saving_lakh = 0.0

    persona_losses = {
        key: {
            "baseline": M * W * res_b[key]["delta_tau"] / 60 * WAGE / 1e7,
            "scenario": M * W * res_s[key]["delta_tau"] / 60 * WAGE / 1e7,
        }
        for key in personas
    }

    return {
        "res_scenario":     res_s,
        "res_baseline":     res_b,
        "dtau_bar_s":       dtau_bar_s,
        "dtau_bar_b":       dtau_bar_b,
        "annual_pm_s":      annual_pm_s,
        "annual_pm_b":      annual_pm_b,
        "annual_loss_cr_s": annual_loss_cr_s,
        "annual_loss_cr_b": annual_loss_cr_b,
        "pct_recovered":    pct_recovered,
        "bcr_low":          bcr_low,
        "bcr_high":         bcr_high,
        "saving_lakh":      saving_lakh,
        "persona_losses":   persona_losses,
        "n_fixes":          n_fixes,
        "bazaar_f":         bazaar_f,
    }


# -------------------------------------------------------------------------
# PLOT HELPERS
# -------------------------------------------------------------------------

def plot_time_tax_bars(res_b: dict, res_s: dict, personas: dict) -> plt.Figure:
    """Grouped horizontal bars — baseline vs scenario Time Tax per persona."""
    labels  = [p["label"] for p in personas.values()]
    taxes_b = [res_b[k]["delta_tau"] / 60 for k in personas]
    taxes_s = [res_s[k]["delta_tau"] / 60 for k in personas]
    colors  = [p["color"] for p in personas.values()]

    max_tax = max(max(taxes_b), max(taxes_s), 0.5)
    n = len(labels)
    y = np.arange(n)
    h = 0.35

    fig, ax = plt.subplots(figsize=(8, 3.5))
    fig.patch.set_facecolor("#1a1a1a")
    ax.set_facecolor("#1a1a1a")

    ax.barh(y + h/2, taxes_b, height=h, color=colors, alpha=0.35,
            linewidth=0, label="Baseline (surveyed)")
    ax.barh(y - h/2, taxes_s, height=h, color=colors, alpha=0.9,
            linewidth=0, label="Scenario")

    for i, (vb, vs) in enumerate(zip(taxes_b, taxes_s)):
        ax.text(max_tax * 0.015, y[i] + h/2, f"{vb:.1f}m",
                va="center", fontsize=7, color="#aaaaaa")
        col = "#4CAF50" if vs <= vb else "#F44336"
        ax.text(max_tax * 0.015, y[i] - h/2, f"{vs:.1f}m",
                va="center", fontsize=7, color=col)

    ax.set_xlim(0, max_tax * 1.3)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8.5, color="white")
    ax.set_xlabel("Time Tax per trip (min)", fontsize=9, color="white")
    ax.tick_params(colors="white", labelsize=8)
    ax.xaxis.label.set_color("white")
    ax.legend(fontsize=7.5, facecolor="#2a2a2a", labelcolor="white",
              framealpha=0.85, loc="lower right")
    ax.spines[:].set_visible(False)
    fig.tight_layout()
    return fig


def plot_loss_waterfall(econ: dict, personas: dict) -> plt.Figure:
    """Bar chart of per-persona annual loss change vs baseline."""
    PCOLORS = {"able_bodied":"#2196F3","elderly":"#FF9800",
               "wheelchair":"#9C27B0","delivery":"#F44336"}
    PLABELS = {"able_bodied":"Able-bodied","elderly":"Elderly",
               "wheelchair":"Wheelchair","delivery":"Delivery"}

    keys    = list(econ["persona_losses"].keys())
    deltas  = [econ["persona_losses"][k]["baseline"] -
               econ["persona_losses"][k]["scenario"] for k in keys]
    cats    = [PLABELS.get(k, k) for k in keys]
    colors  = ["#4CAF50" if d >= 0 else "#F44336" for d in deltas]

    max_abs = max(abs(d) for d in deltas) if deltas else 1.0

    fig, ax = plt.subplots(figsize=(7, 3))
    fig.patch.set_facecolor("#1a1a1a")
    ax.set_facecolor("#1a1a1a")

    bars = ax.bar(cats, deltas, color=colors, linewidth=0, width=0.5)
    ax.axhline(0, color="#555", linewidth=0.8)

    for bar, val in zip(bars, deltas):
        va  = "bottom" if val >= 0 else "top"
        off = max_abs * 0.03 * (1 if val >= 0 else -1)
        ax.text(bar.get_x() + bar.get_width() / 2, val + off,
                f"{'−' if val < 0 else '+'}Rs{abs(val):.2f}Cr",
                ha="center", va=va, fontsize=7.5, color="white")

    ax.set_ylabel("Annual loss change (Rs Cr)", fontsize=9, color="white")
    ax.set_title("Per-Persona Loss Delta vs Baseline  (positive = improvement)",
                 fontsize=8, color="#aaaaaa", pad=4)
    ax.tick_params(colors="white", labelsize=8)
    ax.yaxis.label.set_color("white")
    ax.spines[:].set_visible(False)
    fig.tight_layout()
    return fig


def plot_bcr_curve(df: pd.DataFrame, personas: dict,
                   bazaar_f: int, n_range: int = 10) -> plt.Figure:
    """BCR midpoint vs n_fixes. Y-axis floored at 0."""
    bcr_vals = []
    for n in range(n_range + 1):
        e = compute_economics(df, personas, n, bazaar_f)
        bcr_vals.append((e["bcr_low"] + e["bcr_high"]) / 2)

    fig, ax = plt.subplots(figsize=(7, 3))
    fig.patch.set_facecolor("#1a1a1a")
    ax.set_facecolor("#1a1a1a")

    xs = list(range(n_range + 1))
    ax.plot(xs, bcr_vals, color="#FF9800", linewidth=2.5,
            marker="o", markersize=5, zorder=3)
    ax.fill_between(xs, [max(v, 0) for v in bcr_vals], 0,
                    alpha=0.12, color="#FF9800")
    ax.axhline(10, color="#4CAF50", linewidth=1, linestyle="--",
               label="BCR = 10:1 threshold", alpha=0.8)

    if n_range >= 3 and bcr_vals[3] > 0:
        ax.annotate(
            f"Lighthouse Pilot\nn=3 -> BCR {bcr_vals[3]:.1f}:1",
            xy=(3, bcr_vals[3]),
            xytext=(3.5, bcr_vals[3] + max(0, max(bcr_vals)) * 0.1),
            fontsize=7, color="#FF9800",
            arrowprops=dict(arrowstyle="->", color="#FF9800", lw=1),
        )

    ax.set_xlabel("Number of hotspots fixed (top-N)", fontsize=9, color="white")
    ax.set_ylabel("Benefit-Cost Ratio", fontsize=9, color="white")
    ax.set_xlim(-0.3, n_range + 0.3)
    ax.set_ylim(0, max(max(bcr_vals) * 1.2, 15))
    ax.legend(fontsize=8, facecolor="#2a2a2a", labelcolor="white", framealpha=0.85)
    ax.tick_params(colors="white", labelsize=8)
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.spines[:].set_visible(False)
    fig.tight_layout()
    return fig


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
        "commuters and $W = 250$ working days, converted to economic value at the "
        "RBI informal wage rate (~Rs50/hr)."
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
    st.sidebar.markdown("### Rs Economic Impact Controls")

    n_fixes = st.sidebar.slider(
        "Hotspots fixed (top-N by f-value):",
        min_value=0, max_value=len(df), value=3, step=1,
        help=(
            "Nodes ranked highest-f first. Each fix sets that node to f=1. "
            "BCR is only shown when n_fixes > 0."
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
        "Bazaar Street (600m) modelled as:",
        options=list(sure_standards.keys()),
        index=0,
    )
    bazaar_f = sure_standards[bazaar_label]

    if n_fixes == 0 and bazaar_f == 5:
        st.sidebar.caption("Showing baseline surveyed conditions.")
    elif n_fixes == 0 and bazaar_f < 5:
        st.sidebar.caption(
            f"Bazaar Street at f={bazaar_f}, no node fixes. "
            "Note: f=4 increases elderly/delivery Time Tax vs baseline — "
            "see explanation below."
        )
    else:
        cost_lo = FIX_COST_LOW_LAKH  * n_fixes / 3
        cost_hi = FIX_COST_HIGH_LAKH * n_fixes / 3
        st.sidebar.caption(
            f"{n_fixes} fix(es) — estimated Rs{cost_lo:.0f}–{cost_hi:.0f} lakh."
        )

    # -----------------------------------------------------------------------
    # COMPUTE
    # -----------------------------------------------------------------------
    econ     = compute_economics(df, personas, n_fixes, bazaar_f)
    improved = econ["pct_recovered"] >= 0

    # -----------------------------------------------------------------------
    # BASELINE METRICS
    # -----------------------------------------------------------------------
    st.markdown("#### Baseline — Surveyed Conditions")
    c1, c2, c3 = st.columns(3)
    c1.metric("Annual person-minutes lost",
              f"{econ['annual_pm_b']/1e6:.2f}M")
    c2.metric("Annual productivity loss",
              f"Rs{econ['annual_loss_cr_b']:.2f} Cr")
    c3.metric("Weighted mean Time Tax",
              f"{econ['dtau_bar_b']:.1f} s/trip")

    st.markdown("---")
    st.markdown("#### Scenario — After Fixes & Bazaar Adjustment")
    c4, c5, c6 = st.columns(3)

    delta_loss = econ["annual_loss_cr_b"] - econ["annual_loss_cr_s"]
    c4.metric(
        "Annual loss — scenario",
        f"Rs{econ['annual_loss_cr_s']:.2f} Cr",
        delta=f"{'−' if improved else '+'}Rs{abs(delta_loss):.2f} Cr",
        delta_color="normal" if improved else "inverse",
    )
    c5.metric(
        "Time Tax change vs baseline",
        f"{abs(econ['pct_recovered']):.1f}% {'recovered' if improved else 'worsened'}",
        delta=f"{econ['pct_recovered']:+.1f}%",
        delta_color="normal" if improved else "inverse",
    )
    if n_fixes > 0:
        bcr_mid = (econ["bcr_low"] + econ["bcr_high"]) / 2
        c6.metric(
            "Benefit-cost ratio",
            f"{econ['bcr_low']:.1f}–{econ['bcr_high']:.1f} : 1"
            if bcr_mid > 0 else "Negative — scenario worsens",
        )
    else:
        c6.metric("Benefit-cost ratio", "N/A — no fixes applied")

    # Contextual banners
    if n_fixes > 0 and improved and econ["bcr_low"] >= 10:
        st.success(
            f"Fixing the top {n_fixes} hotspot(s) to "
            "[Tender S.U.R.E.](https://www.janausp.org/portfolio/tender-sure) "
            f"standard recovers **{econ['pct_recovered']:.1f}%** of the annual "
            f"Time Tax at a BCR of **{econ['bcr_low']:.1f}:1 – "
            f"{econ['bcr_high']:.1f}:1**."
        )
    elif bazaar_f == 4 and n_fixes == 0:
        st.warning(
            "**Why does f=4 worsen the aggregate?** "
            "At f=5 (impassable), elderly and delivery personas take the ROW detour: "
            r"$\tau^\text{ROW} = (d+\delta)\cdot\alpha/v_0$. "
            "At f=4 (now passable), they traverse at "
            r"$\tau = d\cdot4^k/v_0$, which is **slower** for high-$k$ personas. "
            "Example — elderly at $f=4$: $12.5\\times4^{0.9}/0.9=57.4$s vs ROW "
            "at $f=5$: $(12.5+10)\\times1.5/0.9=37.5$s. "
            "This is physically correct, not a bug."
        )
    elif not improved and n_fixes > 0:
        st.info(
            f"The Bazaar Street setting (f={bazaar_f}) is worsening some personas "
            "more than the node fixes recover. Set Bazaar Street to Current (f=5) "
            "to isolate the effect of node fixes alone."
        )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # CHARTS
    # -----------------------------------------------------------------------
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("#### Time Tax — Baseline vs Scenario")
        st.caption("Light = baseline · Dark = scenario · Green value = improvement · Red = worsening")
        fig_bars = plot_time_tax_bars(econ["res_baseline"], econ["res_scenario"], personas)
        st.pyplot(fig_bars, use_container_width=True)
        plt.close(fig_bars)

    with col_r:
        st.markdown("#### Per-Persona Annual Loss Change")
        st.caption("Positive bar = loss reduced · Negative bar = loss increased vs baseline")
        fig_wf = plot_loss_waterfall(econ, personas)
        st.pyplot(fig_wf, use_container_width=True)
        plt.close(fig_wf)

    if n_fixes > 0:
        st.markdown("---")
        st.markdown("#### Benefit-Cost Ratio vs Number of Fixes")
        st.caption(
            "BCR for current Bazaar Street setting. "
            "Green dashed = 10:1 threshold. Y-axis floored at 0."
        )
        fig_bcr = plot_bcr_curve(df, personas, bazaar_f)
        st.pyplot(fig_bcr, use_container_width=True)
        plt.close(fig_bcr)

    st.markdown("---")

    # -----------------------------------------------------------------------
    # PER-PERSONA TABLE
    # -----------------------------------------------------------------------
    st.markdown("#### Per-Persona Breakdown")
    rows = []
    for key, p in personas.items():
        rb = econ["res_baseline"][key]
        rs = econ["res_scenario"][key]
        lb = econ["persona_losses"][key]["baseline"]
        ls = econ["persona_losses"][key]["scenario"]
        dl = lb - ls
        rows.append({
            "Persona":                      p["label"],
            "Weight":                       f"{p['weight']*100:.0f}%",
            "v0 (m/s)":                     p["v0"],
            "k":                            p["k"],
            "f_max":                        p["f_max"],
            "Baseline detours":             rb["n_detours"],
            "Scenario detours":             rs["n_detours"],
            "Baseline Dt (s)":              f"{rb['delta_tau']:.0f}",
            "Scenario Dt (s)":              f"{rs['delta_tau']:.0f}",
            "Baseline loss (Rs Cr)":        f"{lb:.2f}",
            "Scenario loss (Rs Cr)":        f"{ls:.2f}",
            "Delta loss (Rs Cr)":           f"{'−' if dl < 0 else '+'}Rs{abs(dl):.2f}",
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    st.markdown("---")

    # -----------------------------------------------------------------------
    # MATH EXPANDER
    # -----------------------------------------------------------------------
    with st.expander("Full mathematical derivation"):

        st.markdown("##### Notation")
        st.markdown("""
| Symbol | Meaning |
|--------|---------|
| $D = 900$ m | Total corridor length |
| $d = 12.5$ m | Segment length |
| $N_{300} = 24$ | Discrete obstacle nodes, 300m stretch |
| $N_{600} = 48$ | Uniform segments, 600m Bazaar Street |
| $f_i \\in \\{1,2,3,4,5\\}$ | Friction at segment $i$ |
| $v_0(\\phi)$ | Free-walking speed (m/s) |
| $k(\\phi)$ | Friction sensitivity exponent |
| $f_{\\text{max}}(\\phi)$ | Impassability threshold |
| $\\delta(\\phi)$ | Mean ROW detour length (m) |
| $\\alpha = 1.5$ | ROW velocity penalty multiplier |
| $w_\\phi$ | Population share weight |
| $M = 100{,}000$ | Daily commuters |
| $W = 250$ | Working days/year |
        """)

        st.markdown("##### Effective Path Length")
        st.latex(r"L_{\text{eff}}=d\sum_{i=1}^N f_i \qquad \bar{f}=\frac{L_{\text{eff}}}{D}")
        st.latex(r"L_{\text{eff}}^{300}=1187.5\text{ m} \quad L_{\text{eff}}^{600}=3000\text{ m} \quad \bar{f}=4.653")

        st.markdown("##### Power-Law Velocity & Traversal Time")
        st.latex(r"v_{\text{eff}}(i,\phi)=\frac{v_0}{f_i^k} \qquad \tau_i=\frac{d\cdot f_i^k}{v_0} \quad(f_i\leq f_{\max})")
        st.latex(r"\tau_i^{\text{ROW}}=\frac{(d+\delta)\cdot\alpha}{v_0} \quad(f_i>f_{\max})")

        st.info(
            "**The f=4 paradox:** For elderly ($k=0.9$, $f_\\text{max}=4$):\n\n"
            "- Bazaar St at $f=5$ (impassable): "
            r"$\tau^\text{ROW}=(12.5+10)\times1.5/0.9=37.5$ s" "\n\n"
            "- Bazaar St at $f=4$ (passable): "
            r"$\tau=12.5\times4^{0.9}/0.9=57.4$ s" "\n\n"
            "Lowering from f=5 to f=4 makes elderly **20s slower per segment**. "
            "Across 48 Bazaar Street segments this adds ~960s to elderly traversal time. "
            "The ROW detour at f=5 was paradoxically cheaper. This is a real-world "
            "effect of the power-law model with high $k$."
        )

        st.markdown("##### Time Tax & Economic Aggregation")
        st.latex(r"\Delta\tau(\phi)=\frac{d}{v_0}\left(\sum_i f_i^k-N\right)")
        st.latex(r"\bar{\Delta\tau}=\frac{\sum_\phi w_\phi\Delta\tau(\phi)}{\sum_\phi w_\phi} ="
                 rf" {econ['dtau_bar_b']:.1f}\text{{ s (baseline)}}")
        st.latex(r"\mathcal{T}_\text{year}=M\cdot W\cdot\bar{\Delta\tau}/60"
                 rf" = {econ['annual_pm_b']/1e6:.2f}\text{{M person-minutes}}")
        st.latex(r"\text{Loss}=\mathcal{T}_\text{year}\times\frac{50}{60}"
                 rf" \approx \text{{Rs}}{econ['annual_loss_cr_b']:.2f}\text{{ Cr/yr}}")

        st.markdown("##### Benefit-Cost Ratio")
        st.latex(r"\text{BCR}=\frac{(\mathcal{L}_\text{baseline}-\mathcal{L}_\text{scenario})\times100}{\text{repair cost (lakh Rs)}}")
        st.markdown(
            f"Cost scales at Rs{FIX_COST_LOW_LAKH}/3–{FIX_COST_HIGH_LAKH}/3 lakh per fix. "
            "**BCR = 0 when n\\_fixes = 0**, regardless of bazaar\\_f setting."
        )
        if n_fixes > 0:
            st.markdown(
                f"**For $n={n_fixes}$:** saving = Rs{econ['saving_lakh']:.1f} lakh/yr · "
                f"BCR = {econ['bcr_low']:.1f}:1 – {econ['bcr_high']:.1f}:1"
            )
