"""
Resource collection, economy, and unit training system for PROXY BOT WARS.
"""
from typing import Dict, List, Tuple, Any, Optional
from game_engine.config import (
    MINER_GATHER_RATE, BASE_PASSIVE_INCOME, UNIT_SPECS
)
from game_engine.units import Unit

class ResourceSystem:
    @staticmethod
    def resolve_gathering(game_state, gather_actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Resolves gather actions from Miners.
        gather_actions: [{'unit_id': int, 'deposit_id': int}]
        """
        events = []
        for act in gather_actions:
            u_id = act.get("unit_id")
            miner = game_state.units.get(u_id)
            if not miner or not miner.alive:
                continue

            if miner.unit_type != "miner":
                events.append({
                    "type": "gather_failed",
                    "unit_id": u_id,
                    "reason": "Only Miners can gather resources"
                })
                continue

            dep_id = act.get("deposit_id")
            deposit = game_state.game_map.resource_deposits.get(dep_id)
            if not deposit or deposit.amount <= 0:
                events.append({
                    "type": "gather_failed",
                    "unit_id": u_id,
                    "reason": "Resource deposit not found or depleted"
                })
                continue

            # Check adjacency (Chebyshev distance <= 1)
            dist = max(abs(miner.x - deposit.x), abs(miner.y - deposit.y))
            if dist > 1:
                events.append({
                    "type": "gather_failed",
                    "unit_id": u_id,
                    "reason": f"Distance {dist} to deposit exceeds gathering range (1 cell)"
                })
                continue

            gathered = min(deposit.amount, MINER_GATHER_RATE)
            deposit.amount -= gathered
            game_state.team_resources[miner.team] += gathered
            game_state.stats[miner.team]["resources_collected"] += gathered

            miner.last_action = {"action": "gather", "deposit_id": dep_id, "amount": gathered}

            events.append({
                "type": "resource_gathered",
                "unit_id": u_id,
                "team": miner.team,
                "deposit_id": dep_id,
                "amount": gathered,
                "deposit_remaining": deposit.amount,
                "team_balance": game_state.team_resources[miner.team]
            })

        # Apply base passive income
        for team in ["blue", "red"]:
            base = game_state.structures.get(f"base_{team}")
            if base and base.alive:
                game_state.team_resources[team] += BASE_PASSIVE_INCOME
                game_state.stats[team]["resources_collected"] += BASE_PASSIVE_INCOME

        return events

    @staticmethod
    def resolve_training(game_state, train_actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Resolves unit production at the team base.
        train_actions: [{'team': str, 'unit_type': str}]
        """
        events = []
        for act in train_actions:
            team = act.get("team")
            unit_type = act.get("unit_type")
            if team not in ["blue", "red"] or unit_type not in UNIT_SPECS:
                events.append({
                    "type": "train_failed",
                    "team": team,
                    "unit_type": unit_type,
                    "reason": "Invalid team or unit type"
                })
                continue

            base = game_state.structures.get(f"base_{team}")
            if not base or not base.alive:
                events.append({
                    "type": "train_failed",
                    "team": team,
                    "reason": "Base is destroyed"
                })
                continue

            cost = UNIT_SPECS[unit_type]["cost"]
            if game_state.team_resources[team] < cost:
                events.append({
                    "type": "train_failed",
                    "team": team,
                    "unit_type": unit_type,
                    "reason": f"Insufficient resources: need {cost}, have {game_state.team_resources[team]}"
                })
                continue

            # Find empty adjacent cell around base to spawn
            spawn_pos = None
            occupied_cells = {(u.x, u.y) for u in game_state.units.values() if u.alive}
            occupied_cells.update({(s.x, s.y) for s in game_state.structures.values() if s.alive})

            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    candidate = (base.x + dx, base.y + dy)
                    if (game_state.game_map.is_passable(candidate[0], candidate[1]) and
                        candidate not in occupied_cells):
                        spawn_pos = candidate
                        break
                if spawn_pos:
                    break

            if not spawn_pos:
                events.append({
                    "type": "train_failed",
                    "team": team,
                    "unit_type": unit_type,
                    "reason": "All adjacent cells around base are blocked"
                })
                continue

            # Deduct cost and spawn unit
            game_state.team_resources[team] -= cost
            game_state.stats[team]["resources_spent"] += cost
            game_state.stats[team]["units_trained"] += 1

            new_unit_id = game_state.next_unit_id
            game_state.next_unit_id += 1

            new_unit = Unit.create(
                unit_id=new_unit_id,
                unit_type=unit_type,
                team=team,
                x=spawn_pos[0],
                y=spawn_pos[1]
            )
            game_state.units[new_unit_id] = new_unit

            events.append({
                "type": "unit_trained",
                "unit_id": new_unit_id,
                "unit_type": unit_type,
                "team": team,
                "x": spawn_pos[0],
                "y": spawn_pos[1],
                "cost": cost,
                "remaining_resources": game_state.team_resources[team]
            })

        return events

