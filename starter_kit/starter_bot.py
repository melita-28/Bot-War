"""
=============================================================================
PROXY BOT WARS - STARTER BOT (ROLE-BASED MODULAR ARCHITECTURE)
=============================================================================
Welcome to PROXY '26 BOT WARS!

This bot demonstrates a clean, role-delegated architecture where decision-making
is organized into modular handlers for each unit class:
- handle_economy(): Unit production and resource management
- handle_scouts(): Reconnaissance and perimeter discovery
- handle_miners(): Adjacent and nearest node resource gathering
- handle_combat(): Frontline combat, target prioritization, and defense
- handle_engineers(): Field repair and fortification construction
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bot_api.api import BotController, BotHelper, run_bot

class StarterBot(BotController):
    """
    StarterBot organizes decisions by unit roles, making it easy to read,
    customize, and expand with your own strategy.
    """

    def decide(self, obs: dict) -> dict:
        self.obs = obs
        self.team = obs.get("team", "blue")
        self.resources = obs.get("resources", 0)
        self.units = obs.get("units", [])
        self.visible_enemies = obs.get("visible_enemies", [])
        self.visible_resources = obs.get("visible_resources", [])
        self.control_zones = obs.get("control_zones", [])
        self.base = obs.get("base")

        actions = []

        # 1. Macro Economy & Unit Training
        actions.extend(self.handle_economy())

        # 2. Individual Unit Role Dispatchers
        for unit in self.units:
            u_type = unit["type"]
            if u_type == "scout":
                act = self.handle_scout(unit)
            elif u_type == "miner":
                act = self.handle_miner(unit)
            elif u_type in ["soldier", "tank"]:
                act = self.handle_combat_unit(unit)
            elif u_type == "engineer":
                act = self.handle_engineer(unit)
            else:
                act = None

            if act:
                actions.append(act)

        # 3. Compact Strategic Message (under 100 bytes)
        msg = f"T{obs.get('turn', 0)}|U:{len(self.units)}|R:{self.resources}"

        return {
            "actions": actions,
            "message": msg
        }

    # -------------------------------------------------------------------------
    # 1. ECONOMY: Train new units
    # -------------------------------------------------------------------------
    def handle_economy(self) -> list:
        actions = []
        miner_count = sum(1 for u in self.units if u["type"] == "miner")
        soldier_count = sum(1 for u in self.units if u["type"] == "soldier")

        # Keep at least 2 miners active for resource flow
        if miner_count < 2 and self.resources >= 40:
            actions.append({"action": "train", "unit_type": "miner"})
        elif self.resources >= 100:
            actions.append({"action": "train", "unit_type": "tank"})
        elif self.resources >= 50:
            actions.append({"action": "train", "unit_type": "soldier"})

        return actions

    # -------------------------------------------------------------------------
    # 2. SCOUT: Rapid reconnaissance & control zone capture
    # -------------------------------------------------------------------------
    def handle_scout(self, unit: dict) -> dict:
        ux, uy = unit["x"], unit["y"]

        # Objective: Move towards nearest unowned or central control zone
        target = None
        if self.control_zones:
            target = min(self.control_zones, key=lambda z: BotHelper.distance(ux, uy, z["x"], z["y"]))
            tx, ty = target["x"], target["y"]
        else:
            tx, ty = self.obs.get("map_width", 30) // 2, self.obs.get("map_height", 30) // 2

        dx, dy = BotHelper.step_towards(ux, uy, tx, ty, max_step=unit["speed"])
        if dx != 0 or dy != 0:
            return {"unit_id": unit["id"], "action": "move", "dx": dx, "dy": dy}
        return None

    # -------------------------------------------------------------------------
    # 3. MINER: Extraction of nearby ore and Tempest crystal deposits
    # -------------------------------------------------------------------------
    def handle_miner(self, unit: dict) -> dict:
        ux, uy = unit["x"], unit["y"]

        # Check if already adjacent to a deposit with remaining resources
        adjacent_dep = next(
            (d for d in self.visible_resources if d.get("amount", 0) > 0 and BotHelper.distance(ux, uy, d["x"], d["y"]) <= 1),
            None
        )
        if adjacent_dep:
            return {"unit_id": unit["id"], "action": "gather", "deposit_id": adjacent_dep["id"]}

        # Otherwise move towards closest known deposit
        active_deps = [d for d in self.visible_resources if d.get("amount", 0) > 0]
        if active_deps:
            closest = min(active_deps, key=lambda d: BotHelper.distance(ux, uy, d["x"], d["y"]))
            dx, dy = BotHelper.step_towards(ux, uy, closest["x"], closest["y"], max_step=unit["speed"])
            if dx != 0 or dy != 0:
                return {"unit_id": unit["id"], "action": "move", "dx": dx, "dy": dy}

        return None

    # -------------------------------------------------------------------------
    # 4. SOLDIER & TANK: Tactical combat & focus firing
    # -------------------------------------------------------------------------
    def handle_combat_unit(self, unit: dict) -> dict:
        ux, uy = unit["x"], unit["y"]

        # Check for enemies in attack range
        in_range = [
            e for e in self.visible_enemies
            if BotHelper.distance(ux, uy, e["x"], e["y"]) <= unit["attack_range"]
        ]
        if in_range:
            # Focus fire on the enemy with lowest health
            weakest = min(in_range, key=lambda e: e["hp"])
            return {"unit_id": unit["id"], "action": "attack", "target_id": weakest["id"], "target_type": "unit"}

        # Move towards closest visible enemy
        if self.visible_enemies:
            closest_enemy = min(self.visible_enemies, key=lambda e: BotHelper.distance(ux, uy, e["x"], e["y"]))
            dx, dy = BotHelper.step_towards(ux, uy, closest_enemy["x"], closest_enemy["y"], max_step=unit["speed"])
            if dx != 0 or dy != 0:
                return {"unit_id": unit["id"], "action": "move", "dx": dx, "dy": dy}

        # Otherwise march to contested center
        cx, cy = self.obs.get("map_width", 30) // 2, self.obs.get("map_height", 30) // 2
        dx, dy = BotHelper.step_towards(ux, uy, cx, cy, max_step=unit["speed"])
        if dx != 0 or dy != 0:
            return {"unit_id": unit["id"], "action": "move", "dx": dx, "dy": dy}

        return None

    # -------------------------------------------------------------------------
    # 5. ENGINEER: Support, field repair and barricade construction
    # -------------------------------------------------------------------------
    def handle_engineer(self, unit: dict) -> dict:
        ux, uy = unit["x"], unit["y"]

        # Check for adjacent damaged friendly units
        damaged_allies = [
            u for u in self.units
            if u["id"] != unit["id"] and u["hp"] < u["max_hp"] and BotHelper.distance(ux, uy, u["x"], u["y"]) <= 1
        ]
        if damaged_allies:
            target = max(damaged_allies, key=lambda u: u["max_hp"]) # Prioritize tanks/soldiers
            return {"unit_id": unit["id"], "action": "repair", "target_id": target["id"], "target_type": "unit"}

        # Follow combatants
        combatants = [u for u in self.units if u["type"] in ["soldier", "tank"]]
        if combatants:
            c = combatants[0]
            dx, dy = BotHelper.step_towards(ux, uy, c["x"], c["y"], max_step=unit["speed"])
            if dx != 0 or dy != 0:
                return {"unit_id": unit["id"], "action": "move", "dx": dx, "dy": dy}

        return None

if __name__ == "__main__":
    run_bot(StarterBot())
