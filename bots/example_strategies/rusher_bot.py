"""
PROXY BOT WARS - RUSHER STRATEGY BOT
Aggressive offensive bot:
- Immediately produces combat units
- Ignores defensive setups and rushes the enemy base
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from bot_api.api import BotController, BotHelper, run_bot

class RusherBot(BotController):
    def decide(self, obs: dict) -> dict:
        team = obs.get("team", "blue")
        resources = obs.get("resources", 0)
        units = obs.get("units", [])
        visible_enemies = obs.get("visible_enemies", [])
        visible_structures = obs.get("visible_structures", [])
        map_w = obs.get("map_width", 30)
        map_h = obs.get("map_height", 30)

        opp_base_x = map_w - 4 if team == "blue" else 3
        opp_base_y = map_h - 4 if team == "blue" else 3

        actions = []

        # All resources into soldiers and tanks
        if resources >= 100:
            actions.append({"action": "train", "unit_type": "tank"})
        elif resources >= 50:
            actions.append({"action": "train", "unit_type": "soldier"})

        for unit in units:
            u_id = unit["id"]
            u_type = unit["type"]
            ux, uy = unit["x"], unit["y"]

            # Check if enemy base or structure is in attack range
            enemy_struct_in_range = None
            for s in visible_structures:
                if s["team"] != team and BotHelper.distance(ux, uy, s["x"], s["y"]) <= unit["attack_range"]:
                    enemy_struct_in_range = s
                    break

            # Check if enemy unit in attack range
            enemy_unit_in_range = None
            for e in visible_enemies:
                if BotHelper.distance(ux, uy, e["x"], e["y"]) <= unit["attack_range"]:
                    enemy_unit_in_range = e
                    break

            if enemy_struct_in_range and unit["attack"] > 0:
                actions.append({
                    "unit_id": u_id,
                    "action": "attack",
                    "target_id": enemy_struct_in_range["id"],
                    "target_type": "structure"
                })
            elif enemy_unit_in_range and unit["attack"] > 0:
                actions.append({
                    "unit_id": u_id,
                    "action": "attack",
                    "target_id": enemy_unit_in_range["id"],
                    "target_type": "unit"
                })
            else:
                # Rush directly towards enemy base!
                dx, dy = BotHelper.step_towards(ux, uy, opp_base_x, opp_base_y, max_step=unit["speed"])
                if dx != 0 or dy != 0:
                    actions.append({"unit_id": u_id, "action": "move", "dx": dx, "dy": dy})

        return {"actions": actions, "message": "ALL UNITS CHARGE!"}

if __name__ == "__main__":
    run_bot(RusherBot())

