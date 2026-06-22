"""
MatSelect — Streamlit Dashboard v3
Landing: interactive material card grid
Selection: click a rocket component on a schematic → ranked materials
Ashby plots for visual trade-off analysis
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from engine.database import get_all
from engine.topsis import select_materials
import numpy as np

st.set_page_config(page_title="MatSelect", layout="wide", page_icon="🚀")

# ── Category colours ──────────────────────────────────────────────────────────
CAT_COLOR = {
    "nickel_superalloy":  "#ef4444",
    "copper_alloy":       "#f97316",
    "titanium_alloy":     "#3b82f6",
    "stainless_steel":    "#6b7280",
    "aluminium_alloy":    "#a3e635",
    "composite":          "#8b5cf6",
    "refractory_alloy":   "#14b8a6",
}
CAT_LABEL = {
    "nickel_superalloy":  "Ni Superalloy",
    "copper_alloy":       "Cu Alloy",
    "titanium_alloy":     "Ti Alloy",
    "stainless_steel":    "Stainless",
    "aluminium_alloy":    "Al Alloy",
    "composite":          "Composite",
    "refractory_alloy":   "Refractory",
}

# ── Component → constraint presets ───────────────────────────────────────────
COMPONENT_PRESETS = {
    "Combustion Chamber Liner": {
        "min_service_temp_K": 700,
        "cryogenic_required": False,
        "no_hydrogen_risk": False,
        "must_be_weldable": False,
        "am_required": False,
        "max_cost_index": 5,
        "w_temp": 2.0, "w_yield": 1.0, "w_conductivity": 2.5,
        "w_density": 0.5, "w_oxidation": 2.0, "w_trl": 1.5, "w_cost": 0.5,
    },
    "Turbopump Shaft / Disc": {
        "min_service_temp_K": 600,
        "cryogenic_required": False,
        "no_hydrogen_risk": False,
        "must_be_weldable": False,
        "am_required": False,
        "max_cost_index": 5,
        "w_temp": 1.5, "w_yield": 3.0, "w_conductivity": 0.5,
        "w_density": 1.0, "w_oxidation": 1.5, "w_trl": 2.0, "w_cost": 0.5,
    },
    "Propellant Tank": {
        "min_service_temp_K": 200,
        "cryogenic_required": True,
        "no_hydrogen_risk": True,
        "must_be_weldable": True,
        "am_required": False,
        "max_cost_index": 4,
        "w_temp": 0.5, "w_yield": 1.5, "w_conductivity": 0.5,
        "w_density": 3.0, "w_oxidation": 0.5, "w_trl": 2.0, "w_cost": 1.5,
    },
    "Thruster Nozzle": {
        "min_service_temp_K": 1200,
        "cryogenic_required": False,
        "no_hydrogen_risk": False,
        "must_be_weldable": False,
        "am_required": False,
        "max_cost_index": 5,
        "w_temp": 3.0, "w_yield": 1.0, "w_conductivity": 1.0,
        "w_density": 0.5, "w_oxidation": 2.5, "w_trl": 1.5, "w_cost": 0.3,
    },
    "Nozzle Extension": {
        "min_service_temp_K": 1500,
        "cryogenic_required": False,
        "no_hydrogen_risk": False,
        "must_be_weldable": False,
        "am_required": False,
        "max_cost_index": 5,
        "w_temp": 3.0, "w_yield": 0.5, "w_conductivity": 1.0,
        "w_density": 1.0, "w_oxidation": 2.0, "w_trl": 1.0, "w_cost": 0.3,
    },
    "Structure / Interstage": {
        "min_service_temp_K": 200,
        "cryogenic_required": False,
        "no_hydrogen_risk": False,
        "must_be_weldable": True,
        "am_required": False,
        "max_cost_index": 3,
        "w_temp": 0.3, "w_yield": 2.0, "w_conductivity": 0.3,
        "w_density": 3.0, "w_oxidation": 0.5, "w_trl": 2.0, "w_cost": 2.0,
    },
    "Gas Generator Liner": {
        "min_service_temp_K": 900,
        "cryogenic_required": False,
        "no_hydrogen_risk": False,
        "must_be_weldable": False,
        "am_required": False,
        "max_cost_index": 5,
        "w_temp": 2.5, "w_yield": 1.5, "w_conductivity": 1.0,
        "w_density": 0.5, "w_oxidation": 2.5, "w_trl": 1.5, "w_cost": 0.5,
    },
    "Pressure Vessel / Manifold": {
        "min_service_temp_K": 300,
        "cryogenic_required": False,
        "no_hydrogen_risk": False,
        "must_be_weldable": True,
        "am_required": False,
        "max_cost_index": 4,
        "w_temp": 1.0, "w_yield": 2.5, "w_conductivity": 0.5,
        "w_density": 1.0, "w_oxidation": 1.0, "w_trl": 2.0, "w_cost": 1.0,
    },
}


# ── Chart helpers ─────────────────────────────────────────────────────────────

def make_sn_chart(ranked_top3):
    """
    Approximate S-N curves for top 3 TOPSIS materials.
    Anchor points:
      10^3 cycles  → 0.90 × UTS
      10^6 cycles  → 0.45 × UTS  (Ni/steel),  0.35 × UTS  (Al/Ti/Cu)
      10^7 cycles  → same as 10^6 (endurance limit plateau)
    Log-linear interpolation between 10^3 and 10^6.
    """
    LOW_ENDURANCE = {"aluminium_alloy", "titanium_alloy", "copper_alloy", "composite"}

    cycles = np.logspace(3, 7, 200)
    colors = ["#00ff88", "#f97316", "#3b82f6"]

    fig = go.Figure()

    for i, r in enumerate(ranked_top3):
        m = r["material"]
        uts = m["ultimate_strength_MPa"]
        if uts == 0:
            continue

        endurance_frac = 0.35 if m["category"] in LOW_ENDURANCE else 0.45
        s_1e3 = 0.90 * uts
        s_end = endurance_frac * uts

        log_c = np.log10(cycles)
        stress = np.where(
            cycles <= 1e6,
            s_1e3 + (s_end - s_1e3) * (log_c - 3) / (6 - 3),
            s_end
        )

        fig.add_trace(go.Scatter(
            x=cycles, y=stress,
            mode="lines",
            name=f"#{r['rank']} {m['name']}",
            line=dict(color=colors[i], width=2),
            hovertemplate=(
                f"<b>{m['name']}</b><br>"
                "Cycles: %{x:.2e}<br>"
                "Fatigue stress: %{y:.0f} MPa<extra></extra>"
            )
        ))

        fig.add_annotation(
            x=np.log10(1.2e6), y=s_end,
            xref="x", yref="y",
            text=f"{s_end:.0f} MPa",
            showarrow=False,
            font=dict(size=9, color=colors[i]),
            xanchor="left"
        )

    fig.add_annotation(
        x=0.02, y=0.97, xref="paper", yref="paper",
        text="⚠ ESTIMATED — Basquin approximation from UTS.<br>Not a substitute for test data.",
        showarrow=False,
        font=dict(size=9, color="#f97316"),
        bgcolor="rgba(10,15,10,0.85)",
        bordercolor="#f97316", borderwidth=1,
        align="left", xanchor="left", yanchor="top"
    )

    fig.update_layout(
        xaxis=dict(
            type="log", title="Cycles to Failure (N)",
            gridcolor="#1a3a1a", color="#00ff88",
            tickvals=[1e3, 1e4, 1e5, 1e6, 1e7],
            ticktext=["10³", "10⁴", "10⁵", "10⁶", "10⁷"]
        ),
        yaxis=dict(title="Fatigue Stress (MPa)", gridcolor="#1a3a1a", color="#00ff88"),
        plot_bgcolor="#0a0f0a", paper_bgcolor="#0a0f0a",
        font=dict(color="#00ff88", family="monospace"),
        legend=dict(bgcolor="rgba(10,15,10,0.8)", bordercolor="#1a3a1a"),
        height=400,
        margin=dict(l=10, r=10, t=30, b=10),
    )
    return fig


def make_temp_timeline(materials_list):
    """
    Horizontal bar chart: min_service_temp_K → max_service_temp_K per material.
    """
    names  = [m["name"] for m in materials_list]
    lows   = [m["min_service_temp_K"] for m in materials_list]
    highs  = [m["max_service_temp_K"] for m in materials_list]
    widths = [h - l for l, h in zip(lows, highs)]
    cats   = [m["category"] for m in materials_list]
    colors_bar = [CAT_COLOR.get(c, "#4a8a5a") for c in cats]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=widths, y=names,
        base=lows,
        orientation="h",
        marker_color=colors_bar,
        marker_line_width=0,
        customdata=list(zip(lows, highs, [CAT_LABEL.get(c, c) for c in cats])),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "%{customdata[2]}<br>"
            "Min: %{customdata[0]} K<br>"
            "Max: %{customdata[1]} K<extra></extra>"
        )
    ))

    refs = [
        (20,   "#60a5fa", "LH₂ (20 K)"),
        (90,   "#3b82f6", "LOX (90 K)"),
        (293,  "#4a8a5a", "Ambient (293 K)"),
        (1000, "#f97316", "Turbine inlet (~1000 K)"),
        (1800, "#ef4444", "Chamber wall (~1800 K)"),
    ]
    for xval, col, label in refs:
        fig.add_vline(x=xval, line_dash="dash", line_color=col, line_width=1, opacity=0.6)
        fig.add_annotation(
            x=xval, y=1.01, yref="paper",
            text=label, showarrow=False,
            font=dict(size=7, color=col),
            textangle=-45, xanchor="left"
        )

    fig.update_layout(
        xaxis=dict(
            title="Temperature (K)", gridcolor="#1a3a1a", color="#00ff88",
            range=[0, max(highs) * 1.05]
        ),
        yaxis=dict(color="#00ff88", autorange="reversed"),
        plot_bgcolor="#0a0f0a", paper_bgcolor="#0a0f0a",
        font=dict(color="#00ff88", family="monospace"),
        height=max(320, len(materials_list) * 28),
        margin=dict(l=10, r=10, t=50, b=10),
        bargap=0.25,
    )
    return fig


# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

  html, body, [class*="css"] {
    background-color: #0a0f0a;
    color: #00ff88;
    font-family: 'Share Tech Mono', monospace;
  }

  .mat-card {
    background: #0d1a0d;
    border: 1px solid #1a3a1a;
    border-radius: 4px;
    padding: 12px 10px;
    margin: 4px;
    cursor: pointer;
    transition: border-color 0.2s, background 0.2s;
    min-height: 110px;
  }
  .mat-card:hover {
    border-color: #00ff88;
    background: #122012;
  }
  .mat-card .mat-name {
    font-size: 0.78rem;
    font-weight: bold;
    color: #00ff88;
    margin-bottom: 4px;
  }
  .mat-card .mat-cat {
    font-size: 0.65rem;
    color: #4a8a5a;
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .mat-card .mat-stat {
    font-size: 0.7rem;
    color: #88cc99;
  }

  .section-title {
    font-size: 0.7rem;
    color: #4a8a5a;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 2px;
  }
  .hero-title {
    font-size: 2.2rem;
    font-weight: bold;
    color: #00ff88;
    letter-spacing: 0.1em;
    margin-bottom: 0;
  }
  .hero-sub {
    font-size: 0.85rem;
    color: #4a8a5a;
    margin-bottom: 1.5rem;
  }

  div[data-testid="stTabs"] button {
    color: #4a8a5a !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.1em !important;
  }
  div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #00ff88 !important;
    border-bottom: 2px solid #00ff88 !important;
  }

  .stSelectbox label, .stSlider label, .stCheckbox label {
    color: #4a8a5a !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.08em !important;
  }

  .stDataFrame { border: 1px solid #1a3a1a; }

  .comp-badge {
    display: inline-block;
    background: #122012;
    border: 1px solid #00ff88;
    border-radius: 3px;
    padding: 6px 14px;
    margin: 4px;
    font-size: 0.75rem;
    color: #00ff88;
    cursor: pointer;
    letter-spacing: 0.08em;
  }
  .comp-badge:hover { background: #1e3a1e; }

  .rank-1 { border-left: 3px solid #00ff88; }
  .rank-2 { border-left: 3px solid #22cc66; }
  .rank-3 { border-left: 3px solid #118844; }
</style>
""", unsafe_allow_html=True)


