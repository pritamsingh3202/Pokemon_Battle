import random
from typing import Dict, List, Tuple

# Type effectiveness chart
TYPE_CHART = {
    "normal": {"rock": 0.5, "ghost": 0.0, "steel": 0.5},
    "fire": {"fire": 0.5, "water": 0.5, "grass": 2.0, "ice": 2.0, "bug": 2.0,
             "rock": 0.5, "dragon": 0.5, "steel": 2.0},
    "water": {"fire": 2.0, "water": 0.5, "grass": 0.5, "ground": 2.0,
              "rock": 2.0, "dragon": 0.5},
    "grass": {"fire": 0.5, "water": 2.0, "grass": 0.5, "poison": 0.5,
              "ground": 2.0, "flying": 0.5, "bug": 0.5, "rock": 2.0,
              "dragon": 0.5, "steel": 0.5},
    "electric": {"water": 2.0, "electric": 0.5, "ground": 0.0,
                 "flying": 2.0, "dragon": 0.5},
    "ice": {"fire": 0.5, "water": 0.5, "grass": 2.0, "ice": 0.5,
            "ground": 2.0, "flying": 2.0, "dragon": 2.0, "steel": 0.5},
    "fighting": {"normal": 2.0, "ice": 2.0, "rock": 2.0, "dark": 2.0,
                 "steel": 2.0, "poison": 0.5, "flying": 0.5,
                 "psychic": 0.5, "bug": 0.5, "ghost": 0.0, "fairy": 0.5},
    "poison": {"grass": 2.0, "fairy": 2.0, "poison": 0.5, "ground": 0.5,
               "rock": 0.5, "ghost": 0.5, "steel": 0.0},
    "ground": {"fire": 2.0, "electric": 2.0, "grass": 0.5, "poison": 2.0,
               "flying": 0.0, "bug": 0.5, "rock": 2.0, "steel": 2.0},
    "flying": {"electric": 0.5, "grass": 2.0, "fighting": 2.0, "bug": 2.0,
               "rock": 0.5, "steel": 0.5},
    "psychic": {"fighting": 2.0, "poison": 2.0, "psychic": 0.5,
                "dark": 0.0, "steel": 0.5},
    "bug": {"fire": 0.5, "grass": 2.0, "fighting": 0.5, "poison": 0.5,
            "flying": 0.5, "psychic": 2.0, "ghost": 0.5, "dark": 2.0,
            "steel": 0.5, "fairy": 0.5},
    "rock": {"fire": 2.0, "ice": 2.0, "flying": 2.0, "bug": 2.0,
             "fighting": 0.5, "ground": 0.5, "steel": 0.5},
    "ghost": {"normal": 0.0, "psychic": 2.0, "ghost": 2.0, "dark": 0.5},
    "dragon": {"dragon": 2.0, "steel": 0.5, "fairy": 0.0},
    "dark": {"fighting": 0.5, "psychic": 2.0, "ghost": 2.0, "dark": 0.5,
             "fairy": 0.5},
    "steel": {"fire": 0.5, "water": 0.5, "electric": 0.5, "ice": 2.0,
              "rock": 2.0, "steel": 0.5, "fairy": 2.0},
    "fairy": {"fire": 0.5, "fighting": 2.0, "poison": 0.5, "dragon": 2.0,
              "dark": 2.0, "steel": 0.5}
}


def types(move_type: str, defender_types: List[str]) -> float:
    mult = 1.0
    for t in defender_types:
        mult *= TYPE_CHART.get(move_type, {}).get(t, 1.0)
    return mult


def damage(attacker: dict, defender: dict, move: dict) -> int:
    power = move.get("power", 40) or 40
    attack = attacker["stats"]["attack"]
    defense = defender["stats"]["defense"]
    mult = types(move["type"], defender["types"])
    dmg = int((((2 * 50 / 5 + 2) * power * attack / defense) / 50 + 2) * mult)
    return max(1, dmg)


def apply_status_effects(pokemon: dict, log: List[str]) -> bool:
    if pokemon.get("status") == "paralysis":
        if random.random() < 0.25:
            log.append(f"{pokemon['name']} is paralyzed! It can't move!")
            return True
    if pokemon.get("status") == "burn":
        dmg = max(1, int(pokemon["stats"]["hp"] * 0.1))
        pokemon["hp"] -= dmg
        log.append(f"{pokemon['name']} is hurt by its burn ({dmg} HP)!")
    if pokemon.get("status") == "poison":
        dmg = max(1, int(pokemon["stats"]["hp"] * 0.12))
        pokemon["hp"] -= dmg
        log.append(f"{pokemon['name']} is hurt by poison ({dmg} HP)!")
    return False


def infer_moves(move: dict) -> str:
    n = move["name"].lower()
    if any(k in n for k in ["thunder", "bolt", "zap"]):
        return "paralysis"
    if any(k in n for k in ["ember", "flame", "fire", "burn"]):
        return "burn"
    if any(k in n for k in ["poison", "toxic"]):
        return "poison"
    return None


def simulate(A, B, seed=None, max_turns=100):
    if seed is not None:
        random.seed(seed)

    A = A.copy(); B = B.copy()
    A["hp"] = A["stats"]["hp"]
    B["hp"] = B["stats"]["hp"]

    log = []

    for turn in range(max_turns):
        if A["hp"] <= 0 or B["hp"] <= 0:
            break

        log.append(f"--- Turn {turn+1} ---")

        order = sorted([A, B], key=lambda p: p["stats"]["speed"], reverse=True)

        for attacker in order:
            defender = B if attacker is A else A
            if attacker["hp"] <= 0 or defender["hp"] <= 0:
                continue

            if apply_status_effects(attacker, log):
                continue

            move = random.choice(attacker["moves"])
            dmg = damage(attacker, defender, move)
            defender["hp"] -= dmg
            log.append(f"{attacker['name']} used {move['name']} → {defender['name']} lost {dmg} HP!")

            status = infer_moves(move)
            if status and not defender.get("status"):
                defender["status"] = status
                log.append(f"{defender['name']} is now affected by {status}!")

            if defender["hp"] <= 0:
                log.append(f"{defender['name']} fainted!")
                return {"winner": attacker["name"], "log": log}

  
    if A["hp"] > B["hp"]:
        winner = A["name"]
    elif B["hp"] > A["hp"]:
        winner = B["name"]
    else:
        winner = "Draw"

    return {"winner": winner, "log": log}
