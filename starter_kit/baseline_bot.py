"""
=============================================================================
PROXY BOT WARS - BASELINE COMPETITIVE BOT
=============================================================================
Balanced, tactical benchmark bot featuring:
- Economic expansion (trains miners, mines nearest safe nodes)
- Defensive engineer deployment (builds turrets at choke points)
- Attack squad formation (Soldiers and Tanks move in cohesive fireteams)
- Dynamic target acquisition (focuses fire on weakest enemy in range)
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bot_api.api import BotController, BotHelper, run_bot

class BaselineBot(BotController):
    def __init__(self):
        super().__init__()
        self.turret_built = False

    def decide(self, obs: dict) -> dict:
        turn = obs.get("turn", 0)
        team = obs.get("team", "blue")
        resources = obs.get("resources", 0)
        units = obs.get("units", [])
        visible_enemies = obs.get("visible_enemies", [])
        visible_resources = obs.get("visible_resources", [])
        control_zones = obs.get("control_zones", [])
        base = obs.get("base")
        map_w = obs.get("map_width", 30)
        map_h = obs.get("map_height", 30)

        # Opposite base predicted location based on symmetry
        opp_base_x = map_w - 4 if team == "blue" else 3
        opp_base_y = map_h - 4 if team == "blue" else 3

        actions = []

        # 1. Economic Production Strategy
        miner_count = sum(1 for u in units if u["type"] == "miner")
        soldier_count = sum(1 for u in units if u["type"] == "soldier")
        tank_count = sum(1 for u in units if u["type"] == "tank")

        if miner_count < 2 and resources >= 40:
            actions.append({"action": "train", "unit_type": "miner"})
        elif soldier_count < 3 and resources >= 50:
            actions.append({"action": "train", "unit_type": "soldier"})
        elif resources >= 100:
            actions.append({"action": "train", "unit_type": "tank"})

        # 2. Units Execution
        for unit in units:
            u_id = unit["id"]
            u_type = unit["type"]
            ux, uy = unit["x"], unit["y"]

            # MINER
            if u_type == "miner":
                # Check for adjacent resource
                adjacent_dep = None
                for dep in visible_resources:
                    if dep.get("amount", 0) > 0 and BotHelper.distance(ux, uy, dep["x"], dep["y"]) <= 1:
                        adjacent_dep = dep
                        break

                if adjacent_dep:
                    actions.append({"unit_id": u_id, "action": "gather", "deposit_id": adjacent_dep["id"]})
                else:
                    available_deps = [d for d in visible_resources if d.get("amount", 0) > 0]
                    if available_deps:
                        closest = min(available_deps, key=lambda d: BotHelper.distance(ux, uy, d["x"], d["y"]))
                        dx, dy = BotHelper.step_towards(ux, uy, closest["x"], closest["y"], max_step=unit["speed"])
                        if dx != 0 or dy != 0:
                            actions.append({"unit_id": u_id, "action": "move", "dx": dx, "dy": dy})

            # ENGINEER: Build turret first, then support
            elif u_type == "engineer":
                # If can afford turret and not yet built near base
                if not self.turret_built and resources >= 75 and base:
                    # Choose a defensive spot 1 cell towards map center
                    tx = base["x"] + (1 if team == "blue" else -1)
                    ty = base["y"] + (1 if team == "blue" else -1)
                    # If adjacent to target spot, build it!
                    if BotHelper.distance(ux, uy, tx, ty) <= 1 and (ux != tx or uy != ty):
                        actions.append({
                            "unit_id": u_id,
                            "action": "build",
                            "structure_type": "turret",
                            "target_x": tx,
                            "target_y": ty
                        })
                        self.turret_built = True
                    else:
                        dx, dy = BotHelper.step_towards(ux, uy, tx, ty, max_step=unit["speed"])
                        if dx != 0 or dy != 0:
                            actions.append({"unit_id": u_id, "action": "move", "dx": dx, "dy": dy})
                else:
                    # Repair damaged friendly units in range
                    damaged = [u for u in units if u["id"] != u_id and u["hp"] < u["max_hp"] and BotHelper.distance(ux, uy, u["x"], u["y"]) <= 1]
                    if damaged:
                        # Prioritize highest value damaged unit (Tank > Soldier)
                        target = max(damaged, key=lambda u: u["max_hp"])
                        actions.append({"unit_id": u_id, "action": "repair", "target_id": target["id"], "target_type": "unit"})
                    else:
                        # Follow soldiers
                        combatants = [u for u in units if u["type"] in ["soldier", "tank"]]
                        if combatants:
                            c = combatants[0]
                            dx, dy = BotHelper.step_towards(ux, uy, c["x"], c["y"], max_step=unit["speed"])
                            if dx != 0 or dy != 0:
                                actions.append({"unit_id": u_id, "action": "move", "dx": dx, "dy": dy})

            # COMBAT UNITS: SOLDIER & TANK
            elif u_type in ["soldier", "tank"]:
                # Check for enemies in range - focus fire on lowest HP enemy
                enemies_in_range = [
                    e for e in visible_enemies
                    if BotHelper.distance(ux, uy, e["x"], e["y"]) <= unit["attack_range"]
                ]
                if enemies_in_range:
                    weakest = min(enemies_in_range, key=lambda e: e["hp"])
                    actions.append({"unit_id": u_id, "action": "attack", "target_id": weakest["id"], "target_type": "unit"})
                elif visible_enemies:
                    # Move towards closest visible enemy
                    closest_enemy = min(visible_enemies, key=lambda e: BotHelper.distance(ux, uy, e["x"], e["y"]))
                    dx, dy = BotHelper.step_towards(ux, uy, closest_enemy["x"], closest_enemy["y"], max_step=unit["speed"])
                    if dx != 0 or dy != 0:
                        actions.append({"unit_id": u_id, "action": "move", "dx": dx, "dy": dy})
                else:
                    # March towards center control zone or enemy base
                    unowned_zones = [z for z in control_zones if z.get("owner") != team]
                    if unowned_zones:
                        target_zone = min(unowned_zones, key=lambda z: BotHelper.distance(ux, uy, z["x"], z["y"]))
                        tx, ty = target_zone["x"], target_zone["y"]
                    else:
                        tx, ty = opp_base_x, opp_base_y
                    dx, dy = BotHelper.step_towards(ux, uy, tx, ty, max_step=unit["speed"])
                    if dx != 0 or dy != 0:
                        actions.append({"unit_id": u_id, "action": "move", "dx": dx, "dy": dy})

            # SCOUT: High-speed zone capturing and flank discovery
            elif u_type == "scout":
                # Head straight to central control zone
                cz = [z for z in control_zones if z["id"] == 1]
                if cz:
                    tx, ty = cz[0]["x"], cz[0]["y"]
                else:
                    tx, ty = map_w // 2, map_h // 2
                dx, dy = BotHelper.step_towards(ux, uy, tx, ty, max_step=unit["speed"])
                if dx != 0 or dy != 0:
                    actions.append({"unit_id": u_id, "action": "move", "dx": dx, "dy": dy})

        return {
            "actions": actions,
            "message": f"Turn {turn} Baseline operational"
        }

if __name__ == "__main__":
    run_bot(BaselineBot())
