# 🚶 Escape the Knot: Yeshwantpur–Mathikere Mobility Nexus
### A Physics-Based Pedestrian Accessibility Audit & Simulation Suite

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-ff4b4b)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-success)
![Campaign](https://img.shields.io/badge/YLAC-Mobility_Champions_2026-orange)

> **Authors:** [Aaitijhya Goswami](https://www.linkedin.com/in/aaitijhya-goswami-553940280/) & [Prajwal Kagalgomb](https://www.linkedin.com/)  
> **Partner Organisation:** [Bengawalk](https://bengawalk.com/)  
> **Programme:** YLAC Mobility Champions 2026

---

## 📖 Overview

This project is a **Pedestrian Mobility Audit and Agent-Based Simulation Suite** developed to quantify the *infrastructural tax* imposed on pedestrians at the Yeshwantpur Mobility Knot in Bengaluru. It combines physics-driven modelling with ground-level advocacy to make a data-backed case for the transformation of Yeshwantpur into a **"Lighthouse Pilot"** for Tender S.U.R.E.-compliant intermodal pedestrian infrastructure.

By treating the city as a physical system — where broken drains, encroachments, and missing footpaths act as **potential energy barriers Φ(x)** — we compute the **Effective Path Length**:

$$L_{eff} = \int_0^D f(x, \phi) \, dx$$

where `f` is a friction parameter (1–5) representing obstacle severity, and `φ` encodes the commuter persona (able-bodied, wheelchair user, delivery worker, etc.).

The result: a **Time Tax** — the measurable seconds stolen from 100,000+ daily commuters by a system that was never designed for them.

---

## 🗺️ Campaign Context

**Survey Area:** The 900m stretch connecting Yeshwantpur Railway Station to Constitution Circle, the SWR–Metro interchange corridor, and the 0.45 km² Mathikere road network.

**Key Findings (Milestone 1 Survey — March 7–8, 2026):**
- **90.3%** of the 900m stretch fails Active Mobility Bill standards
- **96%** of it is inaccessible for wheelchair users
- **79.18%** of geotagged obstacles rated `f = 5` (Systemic Failure — footpath ends entirely)
- The entire 600m Bazaar Street stretch is rated `f = 5`, forcing pedestrians into vehicular Right-of-Way

**Policy Target:** Mandate **Tender S.U.R.E. Design Standards** via DULT's Active Mobility Bill — specifically replacing open box drains with integrated "Pipe and Chamber" systems to create a continuous, accessible walking surface.

---

## 🚀 Simulation Modules

### 1. `friction_mapper.py` — Obstacle Parameterisation & Spatial Friction Map
Models the survey-audited route as a discretised path with friction values assigned to each segment node. Overlays the `f`-value distribution onto a Folium/GeoPandas map with colour-coded pins matching the rubric:

| Level | Label | Description |
|-------|-------|-------------|
| `f = 1` | 🟢 Gold Standard | Continuous, wide footpath — stroller and wheelchair accessible |
| `f = 2` | 🟡 Distracted Walk | Minor cracks / hanging cables; requires constant attention |
| `f = 3` | 🟠 Obstacle Course | Broken slabs, rubble — effective pace halved |
| `f = 4` | 🔴 Physical Barrier | Forced stop; high curb or missing drain cover |
| `f = 5` | ⚫ Systemic Failure | Footpath ends; pedestrian enters vehicular ROW |

### 2. `agent_sim.py` — Agent-Based Time Tax Simulation
Computes `L_eff` and **Time Tax (seconds)** for four commuter personas traversing the audited path:

- 🚶 **Able-bodied adult** — baseline traversal speed
- 👴 **Elderly commuter** — reduced speed, higher sensitivity to `f ≥ 3`
- ♿ **Wheelchair user** — `f ≥ 4` nodes become impassable; forced detour routing
- 🛵 **Delivery partner** — carrying load; affected by `f ≥ 3` surface discontinuities

Each agent's journey is compared against a **hypothetical standardised path** (`f = 1` throughout) to yield the delta in traversal time — the Time Tax.

### 3. `streamlit_app.py` — Interactive Digital Twin (Hosted on Streamlit)
A Streamlit dashboard allowing users to:
- Toggle between commuter personas and see their effective path in real time
- Visualise the friction gradient along the 700m route
- Compute and display the **aggregate daily Time Tax** for 100,000+ commuters
- Explore "what-if" scenarios: *What if we fix just the top 3 friction hotspots?*

### 4. `policy_brief.py` — Economic Snapshot Generator
Extrapolates individual Time Tax values into city-scale economic loss metrics, formatted as a 2-page output ready for submission to DULT and BBMP.

---

## 🛠️ Tech Stack

| Layer | Tools |
|-------|-------|
| **Core Simulation** | `NumPy`, `SciPy` — path integration, friction modelling |
| **Geospatial** | `OSMnx`, `GeoPandas`, `NetworkX`, `Folium`, `GeoPy` — map data, routing, geotagging |
| **Visualisation** | `Matplotlib`, `Plotly`, `Altair` — charts, friction maps, time-series |
| **Web App** | `Streamlit` — interactive Digital Twin dashboard |
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
    python agent_sim.py
    python friction_mapper.py
    ```

---

## 📂 Project Structure

```text
escape-the-knot/
├── data/
│   ├── audit_log.csv              # Geotagged obstacle data with f-values
│   ├── interview_notes.md         # Anonymised interview summaries
│   └── route_nodes.geojson        # Surveyed path as geospatial nodes
├── simulations/
│   ├── friction_mapper.py         # Spatial friction map generator
│   ├── agent_sim.py               # Agent-based Time Tax model
│   └── policy_brief.py            # Economic impact snapshot
├── streamlit_app.py               # Interactive Digital Twin dashboard
├── requirements.txt
└── README.md
```

---

## 📊 Survey Results at a Glance

```
Friction Distribution — 900m Yeshwantpur Stretch
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
f = 5 (Systemic Failure)  ████████████████████  79.18%
f = 4 (Physical Barrier)  ███                   11.11%
f = 3 (Obstacle Course)   █                      4.16%
f = 2 (Distracted Walk)   █                      5.55%
f = 1 (Gold Standard)                             0.00%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
90.3% fails Active Mobility Bill standards
96.0% inaccessible for wheelchair users
```

---

## 🗓️ 14-Day Sprint Roadmap

| Phase | Days | Deliverable |
|-------|------|-------------|
| **Data Harvest** | 1–4 | Field audit, geotagged obstacle log, Kannada interviews |
| **Digital Build** | 5–9 | Streamlit app, agent-based sim, SWOT slide deck |
| **Synthesis & Advocacy** | 10–14 | Policy brief, Bengawalk 'Friction Files', DULT/BBMP submission |

---

## 🤝 Stakeholder Ecosystem

- **Regulatory:** DULT (Active Mobility Bill), BBMP (infrastructure), BTP (enforcement)
- **Transit:** BMRCL (Metro), South Western Railway, BMTC (bus)
- **Community:** IISc student body, Mathikere RWAs, Bengawalk collective
- **Frontline:** Gig-worker unions, delivery platforms (Swiggy, Zomato, Porter)
- **Missing Voices:** Sanitation workers, elderly pedestrians, persons with disabilities

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

<p align="center">
  Built with ❤️ for Bengaluru's pedestrians — and for the streets that should belong to them.
  <br><br>
  <a href="https://bengawalk.com">Bengawalk</a> · <a href="#">YLAC Mobility Champions 2026</a>
</p>
