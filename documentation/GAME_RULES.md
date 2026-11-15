# Official Game Rules & Mechanics Specification - PROXY BOT WARS

## 1. Field of Play
- **Dimensions:** 30 columns × 30 rows.
- **Coordinates:** `x` ranges from `0` to `29` (left to right); `y` ranges from `0` to `29` (top to bottom).
- **Distance Metric:** Chebyshev distance `max(|x1 - x2|, |y1 - y2|)` allowing 8-directional movement.

---

## 2. Bases
- **Blue Base HQ:** Located at cell `(3, 3)`.
- **Red Base HQ:** Located at cell `(26, 26)`.
- **Base Attributes:**
  - Health: 500 HP
  - Attack: 15 damage
  - Attack Range: 2 cells
  - Vision: 6 cells
  - Automated Defense: Attacks the nearest enemy unit within range 2 each turn.

---

## 3. Baseline Unit Classes

| Class | HP | Attack | Speed | Vision | Range | Cost | Strategic Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Scout** | 40 | 5 | 4 | 10 | 1 | 30 | High mobility reconnaissance, perimeter patrol, and fast capture. |
| **Soldier** | 100 | 20 | 2 | 5 | 2 | 50 | Frontline skirmishing, focus firing, and base defense. |
| **Tank** | 250 | 40 | 1 | 4 | 3 | 100 | Heavy siege weapon, fortified pushes, and absorption of damage. |
| **Miner** | 60 | 0 | 2 | 5 | 0 | 40 | Resource extraction from deposits. No attack capability. |
| **Engineer** | 70 | 5 | 2 | 6 | 1 | 60 | Field repairs (+20 HP) and construction of Barricades and Turrets. |

---

## 4. Economy & Resources
- **Starting Treasury:** 100 resources per team.
- **Base Passive Income:** +5 resources every turn.
- **Mining Rate:** 10 resources gathered per miner per turn when adjacent (`dist <= 1`) to a deposit.
- **Resource Deposits:** Symmetrically placed patches holding 500 to 1,000 resources.

---

## 5. Engineer Construction
Engineers can build structures in an adjacent passable cell (`dist <= 1`):
- **Barricade (Cost: 25):** 150 HP. Blocks all unit movement; acts as a deployable obstacle.
- **Turret (Cost: 75):** 120 HP, 15 Attack, 2 Range, 4 Vision. Automatically fires at the closest enemy unit in range.
- **Repair Action:** Restores up to 20 HP to a friendly unit or structure within range 1.

---

## 6. Neutral Control Zones
- 3 Symmetrically placed control zones (Center `(15, 15)`, and two flanking quadrants).
- Uncontested presence by friendly units increases capture progress.
- 3 consecutive uncontested turns captures the zone.
- Once captured, each zone generates +2 territory control points per turn for the owning team.

---

## 7. Victory Conditions
1. **Immediate Victory:** Destroying the opposing team's base HQ.
2. **Elimination Victory:** Eliminating all enemy units when the opponent cannot afford to train new units (< 30 resources).
3. **Turn Limit Victory:** If the match reaches 150 turns, the team with the higher official competition score wins.
4. **Tie-Break Rules:**
   - Tie-Break 1: Highest Combat score.
   - Tie-Break 2: Most total resources gathered.
   - Tie-Break 3: Highest surviving army HP.

