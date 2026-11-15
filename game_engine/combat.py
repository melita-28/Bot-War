"""
Combat resolution system for PROXY BOT WARS.
Handles simultaneous damage, range checks, base defense, turrets, and unit elimination.
"""
from typing import Dict, List, Tuple, Any, Optional

class CombatSystem:
    @staticmethod
    def resolve_combat(game_state, attack_actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Resolves unit attacks and automated defenses (bases and turrets) simultaneously.
        attack_actions: [{'unit_id': int, 'target_id': int, 'target_type': 'unit'|'structure'}]
        """
        events = []
        pending_unit_damage: Dict[int, int] = {}
        pending_structure_damage: Dict[str, int] = {}
        attack_records = []

        # 1. Process player unit attacks
        for act in attack_actions:
            u_id = act.get("unit_id")
            attacker = game_state.units.get(u_id)
            if not attacker or not attacker.alive:
                continue

            target_id = act.get("target_id")
            target_type = act.get("target_type", "unit")

            if target_type == "unit":
                target = game_state.units.get(target_id)
                if not target or not target.alive:
                    events.append({
                        "type": "attack_failed",
                        "attacker_id": u_id,
                        "reason": f"Target unit {target_id} not found or already dead"
                    })
                    continue

                if target.team == attacker.team:
                    events.append({
                        "type": "attack_failed",
                        "attacker_id": u_id,
                        "reason": "Cannot attack friendly unit"
                    })
                    continue

                # Range check (Chebyshev distance)
                dist = max(abs(attacker.x - target.x), abs(attacker.y - target.y))
                if dist > attacker.attack_range or attacker.attack <= 0:
                    events.append({
                        "type": "attack_failed",
                        "attacker_id": u_id,
                        "reason": f"Distance {dist} exceeds attack range {attacker.attack_range}"
                    })
                    continue

                pending_unit_damage[target.id] = pending_unit_damage.get(target.id, 0) + attacker.attack
                attack_records.append({
                    "attacker_id": u_id,
                    "attacker_team": attacker.team,
                    "target_id": target.id,
                    "target_type": "unit",
                    "damage": attacker.attack
                })
                attacker.last_action = {"action": "attack", "target_id": target.id, "target_type": "unit"}

            elif target_type == "structure":
                struct_key = str(target_id)
                target_struct = game_state.structures.get(struct_key)
                if not target_struct or not target_struct.alive:
                    events.append({
                        "type": "attack_failed",
                        "attacker_id": u_id,
                        "reason": f"Target structure {target_id} not found or dead"
                    })
                    continue

                if target_struct.team == attacker.team:
                    events.append({
                        "type": "attack_failed",
                        "attacker_id": u_id,
                        "reason": "Cannot attack friendly structure"
                    })
                    continue

                dist = max(abs(attacker.x - target_struct.x), abs(attacker.y - target_struct.y))
                if dist > attacker.attack_range or attacker.attack <= 0:
                    events.append({
                        "type": "attack_failed",
                        "attacker_id": u_id,
                        "reason": f"Distance {dist} exceeds attack range {attacker.attack_range}"
                    })
                    continue

                pending_structure_damage[struct_key] = pending_structure_damage.get(struct_key, 0) + attacker.attack
                attack_records.append({
                    "attacker_id": u_id,
                    "attacker_team": attacker.team,
                    "target_id": target_struct.id,
                    "target_type": "structure",
                    "damage": attacker.attack
                })
                attacker.last_action = {"action": "attack", "target_id": target_struct.id, "target_type": "structure"}

        # 2. Automated Base & Turret defenses
        for struct_key, struct in game_state.structures.items():
            if not struct.alive or struct.attack <= 0 or struct.attack_range <= 0:
                continue

            # Find closest enemy unit within attack range
            closest_enemy = None
            closest_dist = struct.attack_range + 1
            for unit in game_state.units.values():
                if unit.alive and unit.team != struct.team and unit.team != "neutral":
                    d = max(abs(struct.x - unit.x), abs(struct.y - unit.y))
                    if d <= struct.attack_range and d < closest_dist:
                        closest_enemy = unit
                        closest_dist = d

            if closest_enemy:
                pending_unit_damage[closest_enemy.id] = pending_unit_damage.get(closest_enemy.id, 0) + struct.attack
                attack_records.append({
                    "attacker_id": struct.id,
                    "attacker_team": struct.team,
                    "target_id": closest_enemy.id,
                    "target_type": "unit",
                    "damage": struct.attack
                })

        # 3. Apply damage simultaneously to units
        for u_id, dmg in pending_unit_damage.items():
            unit = game_state.units[u_id]
            actual = unit.take_damage(dmg)
            # Track stats
            game_state.stats[unit.team]["damage_received"] += actual
            enemy_team = "red" if unit.team == "blue" else "blue"
            game_state.stats[enemy_team]["damage_dealt"] += actual

            events.append({
                "type": "unit_damaged",
                "unit_id": u_id,
                "team": unit.team,
                "damage": actual,
                "hp_remaining": unit.hp
            })

            if not unit.alive:
                game_state.stats[unit.team]["units_lost"] += 1
                game_state.stats[enemy_team]["units_killed"] += 1
                events.append({
                    "type": "unit_destroyed",
                    "unit_id": u_id,
                    "team": unit.team
                })

        # 4. Apply damage simultaneously to structures
        for s_key, dmg in pending_structure_damage.items():
            struct = game_state.structures[s_key]
            actual = struct.take_damage(dmg)
            if struct.team in game_state.stats:
                game_state.stats[struct.team]["damage_received"] += actual
                enemy_team = "red" if struct.team == "blue" else "blue"
                game_state.stats[enemy_team]["damage_dealt"] += actual

            events.append({
                "type": "structure_damaged",
                "structure_id": struct.id,
                "structure_type": struct.structure_type,
                "team": struct.team,
                "damage": actual,
                "hp_remaining": struct.hp
            })

            if not struct.alive:
                events.append({
                    "type": "structure_destroyed",
                    "structure_id": struct.id,
                    "structure_type": struct.structure_type,
                    "team": struct.team
                })

        events.extend([{"type": "attack_event", **r} for r in attack_records])
        return events

