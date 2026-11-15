"""
PROXY BOT WARS - TURTLE STRATEGY BOT
Defensive bot focused on heavy fortification, engineer construction, and resource accumulation.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from bot_api.api import BotController, BotHelper, run_bot

class TurtleBot(BotController):
    def __init__(self):
        super().__init__()
        self.built_barricades = 0

    def decide(self, obs: dict) -> dict:
        team = obs.get("team", "blue")
        resources = obs.get("resources", 0)
        units = obs.get("units", [])
        visible_enemies = obs.get("visible_enemies", [])
        visible_resources = obs.get("visible_resources", [])
        base = obs.get("base")

        actions = []

        # Train engineers and miners
        eng_count = sum(1 for u in units if u["type"] == "engineer")
        miner_count = sum(1 for u in units if u["type"] == "miner")

        if miner_count < 3 and resources >= 40:
            actions.append({"action": "train", "unit_type": "miner"})
        elif eng_count < 2 and resources >= 60:
            actions.append({"action": "train", "unit_type": "engineer"})
        elif resources >= 100:
            actions.append({"action": "train", "unit_type": "tank"})

        for unit in units:
            u_id = unit["id"]
            u_type = unit["type"]
            ux, uy = unit["x"], unit["y"]

            if u_type == "miner":
                # Gather resources
                adj = next((d for d in visible_resources if d.get("amount", 0) > 0 and BotHelper.distance(ux, uy, d["x"], d["y"]) <= 1), None)
                if adj:
                    actions.append({"unit_id": u_id, "action": "gather", "deposit_id": adj["id"]})
                else:
                    avail = [d for d in visible_resources if d.get("amount", 0) > 0]
                    if avail:
                        cl = min(avail, key=lambda d: BotHelper.distance(ux, uy, d["x"], d["y"]))
                        dx, dy = BotHelper.step_towards(ux, uy, cl["x"], cl["y"], max_step=unit["speed"])
                        if dx != 0 or dy != 0:
                            actions.append({"unit_id": u_id, "action": "move", "dx": dx, "dy": dy})

            elif u_type == "engineer":
                # Build barricades around base
                if self.built_barricades < 3 and resources >= 25 and base:
                    bx, by = base["x"], base["y"]
                    offset = 2 if team == "blue" else -2
                    tx, ty = bx + offset, by + offset
                    if BotHelper.distance(ux, uy, tx, ty) <= 1 and (ux != tx or uy != ty):
                        actions.append({
                            "unit_id": u_id,
                            "action": "build",
                            "structure_type": "barricade",
                            "target_x": tx,
                            "target_y": ty
                        })
                        self.built_barricades += 1
                    else:
                        dx, dy = BotHelper.step_towards(ux, uy, tx, ty, max_step=unit["speed"])
                        if dx != 0 or dy != 0:
                            actions.append({"unit_id": u_id, "action": "move", "dx": dx, "dy": dy})
                else:
                    # Repair friendly units
                    damaged = [u for u in units if u["id"] != u_id and u["hp"] < u["max_hp"] and BotHelper.distance(ux, uy, u["x"], u["y"]) <= 1]
                    if damaged:
                        actions.append({"unit_id": u_id, "action": "repair", "target_id": damaged[0]["id"], "target_type": "unit"})

            elif u_type in ["soldier", "tank"]:
                # Attack nearby enemies or stay close to base
                enemies_in_range = [e for e in visible_enemies if BotHelper.distance(ux, uy, e["x"], e["y"]) <= unit["attack_range"]]
                if enemies_in_range:
                    actions.append({"unit_id": u_id, "action": "attack", "target_id": enemies_in_range[0]["id"], "target_type": "unit"})
                elif base:
                    # Guard perimeter (distance 3 from base)
                    if BotHelper.distance(ux, uy, base["x"], base["y"]) > 4:
                        dx, dy = BotHelper.step_towards(ux, uy, base["x"], base["y"], max_step=unit["speed"])
                        if dx != 0 or dy != 0:
                            actions.append({"unit_id": u_id, "action": "move", "dx": dx, "dy": dy})

        return {"actions": actions, "message": "Fortifications holding"}

if __name__ == "__main__":
    run_bot(TurtleBot())
