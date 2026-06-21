# MatSelect

**Materials selection for propulsion hardware — grounded in real measured data, not theoretical predictions.**

Engineers selecting structural materials for rocket propulsion hardware balance strength, temperature capability, thermal conductivity, weldability, manufacturability, and flight heritage — usually in a spreadsheet, ad hoc, at the start of a program. MatSelect formalises that trade study into an interactive tool.

[https://matselect.streamlit.app/]

## What it does

1. You describe a component (combustion chamber liner, turbopump shaft, propellant tank, etc.) and its operating conditions
2. You set hard constraints (minimum temperature, cryogenic compatibility, hydrogen embrittlement avoidance, cost ceiling)
3. You weight what matters most (strength vs. thermal conductivity vs. flight heritage vs. cost)
4. MatSelect filters the materials database by your hard constraints, then ranks survivors using **TOPSIS** (Technique for Order of Preference by Similarity to Ideal Solution)
5. You get a ranked table, a score comparison chart, and a plain-English explanation of why each top candidate ranked where it did

## Why this matters

Every number in the database is sourced from a real published reference — NASA technical reports, AMS material specifications, manufacturer datasheets — not from theoretical prediction or simulation. When the tool says GRCop-42 is the top choice for a combustion chamber liner, that conclusion is traceable to NASA TM-2017-219439 and matches why NASA actually selected it for the RS-25 chamber liner program.

## Architecture

```
matselect/
├── engine/
│   ├── database.py    # 8 materials, real measured properties, cited sources
│   └── topsis.py       # constraint filtering + TOPSIS multi-criteria ranking
├── app/
│   └── dashboard.py     # Streamlit front end
├── requirements.txt
└── README.md
```

## Running locally

```bash
git clone https://github.com/KarnakOza/matselect.git
cd matselect
pip install -r requirements.txt
streamlit run app/dashboard.py
```

## The scoring method

MatSelect uses **TOPSIS**, a multi-criteria decision analysis method. Each material is scored on 8 criteria (yield strength, max service temperature, thermal conductivity, density, oxidation resistance, weldability, cost, TRL), normalised, weighted by user-set priorities, and ranked by distance from an ideal and anti-ideal solution. This is the same class of method used in real engineering trade studies — not a black-box score.

## Current database (v1)

8 materials covering the core propulsion hardware design space: Inconel 718, GRCop-42, Ti-6Al-4V, 304L Stainless Steel, Haynes 230, Aluminium 2024-T3, CFRP (IM7/977-3), C-103 niobium alloy.

Expansion to 20+ materials is in progress — see `engine/database.py` for the structure and contribute additional cited entries via pull request.

## Roadmap

- [ ] Expand database to 20+ materials
- [ ] PDF export of trade study results
- [ ] Add weld HAZ compatibility scoring between dissimilar materials
- [ ] Docker deployment

## License

MIT
