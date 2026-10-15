# Mid-Day Meal Nutrition + Wastage Tracker (PM POSHAN)
### Soft Computing Capstone Project & State/Block School Monitoring Portal

---

## 📌 Executive Summary & Context

Under India's **PM POSHAN (Pradhan Mantri Poshan Shakti Nirman)** scheme—formerly the National Mid-Day Meal Scheme—government and government-aided schools provide daily hot cooked lunches to over **120 million schoolchildren** across Primary (Classes I–V) and Upper Primary (Classes VI–VIII) levels.

While the scheme specifies strict statutory nutritional benchmarks (e.g., 450 kcal & 12g protein for Primary; 700 kcal & 20g protein for Upper Primary), ground-level monitoring often encounters severe data latency:
- Record-keeping is frequently restricted to monthly paper registers or aggregated attendance counts.
- Daily nutrition density actually delivered to students is rarely cross-calculated against verified food composition standards.
- Food wastage is unmeasured, lumping together over-preparation in kitchen cauldrons (*kitchen leftovers*) and uneaten food rejected by children (*plate waste*).
- Paper-based or sporadic reporting conceals missing entries, which are mistakenly treated as zero waste or assumed compliance.

The **Mid-Day Meal Nutrition + Wastage Tracker** is a modular, mobile-first web application designed for school headmasters, cluster monitors, and district education officers. It unites a rule-based **ICMR-NIN nutritional composition engine**, an empirical **food wastage tracker**, and a **Soft Computing Mamdani Fuzzy Inference System (FIS)** that flags meal sessions requiring administrative review.

---

## 🔍 Market Review & Identified Gap

> [!IMPORTANT]
> **Market Review of Existing Systems:**
> We reviewed current government and commercial solutions across the midday meal and institutional kitchen sector:
>
> 1. **PM POSHAN Official National Portal & Automated Monitoring System (AMS / IVRS):**
>    - *Features:* Collects daily headcounts of meals served via SMS/IVRS from headmasters; tracks grain lifting and fund allocation.
>    - *Limitations:* Captures only binary headcounts (*"Were meals served? Yes/No, and how many"*). Does not calculate daily micronutrient/protein adequacy from actual recipes, does not quantify cooked food wastage, and does not separate kitchen leftovers from plate waste.
> 2. **Commercial AI Food Waste Trackers (e.g., Winnow, Leanpath, Orbisk):**
>    - *Features:* Camera-enabled computerized scales in commercial hotel/hospital kitchens.
>    - *Limitations:* Cost-prohibitive for rural public primary schools; requires high-end hardware, continuous high-speed electricity, and specialized cameras.
>    - *Limitations:* Tailored for commercial buffets, not aligned with Indian ICMR-NIN food composition tables or statutory PM POSHAN ration entitlements.
> 3. **Consumer Diet & Calorie Trackers (e.g., MyFitnessPal, HealthifyMe):**
>    - *Features:* Tracks individual meals against generic adult dietary goals.
>    - *Limitations:* Designed for single-user adult weight management, completely lacking institutional batch cooking conversion (e.g., raw-to-cooked yield factors for 100+ children), block-level aggregation, or school compliance audits.
>
> **The Identified Market Gap:**
> There exists a distinct need for a **lightweight, zero-cost, mobile-first software tool** that bridges institutional kitchen inventory, statutory ICMR-NIN nutritional verification, multi-method waste tracking (manual scales + visual quarter-waste estimates), and Soft Computing priority intelligence without requiring expensive camera hardware or proprietary paid APIs.

---

## 🏗️ Architecture & File Structure

The project is structured according to clean separation of concerns:

