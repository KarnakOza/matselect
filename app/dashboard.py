"""
MatSelect — Streamlit Dashboard
Materials selection for propulsion hardware, grounded in real measured data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from engine.database import get_all
from engine.topsis import select_materials

st.set_page_config(page_title="MatSelect", layout="wide")

st.title("MatSelect")
st.caption("Materials selection for propulsion hardware — grounded in real measured data, not guesswork.")

# --- Sidebar: inputs ---
with st.sidebar:
    st.header("Component & Conditions")

    component = st.selectbox(
        "Component type",
        [
            "Combustion chamber liner",
            "Turbopump shaft / disc",
            "Propellant tank",
            "Thruster nozzle",
            "Structural bracket / frame",
            "Cryogenic propellant line",
            "Nozzle exit cone / fairing",
        ]
    )

    min_temp = st.slider("Minimum service temperature (K)", 200, 1800, 700, step=50)

    cryo_required = st.checkbox("Must be cryogenic compatible (LOX/LH2 contact)")
    no_h2_risk = st.checkbox("Must avoid hydrogen embrittlement risk")
    am_required = st.checkbox("Must be additive-manufacturing qualified")
    must_weld = st.checkbox("Must be easily weldable")

    max_cost = st.select_slider(
        "Maximum acceptable cost",
        options=[1, 2, 3, 4, 5],
        value=5,
        format_func=lambda x: ["Lowest", "Low", "Moderate", "High", "Any"][x-1]
    )

    st.divider()
    st.subheader("Priority weights")
    st.caption("Drag to change what matters most. Rankings update live.")

    w_temp = st.slider("Temperature capability", 0.0, 3.0, 2.0, 0.1)
    w_yield = st.slider("Strength", 0.0, 3.0, 1.0, 0.1)
    w_conductivity = st.slider("Thermal conductivity (cooling)", 0.0, 3.0, 1.5, 0.1)
    w_density = st.slider("Low mass importance", 0.0, 3.0, 1.0, 0.1)
    w_oxidation = st.slider("Oxidation resistance", 0.0, 3.0, 1.5, 0.1)
    w_trl = st.slider("Flight heritage / TRL", 0.0, 3.0, 1.5, 0.1)
    w_cost = st.slider("Cost sensitivity", 0.0, 3.0, 1.0, 0.1)

# --- Build constraints and weights dicts ---
constraints = {
    "min_service_temp_K": min_temp,
    "cryogenic_required": cryo_required,
    "no_hydrogen_risk": no_h2_risk,
    "max_cost_index": max_cost,
    "must_be_weldable": must_weld,
    "am_required": am_required,
}

weights = {
    "w_yield": w_yield,
    "w_temp": w_temp,
    "w_conductivity": w_conductivity,
    "w_density": w_density,
    "w_oxidation": w_oxidation,
    "w_weldability": 1.0,
    "w_cost": w_cost,
    "w_trl": w_trl,
}

# --- Run selection ---
results = select_materials(component, constraints, weights)

if results["error"]:
    st.error(results["error"])
    st.info("Try lowering the minimum temperature or relaxing a constraint in the sidebar.")
else:
    ranked = results["ranked"]

    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader(f"Ranked materials for: {component}")

        table_data = []
        for r in ranked:
            m = r["material"]
            table_data.append({
                "Rank": r["rank"],
                "Material": m["name"],
                "Score": r["topsis_score"],
                "Yield (MPa)": m["yield_strength_MPa"],
                "Max Temp (K)": m["max_service_temp_K"],
                "Density (kg/m³)": m["density_kgm3"],
                "TRL": m["trl_propulsion"],
            })

        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        if results["eliminated"]:
            with st.expander(f"Eliminated materials ({len(results['eliminated'])})"):
                for mid, reasons in results["eliminated"].items():
                    st.write(f"**{mid}**: {'; '.join(reasons)}")

    with col2:
        st.subheader("TOPSIS Score Comparison")
        fig = go.Figure(go.Bar(
            x=[r["topsis_score"] for r in ranked],
            y=[r["material"]["name"] for r in ranked],
            orientation="h",
            marker_color="#2563eb"
        ))
        fig.update_layout(
            yaxis=dict(autorange="reversed"),
            height=350,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Why the top candidates ranked where they did")

    for reasoning_text in results["reasoning"]:
        st.markdown(reasoning_text)
        st.markdown("---")

st.divider()
st.caption(
    f"Database: {len(get_all())} materials with cited sources. "
    "Built on measured properties from NASA technical reports, "
    "AMS specifications, and manufacturer datasheets — not theoretical predictions."
)