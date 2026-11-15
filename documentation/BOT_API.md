# Bot API & Communication Specification - PROXY BOT WARS

Autonomous bots communicate with the game engine via standard input (`sys.stdin`) and standard output (`sys.stdout`) in single-line JSON format.

---

## 1. Input: Turn Observation

On each turn, the engine writes a single-line JSON object to the bot's standard input.

```json
{
  "turn": 1,
  "max_turns": 150,
  "team": "blue",
  "resources": 100,
  "base": {
    "id": "base_blue",
    "type": "base",
    "team": "blue",
    "x": 3,
    "y": 3,
    "hp": 500,
    "max_hp": 500,
    "attack": 15,
    "attack_range": 2,
    "vision": 6
  },
  "units": [
    {
      "id": 1,
      "type": "scout",
      "team": "blue",
      "x": 4,
      "y": 3,
      "hp": 40,
      "max_hp": 40,
      "attack": 5,
      "speed": 4,
      "vision": 10,
      "attack_range": 1,
      "carried_resources": 0,
      "alive": true,
      "last_action": null
    }
  ],
  "visible_enemies": [],
  "visible_structures": [],
  "visible_resources": [
    {"id": 1, "x": 5, "y": 3, "amount": 500, "max_amount": 500}
  ],
  "control_zones": [
    {"id": 1, "x": 15, "y": 15, "radius": 1, "owner": null, "progress": 0}
  ],
  "known_obstacles": [[5, 10], [5, 11]],
  "team_message": "",
  "map_width": 30,
  "map_height": 30,
  "explored_count": 85,
  "stats": {
    "damage_dealt": 0,
    "units_killed": 0,
    "resources_collected": 0
  }
}
```

---

## 2. Output: Actions & Message

The bot must respond with a single-line JSON object on standard output terminated by a newline:

```json
{
  "actions": [
    {"unit_id": 1, "action": "move", "dx": 2, "dy": 0},
    {"unit_id": 2, "action": "gather", "deposit_id": 1},
    {"unit_id": 3, "action": "attack", "target_id": 102, "target_type": "unit"},
    {"action": "train", "unit_type": "soldier"}
  ],
  "message": "Scout spotted enemy south-west"
}
```

---

## 3. Formal Actions Schema

### Move Action
- **`unit_id`** (integer): ID of the friendly unit to move.
- **`action`**: `"move"`.
- **`dx`** (integer): Offset in X (`-speed <= dx <= speed`).
- **`dy`** (integer): Offset in Y (`-speed <= dy <= speed`).
- **Condition:** $\max(|dx|, |dy|) \le \text{unit speed}$. Target cell must be in bounds, not an obstacle, and not occupied.

### Attack Action
- **`unit_id`** (integer): Attacking unit ID.
- **`action`**: `"attack"`.
- **`target_id`** (integer or string): Target unit ID or structure ID.
- **`target_type`** (string): `"unit"` or `"structure"`.
- **Condition:** Target must be an enemy. Chebyshev distance $\le \text{attack range}$.

### Gather Action
- **`unit_id`** (integer): Miner unit ID.
- **`action`**: `"gather"`.
- **`deposit_id`** (integer): Target resource deposit ID.
- **Condition:** Unit must be a Miner. Distance to deposit $\le 1$.

### Build Action
- **`unit_id`** (integer): Engineer unit ID.
- **`action`**: `"build"`.
- **`structure_type`** (string): `"barricade"` or `"turret"`.
- **`target_x`**, **`target_y`** (integers): Adjacent coordinate (`dist <= 1`).
- **Condition:** Cell must be empty, passable, and team must afford the cost.

### Repair Action
- **`unit_id`** (integer): Engineer unit ID.
- **`action`**: `"repair"`.
- **`target_id`**: Friendly unit ID or structure ID.
- **`target_type`**: `"unit"` or `"structure"`.
- **Condition:** Target must be friendly and damaged (`dist <= 1`).

### Train Action
- **`action`**: `"train"`.
- **`unit_type`** (string): `"scout"`, `"soldier"`, `"tank"`, `"miner"`, or `"engineer"`.
- **Condition:** Base must be alive and team must have sufficient resources.

