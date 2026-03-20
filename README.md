# 🚶 Escape the Knot: Yeshwantpur–Mathikere Mobility Nexus
### A Physics-Based Pedestrian Accessibility Audit & Simulation Suite

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-ff4b4b)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-success)

> **Authors:** [Aaitijhya Goswami](https://www.linkedin.com/in/aaitijhya-goswami-553940280/) & [Prajwal Kagalgomb](https://www.linkedin.com/in/prajwalkagalgomb/) <br>
> **Partner Organisation:** [Bengawalk](https://bengawalk.com/) <br>
> **Programme:** YLAC Mobility Champions 2026

---

## 📖 Overview

This interactive dashboard is a **Pedestrian Mobility Audit and Agent-Based Simulation Suite** developed to quantify the infrastructural tax imposed on pedestrians at the Yeshwantpur Mobility Knot in Bengaluru. It combines physics-driven modelling with ground-level advocacy to make a data-backed case for the transformation of Yeshwantpur into a **"Lighthouse Pilot"** for seamless, standards-compliant intermodal pedestrian infrastructure.

By treating the city as a physical system, where broken drains, encroachments, and missing footpaths act as potential energy barriers Φ(x), the commuter's journey becomes analogous to mechanical work done against a spatially varying friction field. Just as the work required to move an object across a rough surface is:

$$W = \int_0^D F(x)  dx = \int_0^D \mu(x)  mg  dx$$

we define the **Effective Path Length** as the friction-weighted integral over the surveyed corridor of total length `D`:

$$L_{eff}(\phi) = \int_0^D f(x, \phi)  dx$$

where `f(x, φ) ∈ [1, 5]` is a continuous friction field derived from discrete audit observations, and `φ` is the commuter persona. In the discretised implementation over `N` path segments of equal physical length `d = D/N`:

$$L_{eff}(\phi) \approx d \sum_{i=1}^{N} f_i(\phi)$$

The ratio `L_eff / D` is the **mean friction index** of the route. For the Yeshwantpur survey, this evaluates to approximately **4.625**, meaning the corridor imposes the equivalent of traversing a path 4.625× its physical length on a frictionless surface. The result is a **Time Tax** `Δτ(φ)` (the measurable seconds stolen from each commuter per trip) which, summed across 100,000+ daily users and 250 working days, becomes the headline economic argument for infrastructure intervention.

---

## 🗺️ Campaign Context

**Survey Area (March 7–8, 2026):** The 900m stretch connecting Yeshwantpur Railway Station to Constitution Circle, the SWR–Metro interchange corridor, and the 0.45 km² Mathikere road network.

**Policy Target:** Mandate **[Tender S.U.R.E. Design Standards](https://www.janausp.org/portfolio/tender-sure)** via **[DULT's Active Mobility Bill](https://dult.karnataka.gov.in/121/active-mobility-bill/en)**, specifically replacing open box drains with integrated "Pipe and Chamber" systems to create a continuous, accessible walking surface.

```
Friction Distribution — 900m Yeshwantpur Stretch (Survey Results)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
f = 5  (Systemic Failure)   ████████████████████  79.18%
f = 4  (Physical Barrier)   ███                   11.11%
f = 3  (Obstacle Course)    █                      4.16%
f = 2  (Distracted Walk)    █                      5.55%
f = 1  (Gold Standard)                             Reference
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  90.3% of the stretch fails Active Mobility Bill standards
  96.0% is fully inaccessible for individuals in wheelchairs
```

---

## 🚀 The Modules

---

### **1. Spatial Friction Mapper — `friction_mapper.py`**

- **Abstract:** This module models the survey-audited route as a discretised path, assigning a friction value `f ∈ {1, 2, 3, 4, 5}` to each geotagged obstacle node based on the Active Mobility Bill rubric. The rubric maps observable infrastructure states to ordinal friction levels, which are then treated as piecewise-constant values over the path segment surrounding each obstacle. For a route partitioned into `N` segments, the **mean friction index** is:

$$\bar{f} = \frac{1}{N} \sum_{i=1}^{N} f_i = \frac{L_{eff}}{D}$$

  The 900m route is treated as two structurally distinct zones. The **600m Bazaar Street stretch** is a continuous `f = 5` failure (footpath ends entirely, pedestrians enter vehicular ROW) contributing directly to `L_eff`:

$$L_{eff}^{600} = 600 \times 5 = 3000 \text{ m}$$

  The **300m Constitution Circle stretch** has 24 geotagged discrete obstacles: 9 at `f = 5`, 8 at `f = 4`, 4 at `f = 3`, and 3 at `f = 2`. With segment length `d = 300/24 = 12.5 m`:

$$L_{eff}^{300} = 12.5 \times \sum_{i=1}^{24} f_i = 12.5 \times (9{\times}5 + 8{\times}4 + 4{\times}3 + 3{\times}2) = 12.5 \times 95 = 1187.5 \text{ m}$$

  The **total effective path length** and **mean friction index** across the full 900m corridor are therefore:

$$L_{eff} = 3000 + 1187.5 = 4187.5 \text{ m} \qquad \bar{f} = \frac{L_{eff}}{D} = \frac{4187.5}{900} \approx 4.653$$

  indicating the route imposes nearly **4.65× the energetic cost** of a fully compliant footpath. Nodes are snapped to the nearest `OSMnx` footpath edge using minimum Haversine distance, and `f`-values are propagated as edge weights in the `NetworkX` graph for downstream routing.

  The friction rubric encodes the following observable-to-value mapping:

  | `f` | Infrastructure State | Speed Impact | Wheelchair Access |
  |-----|---------------------|--------------|-------------------|
  | 1 | Continuous, unobstructed 3m+ footpath | `v = v₀` | Full |
  | 2 | Minor cracks, unlevelled slabs, low cables | `v ≈ 0.85 v₀` | Partial — discomfort |
  | 3 | Broken slabs, rubble, utility excavation | `v ≈ 0.5 v₀` | Severely restricted |
  | 4 | Missing drain cover, high kerb, partial blockage | `v ≈ 0.25 v₀` | Effectively impassable |
  | 5 | Footpath ends — transformer, encroachment, construction | `v → 0` (ROW entry) | Fully impassable |

- **Applications:**
  - Rapid, replicable infrastructure audits at any urban mobility knot in India, using the same friction rubric.
  - Generating court-admissible, geotagged evidence maps for [PIL](https://en.wikipedia.org/wiki/Public_interest_litigation_in_India) filings on pedestrian rights.
  - Providing a quantitative baseline layer for [Transit-Oriented Development (TOD)](https://en.wikipedia.org/wiki/Transit-oriented_development) planning around station interchange zones.

- **Key Output:** An interactive `Folium` HTML map with colour-coded pins (`f = 2` → green, `f = 5` → red), a route polyline overlay for the surveyed corridor, and a static `Matplotlib` PNG for policy brief annexures.

---

### **2. Agent-Based Time Tax Simulator — `agent_sim.py`**

- **Abstract:** This module computes the traversal time and **Time Tax** for four commuter personas across the friction-mapped route. The physical model treats each path segment as imposing a velocity penalty governed by the local friction value. Rather than a simple linear reduction, which underestimates the compounding effect of high-friction segments on vulnerable users, we adopt a **power-law friction-velocity relationship**:

$$v_{eff}(i, \phi) = \frac{v_0(\phi)}{f_i^{\,k(\phi)}}$$

  The exponent `k(φ)` captures persona-specific friction sensitivity: a wheelchair user navigating broken slabs loses speed super-linearly compared to an able-bodied adult, reflecting the physical reality that small obstacles that merely slow one person completely stop another. The traversal time for segment `i` of length `d` is then:

$$\tau_i(\phi) = \frac{d}{v_{eff}(i, \phi)} = \frac{d \cdot f_i^{\,k(\phi)}}{v_0(\phi)}$$

  The **total actual traversal time** across all `N` segments is:

$$T_{actual}(\phi) = \sum_{i=1}^{N} \tau_i(\phi) = \frac{d}{v_0(\phi)} \sum_{i=1}^{N} f_i^{\,k(\phi)}$$

  The **ideal traversal time** (all segments at `f = 1`, i.e. a fully compliant S.U.R.E. footpath) is simply:

$$T_{ideal}(\phi) = \frac{D}{v_0(\phi)} = \frac{N \cdot d}{v_0(\phi)}$$

  The **Time Tax** per trip per persona is therefore:

$$\Delta\tau(\phi) = T_{actual}(\phi) - T_{ideal}(\phi) = \frac{d}{v_0(\phi)} \left( \sum_{i=1}^{N} f_i^{\,k(\phi)} - N \right)$$

  **Impassability and detour penalty:** When `f_i > f_{max}(\phi)`, the segment is impassable for that persona. The agent is rerouted into the vehicular Right-of-Way (ROW), incurring both a geometric detour of length `δ_i` (the distance to re-enter the footpath after the blockage) and a safety overhead modelled as a velocity penalty multiplier `α = 1.5` for walking in traffic:

$$\tau_i^{ROW}(\phi) = \frac{(d + \delta_i) \cdot \alpha}{v_0(\phi)}$$

  **Economic aggregation:** The aggregate daily Time Tax across `M` commuters and `W` working days per year is:

$$\mathcal{T}_{year} = M \cdot W \cdot \bar{\Delta\tau} = M \cdot W \cdot \frac{1}{|\Phi|} \sum_{\phi \in \Phi} \Delta\tau(\phi)$$

  where `Φ` is the set of persona types weighted by their estimated population share. For `M = 100,000`, `W = 250`, and the Yeshwantpur friction distribution, this yields an estimated loss of **~170 million person-minutes per year** — the headline figure for the DULT brief.

  **What-if scenario (Lighthouse Pilot):** When the top-`n` friction hotspots are set to `f = 1`, the reduction in Time Tax is:

$$\Delta\tau_{saved}(n, \phi) = \frac{d}{v_0(\phi)} \sum_{j=1}^{n} \left( f_j^{\,k(\phi)} - 1 \right)$$

  where nodes are sorted in descending order of `f_j^{k(\phi)}` to identify the maximum-impact fixes first. This directly drives the Streamlit slider — each increment of `n` shows the marginal gain from one more hotspot repair.

- **Applications:**
  - Quantifying the [disability-adjusted](https://en.wikipedia.org/wiki/Disability-adjusted_life_year) mobility cost imposed on wheelchair users and the elderly by non-compliant infrastructure.
  - Modelling how targeted fixes at the top-N friction hotspots reduce the aggregate Time Tax, providing a prioritised, low-cost recommendation for [BBMP](https://bbmp.gov.in/) and [DULT](https://dult.karnataka.gov.in/en).
  - Extending the framework to other Indian intermodal hubs (e.g. KSR Bengaluru, Majestic) for city-wide friction benchmarking.

- **Commuter Personas (`φ`):**

  | Agent | `v₀` (m/s) | Sensitivity `k` | `f_max` | Estimated Time Tax |
  |-------|-----------|-----------------|---------|-------------------|
  | 🚶 Able-bodied adult | 1.4 | 0.6 | 5 | Baseline |
  | 👴 Elderly commuter | 0.9 | 0.9 | 4 | +60–80% |
  | ♿ Wheelchair user | 0.8 | 1.2 | 3 → detour | +120–180% |
  | 🛵 Delivery partner | 1.2 | 0.75 | 4 | +40–60% |

---

### **3. Interactive Digital Twin — `streamlit_app.py`**

- **Abstract:** The Streamlit dashboard is the public-facing face of the project. A ive simulation environment that unifies the friction map, agent simulation, and speculative CAD redesign in one place. Users select a commuter persona, slide through "what-if" hotspot-fix scenarios, and watch the Time Tax recalculate in real time. It is designed for two contexts: as a self-explanatory public exhibit on Bengawalk's channels, and as a live demonstration tool in meetings with DULT and BBMP officials.

- **Applications:**
  - Communicating the human cost of infrastructure neglect to non-technical civic audiences and journalists through interactive, persona-driven storytelling.
  - Demonstrating the marginal return of fixing specific obstacles (e.g. *"Fixing just these 3 drains on Bazaar Street saves 38% of the total daily Time Tax"*) to make the policy ask concrete and costed.
  - Hosting the speculative CAD redesign as an embedded 3D viewer, allowing stakeholders to orbit, inspect, and annotate the proposed Tender S.U.R.E.-compliant corridor.

- **Dashboard Panels:**
  - **Left sidebar:** Persona selector, hotspot-fix slider (N = 1–10), "Run Simulation" trigger
  - **Centre:** Embedded `Folium` friction map with live route overlay
  - **Right panel:** Time Tax bar chart (current vs. fixed), per-agent breakdown, aggregate economic loss metric, embedded 3D CAD viewer

---

### **4. Speculative Redesign — CAD Model — `cad_viewer/`**

- **Abstract:** A static 3D cross-section of the Yeshwantpur corridor redesigned to Tender S.U.R.E. and [Active Mobility Bill](https://dult.karnataka.gov.in/121/active-mobility-bill/en) standards. Rather than modelling the full 900m route, the model covers a single representative 20–30m segment showing what a compliant stretch looks like: a 3m continuous footpath, flush pipe-and-chamber drainage, underground utility duct, and kerb ramps at each end. It is the "Streets of Hope" visual counterpart to the friction audit; concrete enough to hand to a contractor, simple enough to explain to a policymaker. Authored in **[Zoo.dev's KCL](https://zoo.dev/docs/kcl)**, exported to glTF via the KittyCAD API, and rendered as a static embed in the Streamlit dashboard.

- **Applications:**
  - Giving DULT and BBMP reviewers a dimensioned picture of exactly what the Lighthouse Pilot intervention involves — not a concept sketch, but a measurable cross-section.
  - Serving as the "before vs. after" visual for Bengawalk's [Instagram](https://www.instagram.com/bengawalk/) and X "Friction Files" posts.
  - Anchoring the policy brief's Lighthouse Proposal with a visual that non-engineers can immediately read.

- **Design specification:**

  | Element | Dimension |
  |---------|-----------|
  | Footpath width | 3m clear, per Tender S.U.R.E. |
  | Drainage | Pipe and chamber, flush with walking surface |
  | Kerb ramp | 1:12 grade at both ends |
  | Tactile paving | 0.6m warning strip at ramp head |
  | Utility duct | 0.5m wide, underground, lid flush |
  | Vendor setback | 1.5m marked zone behind footpath edge |

- **Workflow:**
  ```
  yeshwantpur_section.kcl    # KCL cross-section geometry
        ↓  (Zoo KittyCAD API)
  yeshwantpur_section.glb    # exported glTF
        ↓
  streamlit_app.py           # embedded via streamlit-model-viewer
  ```

---

### **5. Policy Brief Generator — `policy_brief.py`**

- **Abstract:** This headless script reads the simulation output and renders a submission-ready 2-page PDF using `ReportLab`. It packages the friction distribution pie chart, per-agent Time Tax bar chart, and an economic extrapolation table built on the aggregate formula:

$$\mathcal{T}_{year} = M \cdot W \cdot \bar{\Delta\tau}(\phi)$$

  where `M = 100,000` (daily commuters at the Yeshwantpur hub), `W = 250` (working days), and `Δτ̄(φ)` is the persona-averaged Time Tax per trip from the agent simulation. Converting person-minutes to economic value using the [Reserve Bank of India's](https://www.rbi.org.in/) implicit wage rate for informal workers (~₹50/hr), the brief reports an estimated annual productivity loss of **₹14.2 crore** attributable solely to the 900m audited stretch. The one-page "Lighthouse Proposal" then uses the what-if delta:

$$\Delta\tau_{saved}(n) = \frac{d}{v_0} \sum_{j=1}^{n} \left( f_j^{\,k} - 1 \right)$$

  to show that fixing the top 3 hotspots (estimated cost: ₹8–12 lakh for drain covers and slab repair) recovers approximately 38% of the annual Time Tax — a benefit-to-cost ratio exceeding 10:1. This framing is deliberately calibrated to the language of [BBMP](https://bbmp.gov.in/) project approvals, which require both a cost estimate and a quantified beneficiary impact.

- **Applications:**
  - Direct submission to DULT, BBMP, and the MLA of the Yeshwantpur constituency as a student-led contribution to the [Active Mobility Bill](https://dult.karnataka.gov.in/121/active-mobility-bill/en) discussion.
  - Annexing as supporting evidence in any future [PIL](https://en.wikipedia.org/wiki/Public_interest_litigation_in_India) on pedestrian infrastructure non-compliance at the Yeshwantpur hub.
  - Reuse as a template for parallel audits at other Bengaluru transit nodes.

- **Run headlessly:**
  ```bash
  python simulations/policy_brief.py --fixes 3 --output brief.pdf
  ```

---

## 🛠️ Tech Stack

| Layer | Tools |
|-------|-------|
| **Core Simulation** | `NumPy`, `SciPy` — path integration, friction modelling |
| **Geospatial** | `OSMnx`, `GeoPandas`, `NetworkX`, `Folium`, `GeoPy` — map data, routing, geotagging |
| **Visualisation** | `Matplotlib`, `Plotly`, `Altair` — charts, friction maps, time-series |
| **Web App** | `Streamlit` — interactive Digital Twin dashboard |
| **3D / CAD** | `Zoo.dev` / KCL (authoring) → glTF/GLB export via KittyCAD API → `streamlit-model-viewer` (embedded viewer) |
| **Reporting** | `ReportLab` — policy brief PDF generation |
| **Data** | `Pandas` — field audit data, interview notes, obstacle logs |
| **Language** | Python 3.10+ |

---

## 💻 Installation & Usage

1. **Clone the repository:**
    ```bash
    git clone https://github.com/AaitijhyaGoswami/escape-the-knot.git
    cd escape-the-knot
    ```

2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Run the Streamlit app:**
    ```bash
    streamlit run streamlit_app.py
    ```

4. **Run local simulations (no UI):**
    ```bash
    python simulations/agent_sim.py
    python simulations/friction_mapper.py
    ```

5. **Generate the policy brief PDF:**
    ```bash
    python simulations/policy_brief.py --fixes 3 --output brief.pdf
    ```

---

## 📂 Project Structure

```text
escape-the-knot/
├── data/
│   ├── audit_log.csv                       # Geotagged obstacle data with f-values
│   ├── interview_notes.md                  # Anonymised interview summaries (Kannada + English)
│   ├── personas.yaml                       # Agent config: v₀, k, f_max, label
│   └── route_nodes.geojson                 # Surveyed path as ordered geospatial nodes
├── simulations/
│   ├── friction_mapper.py                  # Spatial friction map generator
│   ├── agent_sim.py                        # Agent-based Time Tax model
│   └── policy_brief.py                     # Economic impact snapshot → PDF
├── cad_viewer/
│   ├── yeshwantpur_section.kcl             # Zoo.dev KCL source — compliant cross-section
│   ├── yeshwantpur_section.glb             # Exported glTF via KittyCAD API
│   └── viewer.py                           # Streamlit component wrapper
├── streamlit_app.py                        # Interactive Digital Twin dashboard
├── requirements.txt
└── README.md
```

---

## 🗓️ 14-Day Sprint Roadmap

| Phase | Days | Deliverable |
|-------|------|-------------|
| **Data Harvest** | 1–4 | Field audit, geotagged obstacle log, Kannada interviews |
| **Digital Build** | 5–9 | Streamlit app, agent-based sim, KCL model via Zoo.dev, SWOT slide deck |
| **Synthesis & Advocacy** | 10–14 | Policy brief PDF, Bengawalk 'Friction Files', DULT/BBMP submission |

---

## 🤝 Stakeholder Ecosystem

- **Regulatory:** [DULT](https://dult.karnataka.gov.in/en) (Active Mobility Bill), [BBMP](https://bbmp.gov.in/) (infrastructure), [BTP](https://btp.karnataka.gov.in/en) (enforcement)
- **Transit:** [BMRCL](https://english.bmrc.co.in/) (Metro), [South Western Railway](https://swr.indianrailways.gov.in/?lang=1), [BMTC](https://mybmtc.karnataka.gov.in/) (bus)
- **Community:** IISc student body, Mathikere RWAs, [Bengawalk](https://bengawalk.com/) collective
- **Frontline:** Gig-worker unions, delivery platforms (Swiggy, Zomato, Porter)
- **Missing Voices:** Sanitation workers, elderly pedestrians, persons with disabilities

---

## 🤝 Contributing

Contributions are welcome — especially extensions of the friction rubric to new survey areas, additional commuter personas, or improvements to the CAD model.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/NewSurveyZone`)
3. Commit your changes (`git commit -m 'Add Mathikere extended audit'`)
4. Push to the branch (`git push origin feature/NewSurveyZone`)
5. Open a Pull Request

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

<p align="center">
  Built with ❤️ for Bengaluru's pedestrians — and for the streets that should belong to them.
</p>