```
project/
├── app.py                      # Main Streamlit web application & sidebar router
├── config.py                   # Central constants, PM POSHAN standards, fuzzy bounds
├── pytest.ini                  # Pytest configuration & warning suppression
├── requirements.txt            # Python dependencies (Streamlit, Plotly, scikit-fuzzy, pytest)
├── poshan_tracker.db           # SQLite persistent relational database
├── database/
│   ├── __init__.py
│   ├── db.py                   # SQLite schema, CRUD operations, duplicate constraint, compliance
│   └── seed_data.py            # Synthetic simulation data generator (6 schools, 12 working days)
├── engines/
│   ├── __init__.py
│   ├── nutrition_engine.py     # ICMR-NIN IFCT 2017 nutrient database, raw/cooked yield math
│   ├── wastage_engine.py       # Food waste computation, visual quarter-plate mapping, validation
│   └── fuzzy_engine.py         # Mamdani Fuzzy Inference System (scikit-fuzzy + Centroid COG)
├── views/
│   ├── __init__.py
│   ├── dashboard.py            # KPI cards, Plotly charts (adequacy trends, waste breakdown, risk matrix)
│   ├── daily_entry.py          # Mobile-first daily meal log with live preview & duplicate checks
│   ├── fuzzy_analysis.py       # Soft computing simulator, membership curves, rule explainability
│   ├── reports.py              # Block/School aggregator, compliance matrix, CSV data exports
│   └── reference_norms.py      # PM POSHAN target editor, ICMR table, scientific assumptions
└── tests/
    ├── __init__.py
    ├── test_nutrition.py       # Unit tests: nutrient lookup, raw/cooked yield, boundary validation
    ├── test_wastage.py         # Unit tests: waste metrics, visual converter, physical sanity rules
    ├── test_fuzzy.py           # Unit tests: Mamdani FIS, 9 IF-THEN rules, defuzzification, boundaries
    └── test_integration.py     # Integration tests: end-to-end lifecycle, duplicate prevention
```

---

## 🧮 Core Calculations & Engine Design

### 1. Nutrition Calculation Engine (`engines/nutrition_engine.py`)

- **Data Origin:** Directly sourced from the *Indian Food Composition Tables (IFCT)* published by the **National Institute of Nutrition (ICMR-NIN), Hyderabad**.
- **Raw vs. Cooked Standardization:** In school storehouses, grains and pulses are weighed raw (dry weight) before cooking. Calorie and protein values are derived from raw dry matter.
- **Cooked Hydration Yield Factors:**
  - Raw Milled Rice $\rightarrow 2.8\times$ (100g raw yields ~280g cooked).
  - Whole Wheat Atta $\rightarrow 1.4\times$ (kneaded chapatis).
  - Pulses/Dal $\rightarrow 3.0\times$ to $3.2\times$ (water absorption during boiling).
  - If a user inputs cooked quantities, the engine adjusts weight using:
    $$\text{Effective Raw Grams} = \frac{\text{Cooked Grams}}{\text{Cooked Yield Factor}}$$
- **Per-Student Serving Equations:**
  $$\text{Energy Per Serving (kcal)} = \frac{\sum_{i=1}^n \text{Calories}_i}{\text{Meals Served}}$$
  $$\text{Protein Per Serving (g)} = \frac{\sum_{i=1}^n \text{Protein}_i}{\text{Meals Served}}$$
  $$\text{Energy Adequacy \%} = \left(\frac{\text{Energy Per Serving}}{\text{Target Energy}}\right) \times 100$$
  $$\text{Protein Adequacy \%} = \left(\frac{\text{Protein Per Serving}}{\text{Target Protein}}\right) \times 100$$
  $$\text{Combined Adequacy \%} = \frac{\text{Energy Adequacy \%} + \text{Protein Adequacy \%}}{2}$$

---

### 2. Food Wastage Engine (`engines/wastage_engine.py`)

