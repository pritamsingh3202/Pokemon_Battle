import pkmon_core.server as s
import json

def test_pokemon_resource():
    # Fetch Pokémon data into .json (e.g., Pikachu, Bulbasaur, Venusaur, Blastoise, Charmander)
    data = s.get_pokemon("Blastoise")
    parsed = json.loads(data)
    assert "stats" in parsed, "Missing stats"
    assert "types" in parsed, "Missing types"
    assert "abilities" in parsed, "Missing abilities"
    assert "moves" in parsed, "Missing moves"
    assert "evolution_chain" in parsed, "Missing evolution chain"

    print("Resource test passed!")
    print(json.dumps(parsed, indent=2)[:400])  
if __name__ == "__main__":
    test_pokemon_resource()
