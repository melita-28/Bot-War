"""
Deterministic competition scoring system for PROXY BOT WARS.
Implements the 5 official scoring categories with specified weights:
- Combat / objective performance (30%)
- Resource and territory control (20%)
- Strategic decision-making (20%)
- Efficiency / computation (15%)
- Adaptability / information use (15%)
"""
from typing import Dict, Any
from game_engine.config import SCORING_WEIGHTS, UNIT_SPECS

class ScoringSystem:
    @staticmethod
    def calculate_team_scores(game_state, team: str) -> Dict[str, Any]:
        stats = game_state.stats[team]
        opp_team = "red" if team == "blue" else "blue"
        opp_stats = game_state.stats[opp_team]

        # 1. Combat Score (30%)
        # Based on damage dealt to units and structures + units destroyed
        raw_combat = (stats["damage_dealt"] * 0.2) + (stats["units_killed"] * 15.0)
        opp_base = game_state.structures.get(f"base_{opp_team}")
        if opp_base:
            base_damage = opp_base.max_hp - opp_base.hp
            raw_combat += (base_damage * 0.1)
        combat_score = min(100.0, max(0.0, raw_combat))

        # 2. Resource & Territory Score (20%)
        # Based on resources collected and control zone points
        raw_resource = (stats["resources_collected"] * 0.15) + (stats["control_points"] * 2.5)
        resource_score = min(100.0, max(0.0, raw_resource))

        # 3. Strategic Decision-Making (20%)
        # Surviving army valuation + active defenses + friendly base health
        alive_unit_val = sum(UNIT_SPECS[u.unit_type]["cost"] for u in game_state.units.values() if u.alive and u.team == team)
        friendly_base = game_state.structures.get(f"base_{team}")
        base_hp = friendly_base.hp if friendly_base and friendly_base.alive else 0
        raw_strategic = (alive_unit_val * 0.2) + (stats["structures_built"] * 10.0) + (base_hp * 0.1)
        strategic_score = min(100.0, max(0.0, raw_strategic))

        # 4. Efficiency / Computation Score (15%)
        # Execution speed within 1.0s budget and economic efficiency (resources put to work)
        avg_time_ms = stats["total_time_ms"] / max(1, stats["turns_executed"])
        time_score = max(0.0, 100.0 - (avg_time_ms / 10.0)) # 0ms -> 100, 500ms -> 50, 1000ms -> 0
        spend_ratio = (stats["resources_spent"] / max(1, stats["resources_collected"])) * 100.0
        efficiency_score = min(100.0, max(0.0, (time_score * 0.5) + (min(100.0, spend_ratio) * 0.5)))

        # 5. Adaptability / Information Use (15%)
        # Map explored percentage + recon capability
        total_cells = game_state.game_map.width * game_state.game_map.height
        explored_count = len(game_state.explored_cells.get(team, set()))
        explored_pct = (explored_count / max(1, total_cells)) * 100.0
        adaptability_score = min(100.0, max(0.0, (explored_pct * 1.2)))

        # Final weighted score
        final_score = (
            SCORING_WEIGHTS["combat"] * combat_score +
            SCORING_WEIGHTS["resource_territory"] * resource_score +
            SCORING_WEIGHTS["strategic"] * strategic_score +
            SCORING_WEIGHTS["efficiency"] * efficiency_score +
            SCORING_WEIGHTS["adaptability"] * adaptability_score
        )

        return {
            "team": team,
            "final_score": round(final_score, 2),
            "breakdown": {
                "combat": round(combat_score, 2),
                "resource_territory": round(resource_score, 2),
                "strategic": round(strategic_score, 2),
                "efficiency": round(efficiency_score, 2),
                "adaptability": round(adaptability_score, 2)
            },
            "metrics": {
                "damage_dealt": stats["damage_dealt"],
                "units_killed": stats["units_killed"],
                "resources_collected": stats["resources_collected"],
                "control_points": stats["control_points"],
                "structures_built": stats["structures_built"],
                "explored_cells": explored_count,
                "explored_pct": round(explored_pct, 1),
                "avg_turn_ms": round(avg_time_ms, 2)
            }
        }

