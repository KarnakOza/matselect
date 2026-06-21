"""
MatSelect — TOPSIS Scoring Engine
Ranks materials for a given propulsion component and operating conditions.

TOPSIS = Technique for Order of Preference by Similarity to Ideal Solution
- Filter by hard constraints first (temperature, compatibility)
- Score survivors by distance from ideal and anti-ideal solution
- Return ranked list with scores and plain-English reasoning
"""

import math
from engine.database import get_all


# --- Hard constraint filter ---

def apply_constraints(materials, constraints):
    """
    Remove materials that fail any hard constraint.
    constraints is a dict with optional keys:
        min_service_temp_K   : float
        cryogenic_required   : bool
        no_hydrogen_risk     : bool
        max_cost_index       : int (1-5)
        must_be_weldable     : bool  (weldability <= 2)
        am_required          : bool
    Returns filtered list and a dict of why each was eliminated.
    """
    passed = []
    eliminated = {}

    for m in materials:
        reasons = []

        if "min_service_temp_K" in constraints:
            if m["max_service_temp_K"] < constraints["min_service_temp_K"]:
                reasons.append(
                    f"max service temp {m['max_service_temp_K']}K "
                    f"< required {constraints['min_service_temp_K']}K"
                )

        if constraints.get("cryogenic_required"):
            if not m["cryogenic_compatible"]:
                reasons.append("not cryogenic compatible")

        if constraints.get("no_hydrogen_risk"):
            if m["hydrogen_embrittlement_risk"]:
                reasons.append("hydrogen embrittlement risk")

        if "max_cost_index" in constraints:
            if m["cost_index"] > constraints["max_cost_index"]:
                reasons.append(
                    f"cost index {m['cost_index']} "
                    f"> max allowed {constraints['max_cost_index']}"
                )

        if constraints.get("must_be_weldable"):
            if m["weldability"] > 2:
                reasons.append(f"weldability score {m['weldability']} > 2")

        if constraints.get("am_required"):
            if not m["AM_compatible"]:
                reasons.append("not AM compatible")

        if reasons:
            eliminated[m["id"]] = reasons
        else:
            passed.append(m)

    return passed, eliminated


# --- TOPSIS core ---

def run_topsis(materials, weights):
    """
    Run TOPSIS on a list of materials with given criteria weights.

    weights is a dict:
        w_yield         : weight for yield strength (benefit)
        w_temp          : weight for max service temperature (benefit)
        w_conductivity  : weight for thermal conductivity (benefit — for cooling)
        w_density       : weight for density (cost — lower is better for structures)
        w_oxidation     : weight for oxidation resistance (benefit)
        w_weldability   : weight for weldability (cost — lower score = better)
        w_cost          : weight for cost index (cost — lower is better)
        w_trl           : weight for TRL (benefit)

    Returns list of dicts sorted by TOPSIS score descending.
    """

    if len(materials) == 0:
        return []

    if len(materials) == 1:
        return [{
            "material": materials[0],
            "topsis_score": 1.0,
            "rank": 1
        }]

    # Define criteria: (key, benefit_or_cost)
    # benefit = higher is better, cost = lower is better
    criteria = [
        ("yield_strength_MPa",       "benefit", weights.get("w_yield", 1.0)),
        ("max_service_temp_K",        "benefit", weights.get("w_temp", 1.0)),
        ("thermal_conductivity_Wm K", "benefit", weights.get("w_conductivity", 1.0)),
        ("density_kgm3",              "cost",    weights.get("w_density", 1.0)),
        ("oxidation_resistance",      "benefit", weights.get("w_oxidation", 1.0)),
        ("weldability",               "cost",    weights.get("w_weldability", 1.0)),
        ("cost_index",                "cost",    weights.get("w_cost", 1.0)),
        ("trl_propulsion",            "benefit", weights.get("w_trl", 1.0)),
    ]

    # Build decision matrix — handle None values with 0
    matrix = []
    for m in materials:
        row = []
        for key, _, _ in criteria:
            val = m.get(key)
            row.append(float(val) if val is not None else 0.0)
        matrix.append(row)

    n = len(materials)
    c = len(criteria)

    # Step 1: Normalise using vector normalisation
    norm_matrix = [[0.0] * c for _ in range(n)]
    for j in range(c):
        col_sq_sum = sum(matrix[i][j] ** 2 for i in range(n))
        denom = math.sqrt(col_sq_sum) if col_sq_sum > 0 else 1.0
        for i in range(n):
            norm_matrix[i][j] = matrix[i][j] / denom

    # Step 2: Apply weights
    weighted = [[0.0] * c for _ in range(n)]
    for i in range(n):
        for j in range(c):
            weighted[i][j] = norm_matrix[i][j] * criteria[j][2]

    # Step 3: Ideal best and worst
    ideal_best = []
    ideal_worst = []
    for j in range(c):
        col = [weighted[i][j] for i in range(n)]
        if criteria[j][1] == "benefit":
            ideal_best.append(max(col))
            ideal_worst.append(min(col))
        else:
            ideal_best.append(min(col))
            ideal_worst.append(max(col))

    # Step 4: Distance to ideal best and worst
    dist_best = []
    dist_worst = []
    for i in range(n):
        db = math.sqrt(sum((weighted[i][j] - ideal_best[j]) ** 2 for j in range(c)))
        dw = math.sqrt(sum((weighted[i][j] - ideal_worst[j]) ** 2 for j in range(c)))
        dist_best.append(db)
        dist_worst.append(dw)

    # Step 5: TOPSIS score
    scores = []
    for i in range(n):
        denom = dist_best[i] + dist_worst[i]
        score = dist_worst[i] / denom if denom > 0 else 0.0
        scores.append(score)

    # Sort by score descending
    ranked = sorted(
        zip(scores, materials),
        key=lambda x: x[0],
        reverse=True
    )

    results = []
    for rank, (score, mat) in enumerate(ranked, start=1):
        results.append({
            "rank": rank,
            "material": mat,
            "topsis_score": round(score, 4)
        })

    return results


