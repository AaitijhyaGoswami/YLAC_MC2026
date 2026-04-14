import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

# -------------------------------------------------------------------------
# Streamlit static file serving
# Files in static/ are served at /app/static/ on Streamlit Cloud
# and at http://localhost:8501/app/static/ locally.
# The model-viewer src must be an absolute path — relative paths resolve
# against the iframe origin, not the app root.
# -------------------------------------------------------------------------

STATIC_BASE = "/app/static/cad_viewer"

# model-viewer via jsDelivr — more reliable on Streamlit Cloud than unpkg
MODEL_VIEWER_CDN = (
    "https://cdn.jsdelivr.net/npm/@google/model-viewer@3.4.0"
    "/dist/model-viewer.min.js"
)


def render_3d_model(filename: str, label: str, color: str, height: int = 500):
    """
    Render a glTF model using <model-viewer>.

    Parameters
    ----------
    filename : str
        Filename only (e.g. 'yeshwantpur.gltf') — the function prepends
        the correct /app/static/cad_viewer/ path.
    label : str
        Heading shown above the viewer.
    color : str
        Hex colour for the label text.
    height : int
        Height of the viewer in pixels.
    """
    model_url = f"{STATIC_BASE}/{filename}"

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <script type="module" src="{MODEL_VIEWER_CDN}"></script>
      <style>
        body {{
          margin: 0;
          background: transparent;
          font-family: 'Segoe UI', sans-serif;
        }}
        .label {{
          text-align: center;
          color: {color};
          font-size: 15px;
          font-weight: 500;
          margin: 8px 0 10px 0;
          letter-spacing: 0.02em;
        }}
        model-viewer {{
          width: 100%;
          height: {height}px;
          background-color: #0e1117;
          border-radius: 10px;
          border: 1px solid #2a2a2a;
          display: block;
        }}
        .error-box {{
          width: 100%;
          height: {height}px;
          background: #1a1a1a;
          border-radius: 10px;
          border: 1px dashed #444;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #666;
          font-size: 13px;
          text-align: center;
          padding: 20px;
          box-sizing: border-box;
        }}
      </style>
    </head>
    <body>
      <div class="label">{label}</div>
      <model-viewer
        src="{model_url}"
        alt="{label}"
        auto-rotate
        camera-controls
        shadow-intensity="1.5"
        exposure="1.1"
        environment-image="neutral"
        tone-mapping="neutral"
        onerror="this.style.display='none'; document.getElementById('err_{filename.replace('.','_')}').style.display='flex';"
      ></model-viewer>
      <div id="err_{filename.replace('.','_')}" class="error-box" style="display:none;">
        Model could not load. <br \>
        Check that <code>static/cad_viewer/{filename}</code> exists <br \>
        and <code>enableStaticServing = true</code> is set in <br \>
        <code>.streamlit/config.toml </code>
      </div>
    </body>
    </html>
    """
    components.html(html_code, height=height + 60, scrolling=False)


def app():
    st.title("What-If: Lighthouse Prototype")
    st.markdown(
        "3D cross-sections of the Yeshwantpur corridor — as-surveyed ($f=5$) "
        "versus the proposed [Tender S.U.R.E.](https://www.janausp.org/portfolio/tender-sure) "
        "redesign ($f=1$). Models exported from Zoo.dev KCL via the KittyCAD API."
    )
    st.markdown("---")

    # -----------------------------------------------------------------------
    # DIAGNOSTIC — helps catch path issues early
    # -----------------------------------------------------------------------
    with st.expander("🔧 Model path diagnostic", expanded=False):
        st.markdown(
            "Models are served from `static/cad_viewer/` via Streamlit's static "
            "file server. Confirm your `.streamlit/config.toml` contains:"
        )
        st.code("[server]\nenableStaticServing = true", language="toml")
        st.markdown("Files resolved to:")
        st.code(
            f"{STATIC_BASE}/yeshwantpur.gltf\n"
            f"{STATIC_BASE}/f=1.gltf",
            language="text"
        )
        st.info(
            "If models show a grey box instead of rendering, open your browser's "
            "DevTools → Network tab and check whether the `.gltf` request returns "
            "200 or 404. A 404 means the static path is wrong."
        )

    # -----------------------------------------------------------------------
    # SIDE-BY-SIDE MODEL VIEWERS
    # -----------------------------------------------------------------------
    col_f5, col_f1 = st.columns(2)

    with col_f5:
        st.markdown("##### Current conditions — $f = 5$ · Systemic Failure")
        render_3d_model(
            filename="yeshu.gltf",
            label="As Surveyed — Footpath absent, encroachments permanent",
            color="#F44336",
        )

    with col_f1:
        st.markdown("##### Proposed redesign — $f = 1$ · Tender S.U.R.E. standard")
        render_3d_model(
            filename="f=1.gltf",
            label="S.U.R.E. Compliant — 3m clear path, integrated drainage",
            color="#4CAF50",
        )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # SPATIAL COMPARISON TABLE
    # -----------------------------------------------------------------------
    st.markdown("#### Spatial Allocation Comparison")
    comparison_df = pd.DataFrame({
        "Element": [
            "Pedestrian carriageway",
            "Drainage system",
            "Vending / utilities zone",
            "Overhead clearance",
            "Kerb ramps",
            "Barriers",
        ],
        "Current (f=5)": [
            "0.0 m — footpath fully colonised",
            "Open box drain, uncovered",
            "3.0 m (encroachment — vendors, transformers)",
            "Low-hanging cables — not measured",
            "Absent",
            "800mm masonry wall + 800mm mesh",
        ],
        "Proposed (f=1)": [
            "3.0 m continuous clear path",
            "Integrated pipe-and-chamber system (S.U.R.E.)",
            "1.5 m designated zone, set back from path",
            "2.5 m minimum per IRC 103",
            "Kerb ramps at all crossings (IRC 103)",
            "None",
        ],
    })
    st.table(comparison_df)

    # -----------------------------------------------------------------------
    # EFFECTIVE WIDTH DERIVATION
    # -----------------------------------------------------------------------
    with st.expander("Mathematical justification — effective width model"):
        st.markdown(
            "The usable pedestrian width $W_\\text{eff}$ is the total carriageway "
            "width minus all obstacles and safety buffers:"
        )
        st.latex(
            r"W_{\text{eff}} = W_{\text{total}} - W_{\text{obstacles}} - W_{\text{buffer}}"
        )
        st.markdown(
            "In the current $f=5$ configuration, $W_\\text{obstacles}$ includes the "
            "masonry wall (0.8 m), mesh fence (0.8 m), and vendor encroachment (3.0 m), "
            "leaving $W_\\text{eff} \\approx 0$ m — the footpath is fully impassable."
        )
        st.latex(
            r"W_{\text{eff}}^{(f=5)} = 4.6 - 0.8 - 0.8 - 3.0 = 0.0\text{ m}"
        )
        st.markdown(
            "The S.U.R.E. redesign reallocates the space, achieving:"
        )
        st.latex(
            r"W_{\text{eff}}^{(f=1)} = 4.6 - 0.0 - 0.1 = \geq 3.0\text{ m}"
            r"\quad \checkmark \text{ (S.U.R.E. minimum)}"
        )
        st.markdown(
            "This maps directly to $f=1$ in the friction rubric — a continuous, "
            "unobstructed 3m+ footpath requiring zero additional pedestrian effort."
        )

    # -----------------------------------------------------------------------
    # WHAT-IF DELTA
    # -----------------------------------------------------------------------
    st.markdown("---")
    st.markdown("#### What the Redesign Recovers")
    c1, c2, c3 = st.columns(3)
    c1.metric("Footpath width restored", "0 m → 3.0 m")
    c2.metric("Friction index change", "f=5 → f=1", delta="−4 levels", delta_color="normal")
    c3.metric("Time Tax recovered (top-3 fix)", "~38% of annual total")
    st.caption(
        "The top-3 friction hotspot fix (all f=5 on Bazaar Street) costs an estimated "
        "₹8–12 lakh and delivers a benefit-to-cost ratio exceeding 10:1. "
        "See the **Economic Impact** module for the full aggregation."
    )
