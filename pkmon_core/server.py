import json
import requests
from typing import Optional

from mcp.server.fastmcp import FastMCP
from mcp.server import stdio
from tenacity import retry, wait_exponential, stop_after_attempt


mcp = FastMCP("pkmon-core")



def fetch_json(url: str) -> dict:
    """Simple GET JSON with status check."""
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        raise ValueError(f"GET {url} -> {r.status_code}")
    return r.json()

def move_effect(mv: dict) -> Optional[str]:
    """Returns the effect text of a move from effect_entries (English)."""
    for e in mv.get("effect_entries", []):
        if e.get("language", {}).get("name") == "en":
            return e.get("short_effect") or e.get("effect")
    return None

def build_moves_with_effects(poke_json: dict, limit: int = 8) -> list[dict]:
    """Collects the first N moves (with power/accuracy/type) including effect text if available."""
    out = []
    for m in poke_json.get("moves", []):
        mv = fetch_json(m["move"]["url"])
        out.append({
            "name": mv["name"],
            "type": mv["type"]["name"],
            "power": mv.get("power"),
            "accuracy": mv.get("accuracy"),
            "effect": move_effect(mv),
            "effect_chance": mv.get("effect_chance"),
        })
        if len(out) >= limit:
            break
    if not out:
        return [{
            "name": "tackle", "type": "normal",
            "power": 40, "accuracy": 100,
            "effect": None, "effect_chance": None
        }]
    return out

def build_chain(species_json: dict) -> list[str]:
    """Extracts the evolution chain from species -> evolution_chain."""
    evo_url = species_json.get("evolution_chain", {}).get("url")
    if not evo_url:
        return []
    chain = fetch_json(evo_url).get("chain")
    names: list[str] = []

    def walk(node):
        if not node:
            return
        names.append(node["species"]["name"])
        for nxt in node.get("evolves_to", []):
            walk(nxt)

    walk(chain)
    seen, ordered = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            ordered.append(n)
    return ordered

POKEAPI_BASE = "https://pokeapi.co/api/v2/pokemon/"

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
def fetch_pokemon_data(name: str) -> dict:
    """Fetch Pokémon JSON from PokéAPI with retry."""
    url = f"{POKEAPI_BASE}{name.lower()}"
    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        raise ValueError(f"Could not fetch data for {name}")
    return resp.json()



@mcp.tool()
def ping(text: str = "pong") -> dict:
    """Simple test tool."""
    return {"echo": text}

@mcp.resource("hello://{name}")
def hello(name: str) -> str:
    """Test resource that returns a JSON greeting."""
    return json.dumps({"greeting": f"Hello, {name}!"}, indent=2)

@mcp.resource("pokemon://{name}")
def get_pokemon(name: str) -> str:
    """Resource: returns complete Pokémon data + moves effects + evolution chain."""
    data = fetch_pokemon_data(name)
    species = fetch_json(data["species"]["url"])
    info = {
        "name": data["name"],
        "id": data["id"],
        "height": data["height"],
        "weight": data["weight"],
        "types": [t["type"]["name"] for t in data["types"]],
        "stats": {s["stat"]["name"]: s["base_stat"] for s in data["stats"]},
        "abilities": [a["ability"]["name"] for a in data["abilities"]],
        "moves": build_moves_with_effects(data, limit=8),
        "evolution_chain": build_chain(species),
    }
    return json.dumps(info, indent=2)


from pkmon_core.battle import simulate   

def battle_pokemon(name: str) -> dict:
    """Builds a Pokémon object suitable for the battle engine from PokéAPI."""
    data = fetch_pokemon_data(name)
    moves = build_moves_with_effects(data, limit=8)
    raw = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}
    stats = {
        "hp": raw.get("hp", 50),
        "attack": raw.get("attack", 50),
        "defense": raw.get("defense", 50),
        "special-attack": raw.get("special-attack", raw.get("sp-attack", 50)),
        "special-defense": raw.get("special-defense", raw.get("sp-defense", 50)),
        "speed": raw.get("speed", 50),
    }
    return {
        "name": data["name"],
        "types": [t["type"]["name"] for t in data["types"]],
        "stats": stats,
        "moves": moves,
    }

@mcp.tool()
def simulate_battle(
    pokemon_a: str,
    pokemon_b: str,
    max_turns: int = 100,
    seed: Optional[int] = None,
) -> dict:
    """Runs a battle simulation between two Pokémon and returns the winner + log."""
    A = battle_pokemon(pokemon_a)
    B = battle_pokemon(pokemon_b)
    return simulate(A, B, seed=seed, max_turns=max_turns)


if __name__ == "__main__":
    print("✅ pkmon-core MCP Server started! Waiting for requests...")
    mcp.run()
