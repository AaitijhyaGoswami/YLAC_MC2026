# Escape the Knot
### A Physics-Based Pedestrian Accessibility Audit of the Yeshwantpur–Mathikere Corridor, Bengaluru

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-ff4b4b?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square)

> **Authors:** [Aaitijhya Goswami](https://www.linkedin.com/in/aaitijhya-goswami-553940280/) (IISc Bengaluru) · [Prajwal Kagalgomb](https://www.linkedin.com/in/prajwalkagalgomb/) (IIM Bengaluru)  
> **Partner:** [Bengawalk](https://bengawalk.com/) · **Programme:** YLAC Mobility Champions 2026  
> **Field Audit:** March 2026 · **Survey Area:** 900 m, Yeshwantpur Railway Station → Constitution Circle

---

## Overview

This project is a **multi-module Streamlit application** that quantifies the infrastructural burden imposed on pedestrians at the Yeshwantpur transit hub. The core idea is to treat a broken pedestrian corridor as a physical system: encroachments, missing drain covers, and footpath failures act as a resistive friction field, and a commuter's journey through it is analogous to work done against that field — exactly as mechanical work scales with surface resistance:

$$W = \int_0^D F(x)\, dx = \int_0^D \mu(x)\, mg\, dx$$

The audit covered a **900 m corridor** split into two structurally distinct zones:
- **300 m (Constitution Circle zone):** 24 discrete geotagged obstacle nodes
- **600 m (Bazaar Street zone):** A continuous systemic failure — footpath fully colonised by vendors and wall-and-mesh barriers

**Key headline results:**

| Metric | Value |
|---|---|
| Route failing Active Mobility Bill standards | 90.3% |
| Route inaccessible to wheelchair users | 96.0% |
| Mean Friction Index $\bar{f}$ | 4.653 |
| Effective felt distance of a 900 m walk | ~4,187 m |
| Annual person-minutes lost (100,000 daily commuters) | ~170 million |
| Annual productivity loss | ₹14.2 Crore |
| BCR of Lighthouse Pilot (top-3 node fix) | >10:1 |

---

## Application Structure

The app (`app.py`) uses a sidebar radio to route between five modules. Each module is a self-contained Python file with an `app()` entry point, imported dynamically at startup with graceful fallback if a module fails to load.

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
- Renders the **600 m Bazaar Street polyline** as a colour-coded route layer, colour varying with the sidebar-controlled `bazaar_f` scenario value
- Renders **24 discrete `CircleMarker`s** for the Constitution Circle zone, each with a rich popup (Node ID, friction, GPS coords, status); nodes remediated by the slider are re-coloured to confirm the fix
- Produces three `Matplotlib` figures: a **friction gradient bar chart** (full 900 m), a **severity pie chart** (300 m zone only), and an **effective path length comparison** chart across Baseline / Modified / S.U.R.E. Target scenarios
- Computes the **S.U.R.E. Compliance Gauge** — a horizontal bar showing where $\bar{f}$ sits between the target of 1.0 and the failure ceiling of 5.0

**Mathematical framework:**

The corridor is treated as a piecewise-constant friction field. The **Effective Path Length** $L_\text{eff}$ — the felt distance in terms of physical effort — is the friction-weighted integral over the full route:

$$L_\text{eff}(\phi) = \int_0^D f(x,\, \phi)\, dx \;\approx\; d \sum_{i=1}^{N} f_i(\phi)$$

where $D = 900\,\text{m}$, $d = 12.5\,\text{m}$ (segment discretisation length), $N = 72$ (total segments), and $\phi$ denotes the commuter persona.

The two zones are computed separately and summed. For the **300 m Constitution Circle zone** (24 nodes: 9 at $f=5$, 8 at $f=4$, 4 at $f=3$, 3 at $f=2$):

$$L_\text{eff}^{300} = 12.5 \times \left(9 \cdot 5 + 8 \cdot 4 + 4 \cdot 3 + 3 \cdot 2\right) = 12.5 \times 95 = 1187.5\,\text{m}$$

For the **600 m Bazaar Street zone** (continuous friction at the sidebar-selected value $f_B$):

$$L_\text{eff}^{600} = 600 \times f_B$$

At baseline ($f_B = 5$), this gives $L_\text{eff}^{600} = 3000\,\text{m}$. The total effective path length and **Mean Friction Index** across the corridor are:

$$L_\text{eff} = L_\text{eff}^{300} + L_\text{eff}^{600} = 1187.5 + 3000 = 4187.5\,\text{m}$$

$$\bar{f} = \frac{1}{D}\left[d\sum_{i=1}^{N} f_i + L_B \cdot f_B\right] = \frac{4187.5}{900} \approx 4.653$$

The corridor imposes **4.65× the energetic cost** of a fully compliant S.U.R.E. footpath. When the slider remediates the top $n$ nodes to $f = 1$, $\bar{f}$ recalculates in real time and all three figures update.

**Sidebar controls:**
- Slider: nodes remediated to $f = 1$ (0–24, ranked by descending `f_value`)
- Selectbox: Bazaar Street scenario ($f = 5$ through $f = 1$)

---

### 2. Time Tax Simulator · `simulation/agent_sim.py`

Simulates how each of four commuter personas traverses the friction array and quantifies the time stolen per trip.

**What it does:**
- Builds a NumPy array of 72 friction values (24 discrete nodes + 48 Bazaar Street segments at $d = 12.5\,\text{m}$)
- Runs `run_simulation()` for each persona against the current friction array
- For each segment $i$: applies the power-law velocity model if $f_i \leq f_\text{max}(\phi)$, or triggers a vehicular Right-of-Way (ROW) detour if $f_i > f_\text{max}(\phi)$
- Produces three `Matplotlib` figures: traversal time comparison (ideal vs. actual), cross-persona Time Tax bar chart, and a two-panel per-segment breakdown (friction gradient + per-segment $\tau_i$)
- Exposes a raw simulation data table in an expander

**Velocity model:**

Rather than a linear speed reduction — which underestimates the compounding penalty on vulnerable users — the simulator uses a **power-law friction-velocity relationship**. The sensitivity exponent $k(\phi)$ captures how super-linearly speed degrades for each persona:

$$v_\text{eff}(i,\, \phi) = \frac{v_0(\phi)}{f_i^{\,k(\phi)}}$$

The traversal time for segment $i$ of length $d$ under normal path conditions is:

$$\tau_i(\phi) = \frac{d}{v_\text{eff}(i,\,\phi)} = \frac{d \cdot f_i^{\,k(\phi)}}{v_0(\phi)} \qquad \text{if } f_i \leq f_\text{max}(\phi)$$

When $f_i > f_\text{max}(\phi)$, the segment is **impassable** for that persona. The agent is rerouted into vehicular ROW, incurring a geometric detour of length $\delta(\phi)$ and a safety speed-penalty multiplier $\alpha = 1.5$:

$$\tau_i^\text{ROW}(\phi) = \frac{\bigl(d + \delta(\phi)\bigr) \cdot \alpha}{v_0(\phi)} \qquad \text{if } f_i > f_\text{max}(\phi)$$

These two cases are unified in the piecewise traversal model:

$$\tau_i(\phi) = \begin{cases} \dfrac{d \cdot f_i^{\,k(\phi)}}{v_0(\phi)} & f_i \leq f_\text{max}(\phi) \\[10pt] \dfrac{\bigl(d + \delta(\phi)\bigr) \cdot \alpha}{v_0(\phi)} & f_i > f_\text{max}(\phi) \end{cases}$$

The **total actual traversal time** and **ideal traversal time** across all $N = 72$ segments are:

$$T_\text{actual}(\phi) = \sum_{i=1}^{N} \tau_i(\phi) \qquad\qquad T_\text{ideal}(\phi) = \frac{D}{v_0(\phi)}$$

The **Time Tax** — cumulative seconds stolen from the commuter per trip — is therefore:

$$\Delta\tau(\phi) = T_\text{actual}(\phi) - T_\text{ideal}(\phi) = \frac{d}{v_0(\phi)}\left(\sum_{i=1}^{N} f_i^{\,k(\phi)} - N\right)$$

**What-if scenario:** when the top $n$ nodes (sorted by descending $f_i^{k(\phi)}$ to maximise impact first) are set to $f = 1$, the time recovered per persona is:

$$\Delta\tau_\text{saved}(n,\,\phi) = \frac{d}{v_0(\phi)} \sum_{j=1}^{n} \left(f_j^{\,k(\phi)} - 1\right)$$

This directly drives the sidebar node-fix slider — each increment shows the marginal gain of one more hotspot repair.

**Persona configuration** (loaded from `data/personas.yaml`):

| Persona | $v_0$ (m/s) | $k$ | $f_\text{max}$ | $\delta$ (m) | Weight |
|---|---|---|---|---|---|
| Able-bodied Adult | 1.4 | 0.60 | 4 | 8 | 45% |
| Elderly Commuter | 0.9 | 0.90 | 3 | 10 | 20% |
| Wheelchair User | 0.8 | 1.20 | 3 | 15 | 10% |
| Delivery Partner | 1.2 | 0.75 | 4 | 8 | 25% |

**Sidebar controls:** Persona selector (with $v_0$, $k$, $f_\text{max}$, $\alpha$, $\delta$ shown in help text), node-fix slider, Bazaar Street scenario selectbox.

---

### 3. Economic Impact · `simulation/economic_impact.py`

Scales individual Time Tax values to a city-wide annual fiscal loss figure and computes the return on infrastructure investment.

**What it does:**
- Runs the full simulation for all four personas under both the **baseline** (`n_fixes = 0`, `bazaar_f = 5`) and the current sidebar scenario
- Computes a population-weighted mean Time Tax, converts to annual person-minutes, then to INR
- Wage rate validated against Karnataka Labour Commissioner minimum wage schedules 2025–26 and 2026–27
- Computes the BCR for the selected number of fixes using ₹8–12 Lakh per node as the repair cost estimate
- Produces: Time Tax comparison bar chart (baseline vs. scenario, per persona), annual loss waterfall chart ($\Delta$ per persona), and a **BCR curve** (investment efficiency vs. number of hotspots fixed, with a 10:1 threshold line)

**Aggregation pipeline:**

The **population-weighted mean Time Tax** across all persona types $\Phi$, weighted by their share $w_\phi$ of the daily commuter population:

$$\overline{\Delta\tau} = \frac{\displaystyle\sum_{\phi \in \Phi} w_\phi \cdot \Delta\tau(\phi)}{\displaystyle\sum_{\phi \in \Phi} w_\phi}$$

The **total annual person-minutes lost** across $M$ daily commuters and $W$ working days:

$$\mathcal{T}_\text{year} = M \cdot W \cdot \frac{\overline{\Delta\tau}}{60}$$

Converted to annual economic loss in Crore INR, where $\text{WAGE} \approx \text{₹}0.83\,\text{min}^{-1}$:

$$\mathcal{L} = \mathcal{T}_\text{year} \cdot \text{WAGE} \times 10^{-7}$$

The **annual economic benefit** of a given remediation scenario relative to baseline:

$$\Delta\mathcal{L} = \mathcal{L}_\text{baseline} - \mathcal{L}_\text{scenario}$$

The **Benefit-Cost Ratio** for $n$ fixes at a repair cost range of ₹8–12 Lakh per node:

$$\text{BCR} = \frac{\Delta\mathcal{L} \times 100}{\text{Repair Cost (Lakhs)}}$$

At the Lighthouse Pilot ($n = 3$), $\Delta\mathcal{L} \approx \text{₹}5.4\,\text{Crore}$ against a repair cost of ₹24–36 Lakh, giving $\text{BCR} > 10:1$.

**Model constants:**

```python
M              = 100_000   # daily commuters at Yeshwantpur hub
W              = 250       # working days per year
WAGE           = 50 / 60   # Rs/min  (RBI informal rate)
FIX_COST_LOW   = 8         # Lakh per node (lower estimate)
FIX_COST_HIGH  = 12        # Lakh per node (upper estimate)
```

**Sidebar controls:** Hotspot-fix slider (default: 3), Bazaar Street scenario selectbox.

---

### 4. Lighthouse Prototype · `cad_viewer/viewer.py`

Presents the proposed S.U.R.E.-compliant redesign of the Bazaar Street cross-section.

**What it does:**
- Displays field photographs of the current corridor (Bazaar Street encroachment, wall-and-mesh barriers, blocked footpaths)
- Shows static CAD renders of the current ($f = 5$) and proposed ($f = 1$) cross-sections as before/after image pairs
- Lists stakeholder groups affected and the relevant administrative authorities (DULT, GBA/BBMP, BMTC, Traffic Police, MLA)
- Renders the spatial allocation comparison table

The physics motivation: the barricades and colonisation impose a psychological buffer zone that reduces usable pedestrian width below even the nominal footpath width. The effective passable width is:

$$W_\text{eff} = W_\text{total} - W_\text{obstacles} - W_\text{buffer}$$

Restoring the full $3\,\text{m}$ clear path eliminates the right-hand terms entirely, returning $v_\text{eff} \to v_0(\phi)$ for every persona — zero Time Tax, $\bar{f} \to 1$.

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

Interviews 01–06 are bilingual: each question and answer appears in Kannada first, followed by the English translation. Interviews 07–10 are English-only. All transcripts follow a press-accurate Q&A format with a metadata header (role, location, interview method, date) and a closing observation note. Strict anonymity protocols were observed — no names, designations, or identifying markers were recorded.

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

Distributed under the MIT License. See `LICENSE` for more information.

---

<p align="center">Built for Bengaluru's pedestrians, and for the streets that should belong to them.<br>
<a href="https://bengawalk.com">Bengawalk</a> · YLAC Mobility Champions 2026</p>