# --- Reasoning generator ---

def generate_reasoning(result, constraints, weights, eliminated):
    """
    Generate a plain-English paragraph explaining why a material
    ranked where it did.
    """
    m = result["material"]
    rank = result["rank"]
    score = result["topsis_score"]
    lines = []

    lines.append(f"**#{rank} — {m['name']}** (Score: {score:.3f})")
    lines.append("")

    # Strengths
    strengths = []
    if m["max_service_temp_K"] >= constraints.get("min_service_temp_K", 0) + 200:
        strengths.append(
            f"excellent temperature margin "
            f"(rated to {m['max_service_temp_K']}K)"
        )
    if m["yield_strength_MPa"] > 600:
        strengths.append(
            f"high yield strength ({m['yield_strength_MPa']} MPa)"
        )
    if m["thermal_conductivity_Wm K"] > 100:
        strengths.append(
            f"very high thermal conductivity "
            f"({m['thermal_conductivity_Wm K']} W/mK) — "
            f"effective for regenerative cooling"
        )
    if m["oxidation_resistance"] >= 4:
        strengths.append("strong oxidation resistance in hot gas environments")
    if m["trl_propulsion"] == 9:
        strengths.append(f"TRL 9 with heritage in {', '.join(m['heritage'][:2])}")
    if m["AM_compatible"]:
        strengths.append("qualified for additive manufacturing")
    if m["cryogenic_compatible"]:
        strengths.append("cryogenic compatible")

    # Weaknesses
    weaknesses = []
    if m["cost_index"] >= 4:
        weaknesses.append("high material cost")
    if m["weldability"] >= 4:
        weaknesses.append("difficult to weld — requires specialist procedures")
    if m["hydrogen_embrittlement_risk"]:
        weaknesses.append("hydrogen embrittlement risk — avoid LH2 contact")
    if m["density_kgm3"] > 8000:
        weaknesses.append(f"high density ({m['density_kgm3']} kg/m³) — mass penalty")
    if m["trl_propulsion"] <= 7:
        weaknesses.append(f"TRL {m['trl_propulsion']} — not yet fully flight qualified")

    if strengths:
        lines.append("**Why it ranked here:** " + "; ".join(strengths) + ".")
    if weaknesses:
        lines.append("**Watch out for:** " + "; ".join(weaknesses) + ".")

    lines.append(
        f"**Typical use:** {', '.join(m['typical_components'][:3])}."
    )
    lines.append(f"*Source: {m['source']}*")

    return "\n".join(lines)


# --- Main selection function ---

def select_materials(component, constraints, weights):
    """
    Full selection pipeline.
    Returns dict with ranked results, eliminated materials, and reasoning.

    component: str description e.g. "combustion chamber liner"
    constraints: dict — hard filters
    weights: dict — TOPSIS criteria weights
    """
    all_materials = get_all()

    # Hard filter
    candidates, eliminated = apply_constraints(all_materials, constraints)

    if len(candidates) == 0:
        return {
            "component": component,
            "candidates": [],
            "eliminated": eliminated,
            "reasoning": [],
            "error": "No materials passed the hard constraints. "
                     "Try relaxing temperature, cost, or compatibility requirements."
        }

    # TOPSIS ranking
    ranked = run_topsis(candidates, weights)

    # Generate reasoning for top 3
    reasoning = []
    for result in ranked[:3]:
        reasoning.append(
            generate_reasoning(result, constraints, weights, eliminated)
        )

    return {
        "component": component,
        "ranked": ranked,
        "eliminated": eliminated,
        "reasoning": reasoning,
        "error": None
    }


# --- Quick test ---

if __name__ == "__main__":
    print("MatSelect TOPSIS Engine — Test Run")
    print("Component: Combustion Chamber Liner")
    print("=" * 60)

    constraints = {
        "min_service_temp_K": 700,
        "cryogenic_required": False,
        "no_hydrogen_risk": False,
        "max_cost_index": 5,
        "must_be_weldable": False,
        "am_required": False,
    }

    weights = {
        "w_yield": 1.0,
        "w_temp": 2.0,          # temperature is critical for chamber
        "w_conductivity": 2.5,  # thermal conductivity critical for regen cooling
        "w_density": 0.5,
        "w_oxidation": 2.0,
        "w_weldability": 1.0,
        "w_cost": 0.5,
        "w_trl": 1.5,
    }

    results = select_materials("combustion chamber liner", constraints, weights)

    if results["error"]:
        print(results["error"])
    else:
        print(f"\nEliminated ({len(results['eliminated'])}):")
        for mid, reasons in results["eliminated"].items():
            print(f"  {mid}: {'; '.join(reasons)}")

        print(f"\nRanked Results ({len(results['ranked'])}):")
        for r in results["ranked"]:
            print(f"  #{r['rank']} {r['material']['name']:<25} "
                  f"score={r['topsis_score']:.4f}")

        print("\nTop 3 Reasoning:")
        print("-" * 60)
        for r in results["reasoning"]:
            print(r)
            print()