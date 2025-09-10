 # make a new file test_battle.py
 
import pkmon_core.battle as battle


A = {
    "name": "venusaur",
    "stats": {
        "hp": 80,
        "attack": 82,
        "defense": 83,
        "special-attack": 100,
        "special-defense": 100,
        "speed": 80,
    },
    "types": ["grass", "poison"],
    "moves": [
        {"name": "razor-leaf", "type": "grass", "power": 55},
        {"name": "sludge-bomb", "type": "poison", "power": 90},
    ],
    "hp": 80,  
}

B = {
    "name": "blastoise",
    "stats": {
        "hp": 79,
        "attack": 83,
        "defense": 100,
        "special-attack": 85,
        "special-defense": 105,
        "speed": 78,
    },
    "types": ["water"],
    "moves": [
        {"name": "hydro-pump", "type": "water", "power": 110},
        {"name": "mega-punch", "type": "normal", "power": 80},
    ],
    "hp": 79,  \
}


result = battle.simulate(A, B, seed=42)

print("Winner:", result["winner"])
print("\n".join(result["log"][:50]))