Distinguishes between production waste (cooking pots) and consumption waste (children's plates):
- **Kitchen Leftovers ($W_{\text{kitchen}}$):** Edible cooked food remaining in pots/vessels due to over-preparation.
- **Plate Waste ($W_{\text{plate}}$):** Food served on plates but left uneaten and discarded.
- **Total Waste ($W_{\text{total}}$):**
  $$W_{\text{total}} = W_{\text{kitchen}} + W_{\text{plate}}$$
  $$\text{Total Wastage \%} = \left(\frac{W_{\text{total}}}{\text{Total Cooked Food Prepared (kg)}}\right) \times 100$$
  $$\text{Plate Waste Per Child (g)} = \frac{W_{\text{plate}} \times 1000}{\text{Meals Served}}$$

- **Visual Quarter-Plate Estimation Method:**
  Recognizing that rural cooks may lack kitchen scales every single day, the engine supports a validated visual estimation protocol:
  - *No visible waste (< 2%):* $0.01 \times \text{Distributed Food}$
  - *Slight leftovers (~5%):* $0.05 \times \text{Distributed Food}$
  - *Quarter plate remaining (~25%):* $0.25 \times \text{Distributed Food}$
  - *Half plate remaining (~50%):* $0.50 \times \text{Distributed Food}$
  - *Substantial plate waste (> 75%):* $0.75 \times \text{Distributed Food}$

- **Physical Consistency Validation Rules:**
  The engine throws `WasteValidationError` and blocks storage if:
  1. $\text{Meals Served} > \text{Students Present}$ (impossible to serve more meals than children present).
  2. $W_{\text{total}} > \text{Food Prepared}$ (waste cannot exceed prepared food).
  3. $W_{\text{kitchen}} > \text{Food Prepared}$.
  4. $W_{\text{plate}} > (\text{Food Prepared} - W_{\text{kitchen}})$ (plate waste cannot exceed food distributed).
  5. Any negative quantity entered.

---

### 3. Soft Computing: Mamdani Fuzzy Inference System (`engines/fuzzy_engine.py`)

The Fuzzy Logic module provides an explainable decision-support score ($Z^* \in [0, 100]$) to triage schools needing inspection.

#### Universes of Discourse & Membership Functions
1. **Input 1: Nutrition Adequacy ($x_1 \in [0, 150]\%$)**
   - $\text{Low} \in [0, 0, 45, 75]$ (Trapezoidal)
   - $\text{Medium} \in [60, 85, 110]$ (Triangular)
   - $\text{High} \in [95, 115, 150, 150]$ (Trapezoidal)
2. **Input 2: Food Wastage ($x_2 \in [0, 50]\%$)**
   - $\text{Low} \in [0, 0, 5, 12]$ (Trapezoidal)
   - $\text{Medium} \in [8, 18, 28]$ (Triangular)
   - $\text{High} \in [22, 35, 50, 50]$ (Trapezoidal)
3. **Output Consequent: Review Priority Score ($z \in [0, 100]$)**
   - $\text{Low Priority} \in [0, 0, 20, 40]$
   - $\text{Medium Priority} \in [25, 50, 75]$
   - $\text{High Priority} \in [60, 80, 100, 100]$

#### Knowledge Base: 9 IF-THEN Rules
| Rule | Nutrition Adequacy ($x_1$) | Food Wastage ($x_2$) | Consequent Priority ($z$) | Expert Rationale |
|:---:|:---:|:---:|:---:|---|
| **R1** | Low | High | **High** | Critical emergency: children are underfed yet prepared food is wasted. |
| **R2** | Low | Medium | **High** | Severe nutrition deficit combined with noticeable food loss. |
| **R3** | Low | Low | **High** | Severe under-nutrition: empty plates because portions/nutrients are critically insufficient. |
| **R4** | Medium | High | **High** | Prepared nutrition is compromised by high food rejection or excess unserved leftovers. |
| **R5** | Medium | Medium | **Medium** | Watchlist: both nutrition and wastage show moderate deviation from target. |
| **R6** | Medium | Low | **Medium** | Good meal consumption, but recipe requires minor fortification. |
| **R7** | High | High | **Medium** | Good nutrition, but excess cooking leads to avoidable economic waste. |
| **R8** | High | Medium | **Low** | Robust nutrition delivered with minor routine plate loss. |
| **R9** | High | Low | **Low** | Ideal operation: statutory nutrition achieved with minimal food loss. |

#### Defuzzification Method
Defuzzification uses the **Centroid of Area (Center of Gravity)** method:
$$Z^* = \frac{\int z \cdot \mu_{\text{Agg}}(z) \, dz}{\int \mu_{\text{Agg}}(z) \, dz}$$

Classification thresholds:
- $Z^* \ge 60$: **High Priority (Immediate Monitoring Review)**
- $35 \le Z^* < 60$: **Medium Priority (Routine Watchlist)**
- $Z^* < 35$: **Low Priority (Compliant / Healthy)**

---

## 🚀 Setup & Execution Instructions

### Prerequisites
- Python 3.10+ (Tested and verified on Python 3.13)
- Modern web browser (Chrome, Edge, Firefox, Safari)

### 1. Installation
Clone or navigate to the project directory:
```bash
cd c:\Users\PC\OneDrive\Desktop\Documents\Desktop\project
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run the Unit & Integration Tests
Execute the automated test suite:
```bash
pytest
```
*Expected output: `17 passed in ~1.0s`.*

### 3. Launch the Web Application
Start Streamlit:
```bash
streamlit run app.py
```
Open your browser to:
```
http://localhost:8501
```

*Note: On first startup, the database is automatically initialized with 12 working days of realistic synthetic data for 6 schools across 2 blocks.*

---

## 🧪 Automated Testing Verification

All unit tests and integration tests have been executed successfully:
- **`tests/test_nutrition.py` (6 tests):** Validates raw/cooked conversion, ICMR IFCT lookups, primary/upper-primary adequacy percentages, negative quantity rejections, and zero-student protections.
- **`tests/test_wastage.py` (4 tests):** Validates kitchen vs. plate waste mathematics, visual quarter-plate conversion factors, and physical consistency rejections (e.g., waste > food prepared, meals > attendance).
- **`tests/test_fuzzy.py` (5 tests):** Validates Mamdani FIS defuzzification, boundary clamping ($<0\%$ or $>150\%$), firing strengths $\alpha_i$, and output priority rankings.
- **`tests/test_integration.py` (2 tests):** Validates SQLite schema generation, meal entry insertion, duplicate session constraint enforcement, and reporting compliance matrix.

---

## 🎓 Soft Computing Viva Defense Guide

Use these key talking points when defending the project to your college viva examiners:

1. **Why use Fuzzy Logic instead of a standard `if-else` threshold?**
   - *Examiner Question:* "Why not simply say: `if nutrition < 90% or waste > 15%: alert = True`?"
   - *Defense:* Crisp Boolean logic creates an artificial discontinuity at arbitrary boundaries. If the standard is 450 kcal, a meal delivering 449 kcal fails as 'non-compliant' identically to one delivering 200 kcal. In contrast, fuzzy membership functions ($\mu(x)$) provide smooth degrees of truth. Furthermore, visual plate waste is inherently qualitative (linguistic variables: *'slight'*, *'moderate'*); fuzzy logic maps human linguistic judgment directly into quantitative assessment without false precision.
2. **Why Mamdani inference rather than Sugeno?**
   - *Defense:* In public policy and educational monitoring, **interpretability** is paramount. Mamdani inference produces fuzzy output sets that can be visually plotted and defended to non-technical stakeholders (e.g., district collectors or school inspectors), whereas Sugeno uses polynomial mathematical functions that lack intuitive linguistic visualization.
3. **Why does Low Nutrition + Low Waste yield High Priority?**
   - *Examiner Question:* "If waste is low, why is the review priority HIGH in Rule R3?"
   - *Defense:* This is a crucial domain insight. When children leave 0% waste on their plates despite receiving a severely calorie-deficient meal, the clean plates indicate acute hunger or ration under-allocation, not successful catering. The school requires immediate monitoring to ensure children receive sufficient food quantities.
4. **How do you address missing records?**
   - *Defense:* Many administrative portals mistakenly calculate averages by treating missing entries as 0% waste or ignoring them. This creates a moral hazard where non-reporting schools appear compliant. Our system cross-references the official academic calendar (excluding Sundays) and maintains an explicit *Missing Reports Roster* with red alert flags.

---

## ⚖️ Academic & Legal Disclaimer

> [!WARNING]
> **ACADEMIC DECISION-SUPPORT NOTICE:**
> The Fuzzy Logic Review Priority index is an algorithmic decision-support tool created strictly for college academic demonstration and soft computing research. It does not constitute an official Government of India administrative audit, disciplinary notice, or clinical dietary diagnosis. All demonstration data is synthetically generated without real student personal identifiable information (PII).
