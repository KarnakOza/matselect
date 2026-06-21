"""
MatSelect — Materials Database for Propulsion Hardware
Real measured properties from published sources.
Every number is defensible and cited.
"""

MATERIALS = [
    {
        "id": "IN718",
        "name": "Inconel 718",
        "category": "nickel_superalloy",

        # Mechanical properties at room temp
        "yield_strength_MPa": 1100,
        "ultimate_strength_MPa": 1375,
        "elongation_pct": 12,
        "hardness_HV": 390,

        # High temperature performance
        "max_service_temp_K": 923,       # ~650°C continuous
        "melting_point_K": 1609,
        "creep_rupture_temp_K": 923,     # temp at which creep becomes critical

        # Thermal properties
        "thermal_conductivity_Wm K": 11.4,
        "thermal_expansion_1e6_K": 13.0,
        "specific_heat_J_kgK": 435,

        # Physical
        "density_kgm3": 8190,

        # Weldability & manufacturing
        "weldability": 3,               # 1=excellent, 5=very difficult
        "machinability": 2,             # 1=easy, 5=very hard
        "AM_compatible": True,          # additive manufacturing

        # Propulsion relevance
        "oxidation_resistance": 4,      # 1=poor, 5=excellent
        "cryogenic_compatible": False,
        "hydrogen_embrittlement_risk": True,
        "cost_index": 4,                # 1=cheap, 5=expensive
        "trl_propulsion": 9,

        # Where it's actually used
        "heritage": [
            "Merlin turbopump", "RL-10 turbopump", "F-1 turbopump",
            "RD-180 turbopump", "most modern turbopump discs and shafts"
        ],
        "typical_components": [
            "turbopump discs", "shafts", "impellers",
            "combustion chamber cases", "injector bodies"
        ],

        "source": "AMS 5664; NASA-TM-2013-217454; Aerospace Structural Metals Handbook"
    },
    {
        "id": "GRCOP42",
        "name": "GRCop-42 (Cu-Cr-Nb)",
        "category": "copper_alloy",

        "yield_strength_MPa": 255,
        "ultimate_strength_MPa": 310,
        "elongation_pct": 28,
        "hardness_HV": 90,

        "max_service_temp_K": 773,
        "melting_point_K": 1338,
        "creep_rupture_temp_K": 773,

        # Key advantage — highest thermal conductivity of any propulsion alloy
        "thermal_conductivity_Wm K": 320,
        "thermal_expansion_1e6_K": 17.0,
        "specific_heat_J_kgK": 386,

        "density_kgm3": 8900,

        "weldability": 3,
        "machinability": 3,
        "AM_compatible": True,          # developed for SLM at NASA GRC

        "oxidation_resistance": 2,
        "cryogenic_compatible": True,
        "hydrogen_embrittlement_risk": False,
        "cost_index": 4,
        "trl_propulsion": 7,

        "heritage": [
            "RS-25 chamber liner", "NASA SLM development program",
            "Vulcain chamber liner concept"
        ],
        "typical_components": [
            "combustion chamber liners",
            "regenerative cooling channel walls",
            "throat inserts"
        ],

        "source": "NASA TM-2017-219439; NASA GRC GRCop-42 development program"
    },
    {
        "id": "TI6AL4V",
        "name": "Ti-6Al-4V",
        "category": "titanium_alloy",

        "yield_strength_MPa": 880,
        "ultimate_strength_MPa": 950,
        "elongation_pct": 14,
        "hardness_HV": 320,

        "max_service_temp_K": 573,       # ~300°C limit
        "melting_point_K": 1933,
        "creep_rupture_temp_K": 573,

        "thermal_conductivity_Wm K": 6.7,
        "thermal_expansion_1e6_K": 8.6,
        "specific_heat_J_kgK": 526,

        "density_kgm3": 4430,            # Key advantage — lowest density here

        "weldability": 2,
        "machinability": 3,
        "AM_compatible": True,

        "oxidation_resistance": 3,
        "cryogenic_compatible": True,
        "hydrogen_embrittlement_risk": True,
        "cost_index": 3,
        "trl_propulsion": 9,

        "heritage": [
            "Saturn V propellant lines", "Space Shuttle propellant ducting",
            "most spacecraft propellant tanks", "pressure vessels"
        ],
        "typical_components": [
            "propellant tanks", "pressure vessels",
            "structural brackets", "feed lines", "valve bodies"
        ],

        "source": "AMS 4928; MIL-T-9046; NASA-STD-6008"
    },
    {
        "id": "SS304L",
        "name": "304L Stainless Steel",
        "category": "stainless_steel",

        "yield_strength_MPa": 170,
        "ultimate_strength_MPa": 485,
        "elongation_pct": 40,
        "hardness_HV": 160,

        "max_service_temp_K": 1173,
        "melting_point_K": 1723,
        "creep_rupture_temp_K": 873,

        "thermal_conductivity_Wm K": 16.2,
        "thermal_expansion_1e6_K": 17.2,
        "specific_heat_J_kgK": 500,

        "density_kgm3": 7900,

        "weldability": 1,               # Excellent — L grade minimises sensitisation
        "machinability": 2,
        "AM_compatible": True,

        "oxidation_resistance": 3,
        "cryogenic_compatible": True,   # Key use case — LOX/LH2 compatible
        "hydrogen_embrittlement_risk": False,
        "cost_index": 1,
        "trl_propulsion": 9,

        "heritage": [
            "propellant feed lines", "LOX/LH2 tankage",
            "cryogenic plumbing", "test stand hardware"
        ],
        "typical_components": [
            "cryogenic propellant lines", "low-pressure tankage",
            "test hardware", "support structures"
        ],

        "source": "ASTM A240; NASA-HDBK-6001; Cryogenic Materials Data Handbook"
    },
    {
        "id": "HAYNES230",
        "name": "Haynes 230",
        "category": "nickel_superalloy",

        "yield_strength_MPa": 390,
        "ultimate_strength_MPa": 870,
        "elongation_pct": 48,
        "hardness_HV": 200,

        "max_service_temp_K": 1173,      # ~900°C — highest here
        "melting_point_K": 1644,
        "creep_rupture_temp_K": 1073,

        "thermal_conductivity_Wm K": 8.9,
        "thermal_expansion_1e6_K": 12.7,
        "specific_heat_J_kgK": 397,

        "density_kgm3": 8970,

        "weldability": 2,
        "machinability": 3,
        "AM_compatible": False,

        "oxidation_resistance": 5,      # Best oxidation resistance in this DB
        "cryogenic_compatible": False,
        "hydrogen_embrittlement_risk": False,
        "cost_index": 5,
        "trl_propulsion": 8,

        "heritage": [
            "RS-25 nozzle", "RL-10 nozzle", "combustion chamber hot sections",
            "gas generator components"
        ],
        "typical_components": [
            "nozzle sections", "hot gas manifolds",
            "combustion chamber hot walls", "gas generator liners"
        ],

        "source": "Haynes International H-3170C; NASA-TM-2000-209941"
    },
    {
        "id": "AL2024T3",
        "name": "Aluminium 2024-T3",
        "category": "aluminium_alloy",

        "yield_strength_MPa": 345,
        "ultimate_strength_MPa": 483,
        "elongation_pct": 18,
        "hardness_HV": 130,

        "max_service_temp_K": 423,       # ~150°C — significant limitation
        "melting_point_K": 911,
        "creep_rupture_temp_K": 373,

        "thermal_conductivity_Wm K": 121,
        "thermal_expansion_1e6_K": 23.2,
        "specific_heat_J_kgK": 875,

        "density_kgm3": 2780,            # Lowest density — structural advantage

        "weldability": 4,               # Poor — hot cracking risk
        "machinability": 1,             # Excellent
        "AM_compatible": False,

        "oxidation_resistance": 2,
        "cryogenic_compatible": True,
        "hydrogen_embrittlement_risk": False,
        "cost_index": 1,
        "trl_propulsion": 9,

        "heritage": [
            "Saturn V structure", "Space Shuttle ET stringers",
            "Falcon 9 interstage", "most launch vehicle structures"
        ],
        "typical_components": [
            "structural frames", "interstages",
            "low-pressure tankage walls", "fairing structures"
        ],

        "source": "MIL-HDBK-5J; AMS 2770; NASA-TM-1999-209260"
    },
    {
        "id": "CFRP_IM7",
        "name": "CFRP (IM7/977-3)",
        "category": "composite",

        "yield_strength_MPa": 0,         # composites don't yield — use UTS
        "ultimate_strength_MPa": 2800,   # fibre direction
        "elongation_pct": 1.5,
        "hardness_HV": None,

        "max_service_temp_K": 423,
        "melting_point_K": None,
        "creep_rupture_temp_K": 373,

        "thermal_conductivity_Wm K": 5.0,
        "thermal_expansion_1e6_K": 0.5,  # Near-zero CTE — dimensional stability
        "specific_heat_J_kgK": 900,

        "density_kgm3": 1550,            # Lowest density with highest strength

        "weldability": 5,               # Cannot be welded
        "machinability": 4,             # Abrasive — tool wear
        "AM_compatible": False,

        "oxidation_resistance": 2,
        "cryogenic_compatible": True,
        "hydrogen_embrittlement_risk": False,
        "cost_index": 4,
        "trl_propulsion": 8,

        "heritage": [
            "Falcon 9 payload fairing", "Ariane 5 fairing",
            "pressure vessels (COPV)", "nozzle exit cones"
        ],
        "typical_components": [
            "payload fairings", "interstages",
            "nozzle exit cones", "COPV overwrap", "skirts"
        ],

        "source": "Hexcel IM7 datasheet; NASA-CR-2004-213256"
    },
    {
        "id": "C103_NB",
        "name": "C-103 (Nb-Hf-Ti)",
        "category": "refractory_alloy",

        "yield_strength_MPa": 345,
        "ultimate_strength_MPa": 415,
        "elongation_pct": 25,
        "hardness_HV": 150,

        "max_service_temp_K": 1644,      # ~1370°C — highest service temp here
        "melting_point_K": 2741,
        "creep_rupture_temp_K": 1533,

        "thermal_conductivity_Wm K": 52,
        "thermal_expansion_1e6_K": 7.1,
        "specific_heat_J_kgK": 272,

        "density_kgm3": 8850,

        "weldability": 2,
        "machinability": 3,
        "AM_compatible": False,

        "oxidation_resistance": 2,       # Needs coating above 400°C
        "cryogenic_compatible": False,
        "hydrogen_embrittlement_risk": False,
        "cost_index": 5,
        "trl_propulsion": 8,

        "heritage": [
            "Apollo LM descent engine nozzle",
            "Hydrazine thruster nozzles (standard)",
            "attitude control thruster nozzles"
        ],
        "typical_components": [
            "thruster nozzles", "attitude control nozzles",
            "high-temperature nozzle extensions"
        ],

        "source": "Wah Chang C-103 datasheet; NASA-TM-X-2076"
    }
]


# --- Query helpers ---

def get_all():
    return MATERIALS

def get_by_id(material_id):
    for m in MATERIALS:
        if m["id"] == material_id:
            return m
    return None

def get_by_category(category):
    return [m for m in MATERIALS if m["category"] == category]

def get_cryogenic_compatible():
    return [m for m in MATERIALS if m["cryogenic_compatible"]]

def get_by_max_temp(min_temp_K):
    """Return materials that survive at least min_temp_K"""
    return [m for m in MATERIALS if m["max_service_temp_K"] >= min_temp_K]


if __name__ == "__main__":
    print(f"MatSelect database: {len(MATERIALS)} materials loaded\n")
    print(f"{'Name':<25} {'Category':<20} {'Yield MPa':<12} {'Max Temp K':<12} {'TRL'}")
    print("-" * 80)
    for m in MATERIALS:
        print(f"{m['name']:<25} {m['category']:<20} "
              f"{m['yield_strength_MPa']:<12} {m['max_service_temp_K']:<12} "
              f"{m['trl_propulsion']}")