# ── Load data ─────────────────────────────────────────────────────────────────
all_mats = get_all()

# Schema guard — catches missing keys from database early
required_keys = [
    "name", "category", "yield_strength_MPa", "ultimate_strength_MPa",
    "max_service_temp_K", "min_service_temp_K", "density_kgm3",
    "trl_propulsion", "thermal_conductivity_WmK", "cryogenic_compatible",
    "hydrogen_embrittlement_risk", "AM_compatible", "oxidation_resistance",
    "weldability", "typical_components", "heritage", "source",
    "elongation_pct", "hardness_HV", "melting_point_K",
]
for m in all_mats:
    missing = [k for k in required_keys if k not in m]
    if missing:
        st.error(f"Material '{m.get('name', 'UNKNOWN')}' missing keys: {missing}")
        st.stop()


# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">// PROPULSION MATERIALS INTELLIGENCE</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-title">MATSELECT</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Materials selection for propulsion hardware — real measured data, cited sources, no guesswork.</p>', unsafe_allow_html=True)

col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
with col_stat1:
    st.metric("Materials in DB", len(all_mats))
with col_stat2:
    st.metric("Categories", len(set(m["category"] for m in all_mats)))
with col_stat3:
    st.metric("Max TRL", max(m["trl_propulsion"] for m in all_mats))
