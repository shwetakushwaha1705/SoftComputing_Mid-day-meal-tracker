"""
Soft Computing Fuzzy Logic Engine for PM POSHAN Tracker
Implements a Mamdani Fuzzy Inference System (FIS) assessing 'Review Priority Score' (0-100)
based on:
  Input 1: Nutrition Adequacy Percentage (0 - 150%)
  Input 2: Food Wastage Percentage (0 - 50%)

Provides:
- scikit-fuzzy integration with membership curves
- Defuzzification via Centroid (Center of Gravity)
- Explainable AI: Rule activation strengths and step-by-step reasoning
- Strict academic disclaimer
"""
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from typing import Dict, Any, List, Tuple
from config import SOFT_COMPUTING_DISCLAIMER


class PoshanFuzzyEngine:
    """
    Mamdani Fuzzy Inference System for School Meal Monitoring.
    """
    def __init__(self):
        # 1. Universes of Discourse
        self.x_adequacy = np.arange(0, 151, 1)    # 0 to 150%
        self.x_waste = np.arange(0, 51, 0.5)      # 0 to 50%
        self.x_priority = np.arange(0, 101, 1)    # 0 to 100 score

        # 2. Membership functions for Nutrition Adequacy
        # Low: peaks at <=40%, drops to 0 at 75%
        self.adequacy_low = fuzz.trapmf(self.x_adequacy, [0, 0, 45, 75])
        # Medium: covers 60% to 110%, peaks around 85%
        self.adequacy_med = fuzz.trimf(self.x_adequacy, [60, 85, 110])
        # High: starts rising at 95%, peak at 115%+
        self.adequacy_high = fuzz.trapmf(self.x_adequacy, [95, 115, 150, 150])

        # 3. Membership functions for Food Wastage Percentage
        # Low: 0 to 12%, minimal waste
        self.waste_low = fuzz.trapmf(self.x_waste, [0, 0, 5, 12])
        # Medium: 8% to 28%
        self.waste_med = fuzz.trimf(self.x_waste, [8, 18, 28])
        # High: 22% to 50%
        self.waste_high = fuzz.trapmf(self.x_waste, [22, 35, 50, 50])

        # 4. Membership functions for Review Priority Output
        # Low Priority: 0 to 40
        self.priority_low = fuzz.trapmf(self.x_priority, [0, 0, 20, 40])
        # Medium Priority: 25 to 75
        self.priority_med = fuzz.trimf(self.x_priority, [25, 50, 75])
        # High Priority: 60 to 100
        self.priority_high = fuzz.trapmf(self.x_priority, [60, 80, 100, 100])

        # 5. Build scikit-fuzzy control system for automated inference
        self._build_control_system()

    def _build_control_system(self):
        # Antecedents & Consequent
        self.antecedent_adequacy = ctrl.Antecedent(self.x_adequacy, 'nutrition_adequacy')
        self.antecedent_waste = ctrl.Antecedent(self.x_waste, 'food_waste')
        self.consequent_priority = ctrl.Consequent(self.x_priority, 'review_priority')

        # Assign memberships to control objects
        self.antecedent_adequacy['low'] = self.adequacy_low
        self.antecedent_adequacy['medium'] = self.adequacy_med
        self.antecedent_adequacy['high'] = self.adequacy_high

        self.antecedent_waste['low'] = self.waste_low
        self.antecedent_waste['medium'] = self.waste_med
        self.antecedent_waste['high'] = self.waste_high

        self.consequent_priority['low'] = self.priority_low
        self.consequent_priority['medium'] = self.priority_med
        self.consequent_priority['high'] = self.priority_high

        # 9 Knowledge-Base Rules (Mamdani Min-Max)
        r1 = ctrl.Rule(self.antecedent_adequacy['low'] & self.antecedent_waste['high'], self.consequent_priority['high'])
        r2 = ctrl.Rule(self.antecedent_adequacy['low'] & self.antecedent_waste['medium'], self.consequent_priority['high'])
        r3 = ctrl.Rule(self.antecedent_adequacy['low'] & self.antecedent_waste['low'], self.consequent_priority['high'])
        r4 = ctrl.Rule(self.antecedent_adequacy['medium'] & self.antecedent_waste['high'], self.consequent_priority['high'])
        r5 = ctrl.Rule(self.antecedent_adequacy['medium'] & self.antecedent_waste['medium'], self.consequent_priority['medium'])
        r6 = ctrl.Rule(self.antecedent_adequacy['medium'] & self.antecedent_waste['low'], self.consequent_priority['medium'])
        r7 = ctrl.Rule(self.antecedent_adequacy['high'] & self.antecedent_waste['high'], self.consequent_priority['medium'])
        r8 = ctrl.Rule(self.antecedent_adequacy['high'] & self.antecedent_waste['medium'], self.consequent_priority['low'])
        r9 = ctrl.Rule(self.antecedent_adequacy['high'] & self.antecedent_waste['low'], self.consequent_priority['low'])

        self.rules = [r1, r2, r3, r4, r5, r6, r7, r8, r9]
        self.control_sys = ctrl.ControlSystem(self.rules)

    def evaluate(self, nutrition_adequacy_pct: float, food_waste_pct: float) -> Dict[str, Any]:
        """
        Executes Mamdani Fuzzy Inference.
        Returns defuzzified crisp score, label, active rules with firing strengths,
        and membership degrees for full transparency and viva defense.
        """
        # Clamp inputs to universe bounds
        clamped_adequacy = float(np.clip(nutrition_adequacy_pct, 0.0, 150.0))
        clamped_waste = float(np.clip(food_waste_pct, 0.0, 50.0))

        # Calculate exact fuzzified membership degrees for inputs
        mu_adeq_low = float(fuzz.interp_membership(self.x_adequacy, self.adequacy_low, clamped_adequacy))
        mu_adeq_med = float(fuzz.interp_membership(self.x_adequacy, self.adequacy_med, clamped_adequacy))
        mu_adeq_high = float(fuzz.interp_membership(self.x_adequacy, self.adequacy_high, clamped_adequacy))

        mu_waste_low = float(fuzz.interp_membership(self.x_waste, self.waste_low, clamped_waste))
        mu_waste_med = float(fuzz.interp_membership(self.x_waste, self.waste_med, clamped_waste))
        mu_waste_high = float(fuzz.interp_membership(self.x_waste, self.waste_high, clamped_waste))

        # Detailed rule evaluations (Mamdani AND = min operator)
        rule_details = [
            {
                "rule_id": "R1",
                "condition": "IF Nutrition is Low AND Waste is High THEN Priority is High",
                "firing_strength": min(mu_adeq_low, mu_waste_high),
                "consequent": "High",
                "rationale": "Critical shortfall: meals underfeed students yet large quantities are thrown away."
            },
            {
                "rule_id": "R2",
                "condition": "IF Nutrition is Low AND Waste is Medium THEN Priority is High",
                "firing_strength": min(mu_adeq_low, mu_waste_med),
                "consequent": "High",
                "rationale": "Severe nutrition deficit combined with noticeable food loss."
            },
            {
                "rule_id": "R3",
                "condition": "IF Nutrition is Low AND Waste is Low THEN Priority is High",
                "firing_strength": min(mu_adeq_low, mu_waste_low),
                "consequent": "High",
                "rationale": "Severe under-nutrition: empty plates due to insufficient food portion or nutrient density."
            },
            {
                "rule_id": "R4",
                "condition": "IF Nutrition is Medium AND Waste is High THEN Priority is High",
                "firing_strength": min(mu_adeq_med, mu_waste_high),
                "consequent": "High",
                "rationale": "Moderate prepared nutrition compromised by excessive food rejection/leftovers."
            },
            {
                "rule_id": "R5",
                "condition": "IF Nutrition is Medium AND Waste is Medium THEN Priority is Medium",
                "firing_strength": min(mu_adeq_med, mu_waste_med),
                "consequent": "Medium",
                "rationale": "Watchlist: both nutrition adequacy and kitchen/plate waste show moderate leakage."
            },
            {
                "rule_id": "R6",
                "condition": "IF Nutrition is Medium AND Waste is Low THEN Priority is Medium",
                "firing_strength": min(mu_adeq_med, mu_waste_low),
                "consequent": "Medium",
                "rationale": "Good meal consumption, but slight nutritional deficit needs fortification."
            },
            {
                "rule_id": "R7",
                "condition": "IF Nutrition is High AND Waste is High THEN Priority is Medium",
                "firing_strength": min(mu_adeq_high, mu_waste_high),
                "consequent": "Medium",
                "rationale": "Nutritionally sound recipes, but excess cooking leads to avoidable economic waste."
            },
            {
                "rule_id": "R8",
                "condition": "IF Nutrition is High AND Waste is Medium THEN Priority is Low",
                "firing_strength": min(mu_adeq_high, mu_waste_med),
                "consequent": "Low",
                "rationale": "Robust nutrition targets met with minor routine plate loss."
            },
            {
                "rule_id": "R9",
                "condition": "IF Nutrition is High AND Waste is Low THEN Priority is Low",
                "firing_strength": min(mu_adeq_high, mu_waste_low),
                "consequent": "Low",
                "rationale": "Exemplary school kitchen operation: high nutritional value and clean consumption."
            }
        ]

        # Evaluate using control simulator
        sim = ctrl.ControlSystemSimulation(self.control_sys)
        sim.input['nutrition_adequacy'] = clamped_adequacy
        sim.input['food_waste'] = clamped_waste
        
        try:
            sim.compute()
            score = float(sim.output['review_priority'])
        except Exception:
            # Fallback manual centroid defuzzification
            score = self._manual_defuzzify(rule_details)

        score = round(float(np.clip(score, 0.0, 100.0)), 2)

        # Categorical label assignment
        if score >= 60.0:
            priority_label = "High Priority (Immediate Monitoring Review)"
            color = "#E53E3E"  # Red
            badge = "HIGH"
        elif score >= 35.0:
            priority_label = "Medium Priority (Routine Watchlist)"
            color = "#DD6B20"  # Orange/Amber
            badge = "MEDIUM"
        else:
            priority_label = "Low Priority (Compliant / Healthy)"
            color = "#38A169"  # Green
            badge = "LOW"

        # Filter active rules (firing strength > 0.01)
        active_rules = [r for r in rule_details if r["firing_strength"] > 0.001]
        active_rules.sort(key=lambda x: x["firing_strength"], reverse=True)

        return {
            "nutrition_adequacy_pct": round(nutrition_adequacy_pct, 2),
            "food_waste_pct": round(food_waste_pct, 2),
            "review_priority_score": score,
            "priority_label": priority_label,
            "priority_badge": badge,
            "color": color,
            "membership_degrees": {
                "adequacy": {
                    "Low": round(mu_adeq_low, 3),
                    "Medium": round(mu_adeq_med, 3),
                    "High": round(mu_adeq_high, 3)
                },
                "waste": {
                    "Low": round(mu_waste_low, 3),
                    "Medium": round(mu_waste_med, 3),
                    "High": round(mu_waste_high, 3)
                }
            },
            "active_rules": active_rules,
            "all_rules": rule_details,
            "disclaimer": SOFT_COMPUTING_DISCLAIMER
        }

    def _manual_defuzzify(self, rule_details: List[Dict[str, Any]]) -> float:
        """
        Pure Centroid (Center of Gravity) Defuzzification fallback:
        COG = sum(x * aggregated(x)) / sum(aggregated(x))
        """
        # Aggregate activations for output categories
        strength_high = max([r["firing_strength"] for r in rule_details if r["consequent"] == "High"] + [0.0])
        strength_med = max([r["firing_strength"] for r in rule_details if r["consequent"] == "Medium"] + [0.0])
        strength_low = max([r["firing_strength"] for r in rule_details if r["consequent"] == "Low"] + [0.0])

        # Clip output membership functions
        clip_low = np.fmin(strength_low, self.priority_low)
        clip_med = np.fmin(strength_med, self.priority_med)
        clip_high = np.fmin(strength_high, self.priority_high)

        # Union (Max) of clipped outputs
        aggregated = np.fmax(clip_low, np.fmax(clip_med, clip_high))

        sum_agg = np.sum(aggregated)
        if sum_agg == 0:
            return 50.0  # Default neutral
        return float(np.sum(self.x_priority * aggregated) / sum_agg)


# Singleton instance for quick access
fuzzy_engine = PoshanFuzzyEngine()
