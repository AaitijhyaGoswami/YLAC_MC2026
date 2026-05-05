# Escape the Knot
### A Physics-Based Pedestrian Accessibility Audit of the Yeshwantpur–Mathikere Corridor, Bengaluru

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-ff4b4b?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square)

> **Authors:** [Aaitijhya Goswami](https://www.linkedin.com/in/aaitijhya-goswami-553940280/) (IISc Bengaluru) · [Prajwal Kagalgomb](https://www.linkedin.com/in/prajwalkagalgomb/) (IIM Bengaluru)  
> **Partner:** [Bengawalk](https://bengawalk.com/) · **Programme:** YLAC Mobility Champions 2026  
> **Field Audit:** March 7–8, 2026 · **Survey Area:** 900 m, Yeshwantpur Railway Station → Constitution Circle

---

## Overview

This project is a **multi-module Streamlit application** that quantifies the infrastructural burden imposed on pedestrians at the Yeshwantpur transit hub. The core idea is to treat a broken pedestrian corridor as a physical system: encroachments, missing drain covers, and footpath failures act as a resistive friction field, and a commuter's journey through it is analogous to work done against that field.

The audit covered a **900 m corridor** split into two structurally distinct zones:
- **300 m (Constitution Circle zone):** 24 discrete geotagged obstacle nodes
- **600 m (Bazaar Street zone):** A continuous systemic failure — footpath fully colonised by vendors and wall-and-mesh barriers

**Key headline results:**

| Metric | Value |
|---|---|
| Route failing Active Mobility Bill standards | 90.3% |
| Route inaccessible to wheelchair users | 96.0% |
| Mean Friction Index `f̄` | 4.653 |
| Effective felt distance of a 900 m walk | ~4,187 m |
| Annual person-minutes lost (100,000 daily commuters) | ~170 million |
| Annual productivity loss | ₹14.2 Crore |
| BCR of Lighthouse Pilot (top-3 node fix) | >10:1 |

---

## Application Structure

The app (`app.py`) uses a sidebar radio to route between four modules. Each module is a self-contained Python file with an `app()` entry point, imported dynamically at startup with graceful fallback if a module fails to load.

```
escape-the-knot/
├── app.py                          # Main Streamlit entry point & sidebar navigation
├── simulation/
│   ├── friction_mapper.py          # Geotagged friction map + corridor analysis
│   ├── agent_sim.py                # Agent-based Time Tax simulator
│   ├── economic_impact.py          # Fiscal aggregation engine
│   └── interviews.py               # Stakeholder interview archive & PDF viewer
├── cad_viewer/
│   └── viewer.py                   # Lighthouse CAD prototype viewer
├── data/
│   ├── audit_log.csv               # Geotagged obstacle data (id, lat, lon, f_value)
│   ├── personas.yaml               # Agent config: v0, k, f_max, alpha, delta, weight
│   └── survey[1–9].jpg             # Field audit photographs
├── interviews/
│   ├── street_vendor.pdf           # Interview 01 — bilingual (Kannada / English)
│   ├── rest_owner.pdf              # Interview 02 — bilingual (Kannada / English)
│   ├── hotel_owner.pdf             # Interview 03 — bilingual (Kannada / English)
│   ├── tc_ysp.pdf                  # Interview 04 — bilingual (Kannada / English)
│   ├── shop_ypr.pdf                # Interview 05 — bilingual (Kannada / English)
│   ├── elderly.pdf                 # Interview 06 — bilingual (Kannada / English)
│   ├── student.pdf                 # Interview 07 — English
│   ├── scholar.pdf                 # Interview 08 — English
│   ├── delivery.pdf                # Interview 09 — English
│   └── auto.pdf                    # Interview 10 — English
└── requirements.txt
```

---

## Modules

### 1. Friction Mapper · `simulation/friction_mapper.py`

Converts the field audit into an interactive geospatial evidence layer.

**What it does:**
- Loads `data/audit_log.csv` (columns: `id`, `lat`, `lon`, `f_value`) and builds a `Folium` map centred on the corridor
- Renders the **600 m Bazaar Street polyline** as a colour-coded route layer (colour varies with the sidebar-controlled `bazaar_f` scenario value)
- Renders **24 discrete CircleMarkers** for the Constitution Circle zone, each with a rich popup (Node ID, friction, GPS coords, status)
- Nodes set to `f = 1` by the sidebar slider are re-coloured to gold to visually confirm remediation
- Produces three `Matplotlib` figures: a **friction gradient bar chart** (full 900 m), a **severity pie chart** (300 m zone only), and an **effective path length comparison** bar chart across three scenarios (Baseline / Modified / S.U.R.E. Target)
- Computes the **S.U.R.E. Compliance Gauge** — a horizontal bar showing where the current `f̄` sits between 1.0 (target) and 5.0 (failure)

**Core computation:**

The mean friction index across the full 900 m corridor is:

```
f̄ = (d × Σfᵢ + L_B × f_B) / D
```

where `d = 12.5 m` (segment length), `D = 900 m`, `L_B = 600 m` (Bazaar Street length), and `f_B` is the sidebar-selected Bazaar Street scenario value.

**Sidebar controls:**
- Slider: nodes remediated to `f = 1` (0–24, ranked by descending `f_value`)
- Selectbox: Bazaar Street scenario (`f = 5` through `f = 1`)

---

### 2. Time Tax Simulator · `simulation/agent_sim.py`

Simulates how each of four commuter personas traverses the friction array, and quantifies the time stolen per trip.

**What it does:**
- Builds a NumPy array of 72 friction values (24 discrete nodes + 48 Bazaar Street segments at `d = 12.5 m`)
- Runs `run_simulation()` for each persona against the current friction array
- For each segment `i`: if `f_i ≤ f_max(φ)`, applies the power-law velocity model; if `f_i > f_max(φ)`, triggers a **vehicular Right-of-Way detour** with a distance penalty `δ` and safety multiplier `α = 1.5`
- Produces three `Matplotlib` figures: traversal time comparison (ideal vs. actual), cross-persona Time Tax bar chart, and a two-panel per-segment breakdown (friction gradient + per-segment `τᵢ`)
- Exposes a raw simulation data table in an expander

**Velocity model:**

```
v_eff(i, φ) = v₀(φ) / fᵢ^k(φ)          [path traversal, fᵢ ≤ f_max]
τᵢ(φ)       = (d + δ) × α / v₀(φ)      [ROW detour,    fᵢ > f_max]

Δτ(φ) = T_actual - T_ideal
       = (d / v₀) × (Σ fᵢ^k - N)       [traversal-only approximation]
```

**Persona configuration** (loaded from `data/personas.yaml`):

| Persona | `v₀` (m/s) | `k` | `f_max` | `δ` (m) | Population weight |
|---|---|---|---|---|---|
| Able-bodied Adult | 1.4 | 0.60 | 4 | 8 | 45% |
| Elderly Commuter | 0.9 | 0.90 | 3 | 10 | 20% |
| Wheelchair User | 0.8 | 1.20 | 3 | 15 | 10% |
| Delivery Partner | 1.2 | 0.75 | 4 | 8 | 25% |

**Sidebar controls:** Persona selector (with calibration metrics in help text), node-fix slider, Bazaar Street scenario selectbox.

---

### 3. Economic Impact · `simulation/economic_impact.py`

Scales individual Time Tax values to a city-wide annual fiscal loss figure.

**What it does:**
- Runs the full simulation for all four personas under both the **baseline** (`n_fixes = 0`, `bazaar_f = 5`) and the **current sidebar scenario**
- Computes a **population-weighted mean Time Tax** `Δτ̄` across personas
- Converts to annual person-minutes and then to INR using `WAGE = ₹50/hr` (RBI informal rate, Karnataka Labour Commissioner data 2025–27)
- Computes the **Benefit-Cost Ratio (BCR)** for the selected number of fixes, using `₹8–12 Lakh` per node as the repair cost estimate
- Produces: Time Tax comparison bar chart (baseline vs. scenario, per persona), annual loss waterfall chart (Δ per persona), and a **BCR curve** (efficiency vs. number of hotspots fixed)
- Displays a per-persona breakdown table

**Aggregation formula:**

```
L = M × W × (Δτ̄ / 60) × WAGE × 10⁻⁷   [Crore INR]

BCR = (ΔL × 100) / Repair Cost (Lakhs)
```

where `M = 100,000` (daily commuters), `W = 250` (working days/year).

**Constants:**

```python
M               = 100_000
W               = 250
WAGE            = 50 / 60          # Rs/min
FIX_COST_LOW    = 8  # Lakh/node
FIX_COST_HIGH   = 12 # Lakh/node
```

**Sidebar controls:** Hotspot-fix slider (default: 3), Bazaar Street scenario selectbox.

---

### 4. Lighthouse Prototype · `cad_viewer/viewer.py`

Presents the proposed S.U.R.E.-compliant redesign of the Bazaar Street cross-section.

**What it does:**
- Displays field photographs of the current corridor condition (Bazaar Street encroachment, barriers, blocked footpaths)
- Shows static CAD renders of the current (`f = 5`) and proposed (`f = 1`) cross-sections as before/after image pairs
- Lists the stakeholder groups affected (residents, transit commuters, students, vendors, persons with disabilities, freight operators) and the relevant administrative authorities (DULT, GBA/BBMP, BMTC, Traffic Police, MLA)
- Renders a spatial allocation comparison table (current spec vs. proposed S.U.R.E. spec for each cross-sectional component)

**Proposed cross-section (Bazaar Street, S.U.R.E. compliant):**

| Component | Current | Proposed |
|---|---|---|
| Pedestrian clear path | 0.0 m (colonised) | 3.0 m continuous (RCC Paver) |
| Utility / vending zone | 3.0 m (unorganised) | 2.5 m structured (Granite) |
| Vertical boundary | 1 m wall + mesh | 150 mm mountable kerb |
| Drainage | Open / broken | Flush covers, integrated |
| Vehicle carriageway | ~4 m (unmarked) | 10 m, 2-lane, marked |
| Total cross-section | 16.0 m | 21.0 m |

---

### 5. Interview Archive · `simulation/interviews.py`

Renders the full set of stakeholder interview transcripts collected during the March 2026 field audit.

**What it does:**
- Defines a `render_interview(filename, title)` helper that wraps `streamlit-pdf-viewer` to embed each PDF inline within a collapsible `st.expander`
- Provides a `st.download_button` for each transcript so users can save a copy locally
- Handles missing files gracefully with a labelled `st.error` rather than a hard crash
- Calls `render_interview` sequentially for all ten transcripts, loaded from `interviews/`

**Interview subjects:**

| # | File | Subject | Language |
|---|---|---|---|
| 01 | `street_vendor.pdf` | Street vendor, 600 m Bazaar Street stretch | Kannada / English |
| 02 | `rest_owner.pdf` | Restaurant owner, Constitution Circle | Kannada / English |
| 03 | `hotel_owner.pdf` | Hotel owner, Bazaar Circle | Kannada / English |
| 04 | `tc_ysp.pdf` | Ticket collector, Yeshwantpur Railway Station | Kannada / English |
| 05 | `shop_ypr.pdf` | Kiosk operator, station main concourse | Kannada / English |
| 06 | `elderly.pdf` | Elderly pedestrian, 30-year Mathikere resident | Kannada / English |
| 07 | `student.pdf` | Grade 10 student, Kendriya Vidyalaya IISc | English |
| 08 | `scholar.pdf` | PhD research scholar, IISc Bengaluru | English |
| 09 | `delivery.pdf` | Swiggy delivery executive, Mathikere–IISc route | English |
| 10 | `auto.pdf` | Auto-rickshaw driver, Yeshwantpur stand (9 years) | English |

Interviews 01–06 are bilingual: each question and answer appears in Kannada first, followed by the English translation, typeset with Lohit Kannada and DejaVu Sans respectively. Interviews 07–10 are English-only. All transcripts follow the same press-accurate Q&A format with a metadata header (role, location, interview method, date) and a closing observation note. Strict anonymity protocols were observed throughout — no names, designations, or identifying markers were recorded.

---

## Installation & Usage

```bash
git clone https://github.com/AaitijhyaGoswami/escape-the-knot.git
cd escape-the-knot
pip install -r requirements.txt
streamlit run app.py
```

The app handles missing modules gracefully — if any simulation file fails to import, it is silently excluded from the sidebar and an "under development" message is shown for that route.

---

## Data Files

### `data/audit_log.csv`
Required columns: `id`, `lat`, `lon`, `f_value`  
24 rows corresponding to geotagged obstacle nodes in the 300 m Constitution Circle zone.

### `data/personas.yaml`
YAML mapping of persona keys to simulation parameters:

```yaml
able_bodied:
  label: "Able-bodied Adult"
  v0: 1.4          # free-walking speed (m/s)
  k: 0.6           # friction sensitivity exponent
  f_max: 4         # impassability threshold
  alpha: 1.5       # ROW velocity penalty multiplier
  delta: 8.0       # mean detour length (m)
  weight: 0.45     # population share
  color: "#2196F3"
```

---

## Tech Stack

| Layer | Libraries |
|---|---|
| Web application | `streamlit` |
| Geospatial mapping | `folium`, `streamlit-folium` |
| Numerical simulation | `numpy` |
| Data handling | `pandas`, `pyyaml` |
| Visualisation | `matplotlib` |
| PDF rendering | `streamlit-pdf-viewer` |

---

## Policy Context

This audit is developed in support of the following regulatory frameworks:

- [Active Mobility Bill (2022)](https://dult.karnataka.gov.in/121/active-mobility-bill/en) — DULT, Govt. of Karnataka
- [Tender S.U.R.E. (Sustainable Urban Road Engineering)](https://www.janausp.org/portfolio/tender-sure)
- [IRC:103-2022](https://www.anjleeagarwal.co.in/books/IRC-103-2022.pdf) — Indian Roads Congress pedestrian facility guidelines
- [Harmonised Guidelines & Space Standards (NIUA, 2021)](https://niua.in/intranet/sites/default/files/2262.pdf)
- [DULT Urban Street Design Guidelines](https://dult.karnataka.gov.in/89/policies-and-guidelines/en)

---

## Contributing

Contributions are welcome, particularly extensions of the friction rubric to new survey corridors, additional commuter personas, or improved CAD visualisations.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-survey-zone`
3. Commit your changes: `git commit -m 'Add extended Mathikere audit data'`
4. Push and open a Pull Request

---

## License

MIT — see `LICENSE` for details.

---

<p align="center">Built for Bengaluru's pedestrians, and for the streets that should belong to them.<br>
<a href="https://bengawalk.com">Bengawalk</a> · YLAC Mobility Champions 2026</p>