with col_stat4:
    st.metric("Temp Range (K)", f"{min(m['min_service_temp_K'] for m in all_mats)} – {max(m['max_service_temp_K'] for m in all_mats)}")

st.divider()


# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "◈  MATERIAL LIBRARY",
    "◈  COMPONENT SELECTOR",
    "◈  ASHBY PLOTS",
])


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — MATERIAL LIBRARY (card grid)
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<p class="section-title">// MATERIAL LIBRARY — 18 ALLOYS · CLICK TO INSPECT</p>', unsafe_allow_html=True)

    categories = sorted(set(m["category"] for m in all_mats))
    selected_cats = st.multiselect(
        "Filter by category",
        options=categories,
        default=categories,
        format_func=lambda c: CAT_LABEL.get(c, c),
    )

    filtered = [m for m in all_mats if m["category"] in selected_cats]

    cols_per_row = 4
    rows = [filtered[i:i + cols_per_row] for i in range(0, len(filtered), cols_per_row)]

    for row in rows:
        grid_cols = st.columns(cols_per_row)
        for col, mat in zip(grid_cols, row):
            with col:
                cat_color = CAT_COLOR.get(mat["category"], "#4a8a5a")
                cat_label = CAT_LABEL.get(mat["category"], mat["category"])
                card_html = f"""
                <div class="mat-card" style="border-top: 2px solid {cat_color};">
                  <div class="mat-name">{mat['name']}</div>
                  <div class="mat-cat" style="color:{cat_color}">{cat_label}</div>
                  <div class="mat-stat">⚡ {mat['yield_strength_MPa']} MPa yield</div>
                  <div class="mat-stat">🌡 {mat['max_service_temp_K']} K max</div>
                  <div class="mat-stat">⚖ {mat['density_kgm3']} kg/m³</div>
                  <div class="mat-stat">TRL {mat['trl_propulsion']}</div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)

                # FIX: use on_click + default-arg capture so every button
                # captures its own mat, not the last one in the loop.
                # key uses mat name (safe) instead of mat["id"] (may not exist).
                st.button(
                    "Inspect →",
                    key=f"btn_{mat['name'].replace(' ', '_').replace('/', '_')}",
                    on_click=lambda m=mat: st.session_state.update({"selected_material": m}),
                    use_container_width=True,
                )

    # ── Detail panel ─────────────────────────────────────────────────────────
    if "selected_material" in st.session_state:
        m = st.session_state["selected_material"]
        st.divider()
        st.markdown(
            f'<p class="section-title">// MATERIAL DETAIL — {m["name"].upper()}</p>',
            unsafe_allow_html=True
        )
        d1, d2, d3 = st.columns(3)

        with d1:
            st.markdown("**Mechanical**")
            st.write(f"Yield Strength: **{m['yield_strength_MPa']} MPa**")
            st.write(f"Ultimate Strength: **{m['ultimate_strength_MPa']} MPa**")
            st.write(f"Elongation: **{m['elongation_pct']}%**")
            st.write(f"Hardness: **{m['hardness_HV']} HV**")

        with d2:
            st.markdown("**Thermal**")
            st.write(f"Max Service Temp: **{m['max_service_temp_K']} K**")
            st.write(f"Min Service Temp: **{m['min_service_temp_K']} K**")
            st.write(f"Melting Point: **{m['melting_point_K']} K**")
            st.write(f"Thermal Conductivity: **{m['thermal_conductivity_WmK']} W/mK**")

        with d3:
            st.markdown("**Propulsion Flags**")
            st.write(f"Cryogenic Compatible: **{'✅' if m['cryogenic_compatible'] else '❌'}**")
            st.write(f"H₂ Embrittlement Risk: **{'⚠️ Yes' if m['hydrogen_embrittlement_risk'] else '✅ No'}**")
            st.write(f"AM Compatible: **{'✅' if m['AM_compatible'] else '❌'}**")
            st.write(f"Oxidation Resistance: **{m['oxidation_resistance']}/5**")
            st.write(f"Weldability: **{m['weldability']}/5** (1=best)")

        st.markdown(f"**Typical components:** {', '.join(m['typical_components'])}")
        st.markdown(f"**Heritage:** {', '.join(m['heritage'][:3])}")
        st.caption(f"Source: {m['source']}")

        # ── S-N curve for the inspected material alone ────────────────────
        st.divider()
        st.markdown('<p class="section-title">// FATIGUE — ESTIMATED S-N CURVE</p>', unsafe_allow_html=True)
        st.caption("Approximate S-N curve derived from UTS via Basquin method.")
        st.plotly_chart(
            make_sn_chart([{"rank": 1, "material": m}]),
            use_container_width=True
        )

        # ── Temperature range for inspected material ──────────────────────
        st.divider()
        st.markdown('<p class="section-title">// TEMPERATURE SERVICE RANGE</p>', unsafe_allow_html=True)
        st.plotly_chart(make_temp_timeline([m]), use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — COMPONENT SELECTOR (engine schematic + TOPSIS)
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<p class="section-title">// SELECT A COMPONENT — RANKED MATERIALS APPEAR BELOW</p>', unsafe_allow_html=True)

    schematic_svg = """
    <svg viewBox="0 0 900 320" xmlns="http://www.w3.org/2000/svg"
         style="width:100%;background:#0a0f0a;border:1px solid #1a3a1a;border-radius:4px;">

      <defs>
        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#0d1a0d" stroke-width="0.5"/>
        </pattern>
      </defs>
      <rect width="900" height="320" fill="url(#grid)"/>

      <text x="20" y="20" fill="#4a8a5a" font-family="monospace" font-size="10"
            letter-spacing="2">// LIQUID BIPROPELLANT ENGINE — CROSS SECTION</text>

      <!-- PROPELLANT TANK -->
      <rect x="30" y="80" width="100" height="160" rx="8"
            fill="#0d1a0d" stroke="#3b82f6" stroke-width="1.5"/>
      <text x="80" y="155" fill="#3b82f6" font-family="monospace" font-size="9"
            text-anchor="middle">PROPELLANT</text>
      <text x="80" y="168" fill="#3b82f6" font-family="monospace" font-size="9"
            text-anchor="middle">TANK</text>

      <!-- TURBOPUMP -->
      <ellipse cx="210" cy="160" rx="38" ry="50"
               fill="#0d1a0d" stroke="#ef4444" stroke-width="1.5"/>
      <text x="210" y="155" fill="#ef4444" font-family="monospace" font-size="9"
            text-anchor="middle">TURBO</text>
      <text x="210" y="168" fill="#ef4444" font-family="monospace" font-size="9"
            text-anchor="middle">PUMP</text>

      <line x1="130" y1="160" x2="172" y2="160"
            stroke="#4a8a5a" stroke-width="1" stroke-dasharray="4,2"/>

      <!-- GAS GENERATOR -->
      <rect x="268" y="120" width="70" height="80" rx="4"
            fill="#0d1a0d" stroke="#f97316" stroke-width="1.5"/>
      <text x="303" y="155" fill="#f97316" font-family="monospace" font-size="9"
            text-anchor="middle">GAS</text>
      <text x="303" y="168" fill="#f97316" font-family="monospace" font-size="9"
            text-anchor="middle">GEN</text>

      <!-- COMBUSTION CHAMBER -->
      <rect x="380" y="90" width="160" height="140" rx="6"
            fill="#0d1a0d" stroke="#00ff88" stroke-width="2"/>
      <text x="460" y="155" fill="#00ff88" font-family="monospace" font-size="10"
            text-anchor="middle" font-weight="bold">COMBUSTION</text>
      <text x="460" y="170" fill="#00ff88" font-family="monospace" font-size="10"
            text-anchor="middle" font-weight="bold">CHAMBER</text>

      <rect x="380" y="90" width="160" height="12" rx="3"
            fill="none" stroke="#00ff88" stroke-width="0.5" opacity="0.4"/>
      <rect x="380" y="218" width="160" height="12" rx="3"
            fill="none" stroke="#00ff88" stroke-width="0.5" opacity="0.4"/>
      <text x="460" y="103" fill="#4a8a5a" font-family="monospace" font-size="7"
            text-anchor="middle">regen cooling channels</text>

      <!-- THROAT -->
      <path d="M 540 110 L 580 140 L 580 180 L 540 210"
            fill="#0d1a0d" stroke="#14b8a6" stroke-width="2"/>
      <text x="572" y="163" fill="#14b8a6" font-family="monospace" font-size="8"
            text-anchor="middle">THROAT</text>

      <!-- NOZZLE -->
      <path d="M 580 140 L 720 60 M 580 180 L 720 260"
            fill="none" stroke="#8b5cf6" stroke-width="2"/>
      <text x="670" y="165" fill="#8b5cf6" font-family="monospace" font-size="10"
            text-anchor="middle">NOZZLE</text>

      <!-- NOZZLE EXTENSION -->
      <path d="M 720 60 L 870 20 M 720 260 L 870 300"
            fill="none" stroke="#14b8a6" stroke-width="1.5" stroke-dasharray="6,3"/>
      <text x="800" y="175" fill="#14b8a6" font-family="monospace" font-size="9"
            text-anchor="middle">EXTENSION</text>

      <text x="460" y="50" fill="#6b7280" font-family="monospace" font-size="9"
            text-anchor="middle">STRUCTURE / INTERSTAGE</text>
      <line x1="380" y1="54" x2="380" y2="90" stroke="#6b7280"
            stroke-width="0.8" stroke-dasharray="3,2"/>
      <line x1="540" y1="54" x2="540" y2="90" stroke="#6b7280"
            stroke-width="0.8" stroke-dasharray="3,2"/>

      <!-- PRESSURE VESSEL -->
      <ellipse cx="303" cy="80" rx="28" ry="18"
               fill="#0d1a0d" stroke="#a3e635" stroke-width="1.2"/>
      <text x="303" y="84" fill="#a3e635" font-family="monospace" font-size="7"
            text-anchor="middle">PRESS. VESSEL</text>

      <line x1="30" y1="270" x2="870" y2="270" stroke="#1a3a1a" stroke-width="0.5"/>
      <text x="450" y="285" fill="#1a3a1a" font-family="monospace" font-size="8"
            text-anchor="middle">← ENGINE ASSEMBLY →</text>

      <defs>
        <linearGradient id="tempGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stop-color="#3b82f6"/>
          <stop offset="50%" stop-color="#f97316"/>
          <stop offset="100%" stop-color="#ef4444"/>
        </linearGradient>
      </defs>
      <rect x="30" y="295" width="840" height="6" fill="url(#tempGrad)" opacity="0.6"/>
      <text x="30" y="310" fill="#4a8a5a" font-family="monospace" font-size="7">COLD</text>
      <text x="860" y="310" fill="#ef4444" font-family="monospace" font-size="7"
            text-anchor="end">HOT</text>
    </svg>
    """
    import streamlit.components.v1 as components
    components.html(schematic_svg, height=340)

    st.markdown("")
    st.markdown('<p class="section-title">// SELECT COMPONENT</p>', unsafe_allow_html=True)

    component_keys = list(COMPONENT_PRESETS.keys())
    selected_component = st.session_state.get("selected_component", component_keys[0])

    comp_cols = st.columns(4)
    for i, comp in enumerate(component_keys):
        with comp_cols[i % 4]:
            # FIX: same on_click pattern — capture comp in default arg
            st.button(
                comp,
                key=f"comp_{comp.replace(' ', '_').replace('/', '_')}",
                on_click=lambda c=comp: st.session_state.update({"selected_component": c}),
                use_container_width=True,
            )

    # Re-read after possible update
    selected_component = st.session_state.get("selected_component", component_keys[0])
    preset = COMPONENT_PRESETS[selected_component]

    st.markdown(
        f'<p class="section-title">// RANKED MATERIALS FOR: {selected_component.upper()}</p>',
        unsafe_allow_html=True
    )

    with st.expander("Fine-tune priority weights"):
        tw1, tw2, tw3, tw4 = st.columns(4)
        with tw1:
            w_temp         = st.slider("Temp capability", 0.0, 3.0, preset["w_temp"],         0.1, key="tw_temp")
            w_yield        = st.slider("Strength",        0.0, 3.0, preset["w_yield"],        0.1, key="tw_yield")
        with tw2:
            w_conductivity = st.slider("Thermal cond.",   0.0, 3.0, preset["w_conductivity"], 0.1, key="tw_cond")
            w_density      = st.slider("Low mass",        0.0, 3.0, preset["w_density"],      0.1, key="tw_dens")
        with tw3:
            w_oxidation    = st.slider("Oxidation res.",  0.0, 3.0, preset["w_oxidation"],    0.1, key="tw_oxid")
            w_trl          = st.slider("Flight heritage", 0.0, 3.0, preset["w_trl"],          0.1, key="tw_trl")
        with tw4:
            w_cost         = st.slider("Cost",            0.0, 3.0, preset["w_cost"],         0.1, key="tw_cost")

    constraints = {
        "min_service_temp_K": preset["min_service_temp_K"],
        "cryogenic_required": preset["cryogenic_required"],
        "no_hydrogen_risk":   preset["no_hydrogen_risk"],
        "max_cost_index":     preset["max_cost_index"],
        "must_be_weldable":   preset["must_be_weldable"],
        "am_required":        preset["am_required"],
    }
    weights = {
        "w_yield":        w_yield,
        "w_temp":         w_temp,
        "w_conductivity": w_conductivity,
        "w_density":      w_density,
        "w_oxidation":    w_oxidation,
        "w_weldability":  1.0,
        "w_cost":         w_cost,
        "w_trl":          w_trl,
    }

    results = select_materials(selected_component, constraints, weights)

    if results["error"]:
        st.error(results["error"])
    else:
        ranked = results["ranked"]
        r1, r2 = st.columns([3, 2])

        with r1:
            table_data = [{
                "Rank":            r["rank"],
                "Material":        r["material"]["name"],
                "Score":           r["topsis_score"],
                "Yield (MPa)":     r["material"]["yield_strength_MPa"],
                "Max Temp (K)":    r["material"]["max_service_temp_K"],
                "Density (kg/m³)": r["material"]["density_kgm3"],
                "TRL":             r["material"]["trl_propulsion"],
            } for r in ranked]
            st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

            if results["eliminated"]:
                with st.expander(f"Eliminated ({len(results['eliminated'])})"):
                    for mid, reasons in results["eliminated"].items():
                        st.write(f"**{mid}**: {'; '.join(reasons)}")

        with r2:
            fig = go.Figure(go.Bar(
                x=[r["topsis_score"] for r in ranked],
                y=[r["material"]["name"] for r in ranked],
                orientation="h",
                marker_color="#00ff88",
                marker_line_color="#0a0f0a",
                marker_line_width=1,
            ))
            fig.update_layout(
                yaxis=dict(autorange="reversed"),
                height=380,
                margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor="#0a0f0a",
                paper_bgcolor="#0a0f0a",
                font=dict(color="#00ff88", family="monospace"),
                xaxis=dict(gridcolor="#1a3a1a"),
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown('<p class="section-title">// REASONING</p>', unsafe_allow_html=True)
        for reasoning_text in results["reasoning"]:
            st.markdown(reasoning_text)
            st.markdown("---")

        # ── S-N curves — top 3 ranked ─────────────────────────────────────
        st.divider()
        st.markdown('<p class="section-title">// FATIGUE COMPARISON — TOP 3 RANKED</p>', unsafe_allow_html=True)
        st.caption("Approximate S-N curves derived from UTS via Basquin method. "
                   "Endurance limit plateau at 10⁶ cycles.")
        if len(ranked) >= 2:
            st.plotly_chart(make_sn_chart(ranked[:3]), use_container_width=True)

        # ── Temperature timeline — top 3 ──────────────────────────────────
        st.divider()
        st.markdown('<p class="section-title">// TEMPERATURE CAPABILITY — TOP 3</p>', unsafe_allow_html=True)
        show_all_t2 = st.toggle("Show all materials", key="toggle_t2")
        tl_mats = all_mats if show_all_t2 else [r["material"] for r in ranked[:3]]
        st.plotly_chart(make_temp_timeline(tl_mats), use_container_width=True)

        # ── Temperature timeline — all materials ──────────────────────────
        st.divider()
        st.markdown('<p class="section-title">// TEMPERATURE SERVICE RANGE — ALL MATERIALS</p>', unsafe_allow_html=True)
        st.caption("Bar spans min → max service temperature. "
                   "Reference lines mark key propulsion temperatures.")
        show_top3_t3 = st.toggle("Top 3 ranked only", key="toggle_t3")
        if show_top3_t3:
            tl_mats_t3 = [r["material"] for r in ranked[:3]]
        else:
            tl_mats_t3 = all_mats
        st.plotly_chart(make_temp_timeline(tl_mats_t3), use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — ASHBY PLOTS
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<p class="section-title">// ASHBY PLOTS — MATERIAL TRADE-OFF SPACE</p>', unsafe_allow_html=True)

    ashby_data = [{
        "Name":                  m["name"],
        "Category":              CAT_LABEL.get(m["category"], m["category"]),
        "Max Temp (K)":          m["max_service_temp_K"],
        "Thermal Cond (W/mK)":   m["thermal_conductivity_WmK"],
        "Yield Strength (MPa)":  max(m["yield_strength_MPa"], 50),
        "Density (kg/m³)":       m["density_kgm3"],
        "TRL":                   m["trl_propulsion"],
        "Heritage":              ", ".join(m["heritage"][:2]),
    } for m in all_mats]

    df_ashby = pd.DataFrame(ashby_data)

    colour_map = {v: CAT_COLOR.get(k, "#4a8a5a") for k, v in CAT_LABEL.items()}

    # Plot 1 — Conductivity vs Temperature
    st.subheader("Thermal Conductivity vs. Max Service Temperature")
    st.caption("Top-right = best for regeneratively cooled hot sections. Bubble size = yield strength.")

    fig2 = px.scatter(
        df_ashby, x="Max Temp (K)", y="Thermal Cond (W/mK)",
        size="Yield Strength (MPa)", color="Category",
        hover_name="Name",
        hover_data={"Max Temp (K)": True, "Thermal Cond (W/mK)": True,
                    "Yield Strength (MPa)": True, "Density (kg/m³)": True,
                    "TRL": True, "Heritage": True, "Category": False},
        color_discrete_map=colour_map, size_max=50, height=520,
    )
    fig2.add_annotation(x=750,  y=310, text="🔥 Regen cooling sweet spot",
                        showarrow=False, font=dict(size=10, color="#f97316"),
                        bgcolor="rgba(10,15,10,0.8)", bordercolor="#f97316", borderwidth=1)
    fig2.add_annotation(x=1700, y=55,  text="🌡 Extreme temp / refractory zone",
                        showarrow=False, font=dict(size=10, color="#14b8a6"),
                        bgcolor="rgba(10,15,10,0.8)", bordercolor="#14b8a6", borderwidth=1)
    fig2.update_layout(
        plot_bgcolor="#0a0f0a", paper_bgcolor="#0a0f0a",
        font=dict(color="#00ff88", family="monospace"),
        xaxis=dict(title="Max Service Temperature (K)", gridcolor="#1a3a1a"),
        yaxis=dict(title="Thermal Conductivity (W/mK)", gridcolor="#1a3a1a"),
        legend=dict(bgcolor="rgba(10,15,10,0.8)", bordercolor="#1a3a1a"),
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # Plot 2 — Yield vs Density
    st.subheader("Yield Strength vs. Density (Specific Strength)")
    st.caption("Top-left = highest specific strength. Bubble size = max service temperature.")

    fig3 = px.scatter(
        df_ashby, x="Density (kg/m³)", y="Yield Strength (MPa)",
        size="Max Temp (K)", color="Category",
        hover_name="Name",
        hover_data={"Density (kg/m³)": True, "Yield Strength (MPa)": True,
                    "Max Temp (K)": True, "TRL": True, "Heritage": True, "Category": False},
        color_discrete_map=colour_map, size_max=50, height=500,
    )
    fig3.update_layout(
        plot_bgcolor="#0a0f0a", paper_bgcolor="#0a0f0a",
        font=dict(color="#00ff88", family="monospace"),
        xaxis=dict(title="Density (kg/m³) — lower is better", gridcolor="#1a3a1a"),
        yaxis=dict(title="Yield Strength (MPa) — higher is better", gridcolor="#1a3a1a"),
        legend=dict(bgcolor="rgba(10,15,10,0.8)", bordercolor="#1a3a1a"),
    )
    st.plotly_chart(fig3, use_container_width=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    f'<p style="color:#1a3a1a;font-family:monospace;font-size:0.7rem;">'
    f'// {len(all_mats)} materials · cited sources · NASA TRs · AMS specs · manufacturer datasheets'
    f'</p>', unsafe_allow_html=True
)
