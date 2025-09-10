import streamlit as st
import json
import requests
from typing import Dict, List, Optional
import time
import random
from tenacity import retry, wait_exponential, stop_after_attempt
from pkmon_core.battle import simulate, TYPE_CHART
from pkmon_core.server import fetch_pokemon_data, build_moves_with_effects


st.set_page_config(
    page_title="Pokémon Battle Simulator",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
<style>
    .pokemon-card {
        border: 2px solid #ddd;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .battle-log {
        background-color: #1e1e1e;
        color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        max-height: 400px;
        overflow-y: auto;
        border: 2px solid #333;
    }
    .winner-announcement {
        text-align: center;
        font-size: 2em;
        font-weight: bold;
        color: #ff6b6b;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        margin: 20px 0;
    }
    .type-badge {
        display: inline-block;
        padding: 4px 8px;
        margin: 2px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: bold;
        color: white;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    .stats-bar {
        background-color: #e0e0e0;
        border-radius: 10px;
        overflow: hidden;
        margin: 5px 0;
    }
    .stats-fill {
        height: 20px;
        border-radius: 10px;
        transition: width 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)


FALLBACK_POKEMON = {
    "pikachu": {
        "name": "pikachu",
        "types": ["electric"],
        "stats": {"hp": 35, "attack": 55, "defense": 40, "special-attack": 50, "special-defense": 50, "speed": 90},
        "moves": [
            {"name": "thunder-shock", "type": "electric", "power": 40},
            {"name": "quick-attack", "type": "normal", "power": 40},
            {"name": "thunderbolt", "type": "electric", "power": 90},
            {"name": "iron-tail", "type": "steel", "power": 100}
        ]
    },
    "charizard": {
        "name": "charizard",
        "types": ["fire", "flying"],
        "stats": {"hp": 78, "attack": 84, "defense": 78, "special-attack": 109, "special-defense": 85, "speed": 100},
        "moves": [
            {"name": "flamethrower", "type": "fire", "power": 90},
            {"name": "dragon-claw", "type": "dragon", "power": 80},
            {"name": "air-slash", "type": "flying", "power": 75},
            {"name": "fire-blast", "type": "fire", "power": 110}
        ]
    },
    "blastoise": {
        "name": "blastoise",
        "types": ["water"],
        "stats": {"hp": 79, "attack": 83, "defense": 100, "special-attack": 85, "special-defense": 105, "speed": 78},
        "moves": [
            {"name": "hydro-pump", "type": "water", "power": 110},
            {"name": "ice-beam", "type": "ice", "power": 90},
            {"name": "mega-punch", "type": "normal", "power": 80},
            {"name": "surf", "type": "water", "power": 90}
        ]
    },
    "venusaur": {
        "name": "venusaur",
        "types": ["grass", "poison"],
        "stats": {"hp": 80, "attack": 82, "defense": 83, "special-attack": 100, "special-defense": 100, "speed": 80},
        "moves": [
            {"name": "razor-leaf", "type": "grass", "power": 55},
            {"name": "sludge-bomb", "type": "poison", "power": 90},
            {"name": "solar-beam", "type": "grass", "power": 120},
            {"name": "earthquake", "type": "ground", "power": 100}
        ]
    },
    "snorlax": {
        "name": "snorlax",
        "types": ["normal"],
        "stats": {"hp": 160, "attack": 110, "defense": 65, "special-attack": 65, "special-defense": 110, "speed": 30},
        "moves": [
            {"name": "body-slam", "type": "normal", "power": 85},
            {"name": "rest", "type": "psychic", "power": None},
            {"name": "hyper-beam", "type": "normal", "power": 150},
            {"name": "earthquake", "type": "ground", "power": 100}
        ]
    },
    "mewtwo": {
        "name": "mewtwo",
        "types": ["psychic"],
        "stats": {"hp": 106, "attack": 110, "defense": 90, "special-attack": 154, "special-defense": 90, "speed": 130},
        "moves": [
            {"name": "psychic", "type": "psychic", "power": 90},
            {"name": "shadow-ball", "type": "ghost", "power": 80},
            {"name": "thunderbolt", "type": "electric", "power": 90},
            {"name": "ice-beam", "type": "ice", "power": 90}
        ]
    },
    "mew": {
        "name": "mew",
        "types": ["psychic"],
        "stats": {"hp": 100, "attack": 100, "defense": 100, "special-attack": 100, "special-defense": 100, "speed": 100},
        "moves": [
            {"name": "psychic", "type": "psychic", "power": 90},
            {"name": "thunderbolt", "type": "electric", "power": 90},
            {"name": "flamethrower", "type": "fire", "power": 90},
            {"name": "ice-beam", "type": "ice", "power": 90}
        ]
    },
    "lucario": {
        "name": "lucario",
        "types": ["fighting", "steel"],
        "stats": {"hp": 70, "attack": 110, "defense": 70, "special-attack": 115, "special-defense": 70, "speed": 90},
        "moves": [
            {"name": "aura-sphere", "type": "fighting", "power": 80},
            {"name": "close-combat", "type": "fighting", "power": 120},
            {"name": "flash-cannon", "type": "steel", "power": 80},
            {"name": "dragon-pulse", "type": "dragon", "power": 85}
        ]
    },
    "garchomp": {
        "name": "garchomp",
        "types": ["dragon", "ground"],
        "stats": {"hp": 108, "attack": 130, "defense": 95, "special-attack": 80, "special-defense": 85, "speed": 102},
        "moves": [
            {"name": "dragon-claw", "type": "dragon", "power": 80},
            {"name": "earthquake", "type": "ground", "power": 100},
            {"name": "stone-edge", "type": "rock", "power": 100},
            {"name": "fire-blast", "type": "fire", "power": 110}
        ]
    },
    "dragonite": {
        "name": "dragonite",
        "types": ["dragon", "flying"],
        "stats": {"hp": 91, "attack": 134, "defense": 95, "special-attack": 100, "special-defense": 100, "speed": 80},
        "moves": [
            {"name": "dragon-claw", "type": "dragon", "power": 80},
            {"name": "hurricane", "type": "flying", "power": 110},
            {"name": "thunderbolt", "type": "electric", "power": 90},
            {"name": "ice-beam", "type": "ice", "power": 90}
        ]
    },
    "tyranitar": {
        "name": "tyranitar",
        "types": ["rock", "dark"],
        "stats": {"hp": 100, "attack": 134, "defense": 110, "special-attack": 95, "special-defense": 100, "speed": 61},
        "moves": [
            {"name": "stone-edge", "type": "rock", "power": 100},
            {"name": "crunch", "type": "dark", "power": 80},
            {"name": "earthquake", "type": "ground", "power": 100},
            {"name": "fire-blast", "type": "fire", "power": 110}
        ]
    },
    "metagross": {
        "name": "metagross",
        "types": ["steel", "psychic"],
        "stats": {"hp": 80, "attack": 135, "defense": 130, "special-attack": 95, "special-defense": 90, "speed": 70},
        "moves": [
            {"name": "meteor-mash", "type": "steel", "power": 90},
            {"name": "psychic", "type": "psychic", "power": 90},
            {"name": "earthquake", "type": "ground", "power": 100},
            {"name": "thunder-punch", "type": "electric", "power": 75}
        ]
    },
    "gengar": {
        "name": "gengar",
        "types": ["ghost", "poison"],
        "stats": {"hp": 60, "attack": 65, "defense": 60, "special-attack": 130, "special-defense": 75, "speed": 110},
        "moves": [
            {"name": "shadow-ball", "type": "ghost", "power": 80},
            {"name": "sludge-bomb", "type": "poison", "power": 90},
            {"name": "thunderbolt", "type": "electric", "power": 90},
            {"name": "psychic", "type": "psychic", "power": 90}
        ]
    },
    "alakazam": {
        "name": "alakazam",
        "types": ["psychic"],
        "stats": {"hp": 55, "attack": 50, "defense": 45, "special-attack": 135, "special-defense": 95, "speed": 120},
        "moves": [
            {"name": "psychic", "type": "psychic", "power": 90},
            {"name": "shadow-ball", "type": "ghost", "power": 80},
            {"name": "thunderbolt", "type": "electric", "power": 90},
            {"name": "ice-beam", "type": "ice", "power": 90}
        ]
    },
    "machamp": {
        "name": "machamp",
        "types": ["fighting"],
        "stats": {"hp": 90, "attack": 130, "defense": 80, "special-attack": 65, "special-defense": 85, "speed": 55},
        "moves": [
            {"name": "close-combat", "type": "fighting", "power": 120},
            {"name": "stone-edge", "type": "rock", "power": 100},
            {"name": "earthquake", "type": "ground", "power": 100},
            {"name": "thunder-punch", "type": "electric", "power": 75}
        ]
    },
    "gyarados": {
        "name": "gyarados",
        "types": ["water", "flying"],
        "stats": {"hp": 95, "attack": 125, "defense": 79, "special-attack": 60, "special-defense": 100, "speed": 81},
        "moves": [
            {"name": "waterfall", "type": "water", "power": 80},
            {"name": "dragon-dance", "type": "dragon", "power": None},
            {"name": "earthquake", "type": "ground", "power": 100},
            {"name": "ice-fang", "type": "ice", "power": 65}
        ]
    },
    "lapras": {
        "name": "lapras",
        "types": ["water", "ice"],
        "stats": {"hp": 130, "attack": 85, "defense": 80, "special-attack": 85, "special-defense": 95, "speed": 60},
        "moves": [
            {"name": "surf", "type": "water", "power": 90},
            {"name": "ice-beam", "type": "ice", "power": 90},
            {"name": "thunderbolt", "type": "electric", "power": 90},
            {"name": "psychic", "type": "psychic", "power": 90}
        ]
    },
    "arcanine": {
        "name": "arcanine",
        "types": ["fire"],
        "stats": {"hp": 90, "attack": 110, "defense": 80, "special-attack": 100, "special-defense": 80, "speed": 95},
        "moves": [
            {"name": "flamethrower", "type": "fire", "power": 90},
            {"name": "thunder-fang", "type": "electric", "power": 65},
            {"name": "crunch", "type": "dark", "power": 80},
            {"name": "extreme-speed", "type": "normal", "power": 80}
        ]
    },
    "ninetales": {
        "name": "ninetales",
        "types": ["fire"],
        "stats": {"hp": 73, "attack": 76, "defense": 75, "special-attack": 81, "special-defense": 100, "speed": 100},
        "moves": [
            {"name": "flamethrower", "type": "fire", "power": 90},
            {"name": "solar-beam", "type": "grass", "power": 120},
            {"name": "psychic", "type": "psychic", "power": 90},
            {"name": "shadow-ball", "type": "ghost", "power": 80}
        ]
    },
    "raichu": {
        "name": "raichu",
        "types": ["electric"],
        "stats": {"hp": 60, "attack": 90, "defense": 55, "special-attack": 90, "special-defense": 80, "speed": 110},
        "moves": [
            {"name": "thunderbolt", "type": "electric", "power": 90},
            {"name": "brick-break", "type": "fighting", "power": 75},
            {"name": "iron-tail", "type": "steel", "power": 100},
            {"name": "quick-attack", "type": "normal", "power": 40}
        ]
    },
    "machoke": {
        "name": "machoke",
        "types": ["fighting"],
        "stats": {"hp": 80, "attack": 100, "defense": 70, "special-attack": 50, "special-defense": 60, "speed": 45},
        "moves": [
            {"name": "karate-chop", "type": "fighting", "power": 50},
            {"name": "low-kick", "type": "fighting", "power": 60},
            {"name": "seismic-toss", "type": "fighting", "power": 100},
            {"name": "thunder-punch", "type": "electric", "power": 75}
        ]
    },
    "haunter": {
        "name": "haunter",
        "types": ["ghost", "poison"],
        "stats": {"hp": 45, "attack": 50, "defense": 45, "special-attack": 115, "special-defense": 55, "speed": 95},
        "moves": [
            {"name": "shadow-ball", "type": "ghost", "power": 80},
            {"name": "sludge-bomb", "type": "poison", "power": 90},
            {"name": "thunderbolt", "type": "electric", "power": 90},
            {"name": "psychic", "type": "psychic", "power": 90}
        ]
    },
    "kadabra": {
        "name": "kadabra",
        "types": ["psychic"],
        "stats": {"hp": 40, "attack": 35, "defense": 30, "special-attack": 120, "special-defense": 70, "speed": 105},
        "moves": [
            {"name": "psychic", "type": "psychic", "power": 90},
            {"name": "shadow-ball", "type": "ghost", "power": 80},
            {"name": "thunderbolt", "type": "electric", "power": 90},
            {"name": "ice-beam", "type": "ice", "power": 90}
        ]
    }
}

def get_type_color(type_name: str) -> str:
    """Return a color for each Pokémon type"""
    colors = {
        "normal": "#A8A878", "fire": "#F08030", "water": "#6890F0", "grass": "#78C850",
        "electric": "#F8D030", "ice": "#98D8D8", "fighting": "#C03028", "poison": "#A040A0",
        "ground": "#E0C068", "flying": "#A890F0", "psychic": "#F85888", "bug": "#A8B820",
        "rock": "#B8A038", "ghost": "#705898", "dragon": "#7038F8", "dark": "#705848",
        "steel": "#B8B8D0", "fairy": "#EE99AC"
    }
    return colors.get(type_name.lower(), "#68A090")

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
def fetch_pokemon_with_retry(name: str) -> dict:
    """Fetch Pokémon data with retry logic and longer timeout."""
    try:
       
        session = requests.Session()
        session.timeout = 30 
        url = f"https://pokeapi.co/api/v2/pokemon/{name.lower()}"
        response = session.get(url, timeout=30)
        if response.status_code != 200:
            raise ValueError(f"Could not fetch data for {name}")
        return response.json()
    except Exception as e:
        st.warning(f"API fetch failed for {name}: {str(e)}. Using fallback data...")
        raise e

def battle_pokemon(name: str, use_fallback_only: bool = False) -> dict:
    """Builds a Pokémon object suitable for the battle engine from PokéAPI with fallback."""
    
    if name.lower() in FALLBACK_POKEMON:
        fallback_data = FALLBACK_POKEMON[name.lower()].copy()
        if use_fallback_only:
            st.info(f"Using fallback data for {name.title()}")
        return fallback_data
    
   
    if use_fallback_only:
        for fallback_name, fallback_data in FALLBACK_POKEMON.items():
            if name.lower() in fallback_name or fallback_name in name.lower():
                st.info(f"Using similar fallback data ({fallback_name}) for {name}")
                return fallback_data.copy()
        st.warning(f"No fallback data available for {name}. Using Pikachu as default.")
        return FALLBACK_POKEMON["pikachu"].copy()
    
    
    try:
        data = fetch_pokemon_with_retry(name)
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
    except Exception as e:
        st.warning(f"Failed to fetch {name} from API: {str(e)}")
        
        for fallback_name, fallback_data in FALLBACK_POKEMON.items():
            if name.lower() in fallback_name or fallback_name in name.lower():
                st.info(f"Using similar fallback data ({fallback_name}) for {name}")
                return fallback_data.copy()
        
        
        st.warning(f"No fallback data available for {name}. Using Pikachu as default.")
        return FALLBACK_POKEMON["pikachu"].copy()

def pokemon_card(pokemon: dict, title: str):
    """Display a Pokémon card with stats and info"""
    if not pokemon:
        st.error(f"Failed to load {title}")
        return
    
    with st.container():
        st.markdown(f"### {title}")
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**{pokemon['name'].title()}**")
        with col2:
            for type_name in pokemon['types']:
                color = get_type_color(type_name)
                st.markdown(f'<span class="type-badge" style="background-color: {color}">{type_name.title()}</span>', 
                           unsafe_allow_html=True)
        
        
        st.markdown("**Base Stats:**")
        for stat_name, value in pokemon['stats'].items():
            max_stat = 150  
            percentage = min((value / max_stat) * 100, 100)
            color = "#4CAF50" if value >= 100 else "#FF9800" if value >= 70 else "#F44336"
            
            st.markdown(f"""
            <div class="stats-bar">
                <div class="stats-fill" style="width: {percentage}%; background-color: {color};">
                    {stat_name.replace('-', ' ').title()}: {value}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("**Moves:**")
        moves_text = ", ".join([move['name'].replace('-', ' ').title() for move in pokemon['moves'][:4]])
        st.markdown(f"*{moves_text}*")

def battle_log(log: List[str]):
    """Display the battle log with proper formatting"""
    with st.container():
        st.markdown("### Battle Log")
        log_html = "<div class='battle-log'>"
        for line in log:
            if "Turn" in line:
                log_html += f"<div style='color: #FFD700; font-weight: bold; margin: 10px 0;'>{line}</div>"
            elif "fainted" in line.lower():
                log_html += f"<div style='color: #FF6B6B; font-weight: bold;'>{line}</div>"
            elif "used" in line and "→" in line:
                log_html += f"<div style='color: #4ECDC4;'>{line}</div>"
            elif "hurt by" in line.lower() or "affected by" in line.lower():
                log_html += f"<div style='color: #FFA07A;'>{line}</div>"
            else:
                log_html += f"<div>{line}</div>"
        log_html += "</div>"
        st.markdown(log_html, unsafe_allow_html=True)



def main():
    st.title("⚔️ Pokémon Battle Simulator")
    st.markdown("Choose two Pokémon and watch them battle it out!")
    
    with st.sidebar:
        st.header("🎮 Battle Setup")
        
       
        popular_pokemon = [
            "pikachu", "charizard", "blastoise", "venusaur", "mewtwo", "mew",
            "lucario", "garchomp", "dragonite", "tyranitar", "metagross",
            "gengar", "alakazam", "machamp", "gyarados", "lapras", "snorlax",
            "arcanine", "ninetales", "raichu", "machoke", "haunter", "kadabra"
        ]
        
        st.subheader("Select Pokémon")
        pokemon1_name = st.selectbox("Pokémon 1:", popular_pokemon, index=0)
        pokemon2_name = st.selectbox("Pokémon 2:", popular_pokemon, index=2)
        
        
        st.subheader("Battle Options")
        max_turns = st.slider("Max Turns:", 10, 100, 20)
        use_seed = st.checkbox("Use Random Seed", value=False)
        seed = None
        if use_seed:
            seed = st.number_input("Seed:", value=42, min_value=0, max_value=500)

        st.subheader("Data Source")
        use_fallback = st.checkbox("Use Fallback Data Only", value=False, 
                                 help="Check this if you're experiencing API timeout issues")

        battle_button = st.button("⚔️ START BATTLE!", type="primary", use_container_width=True)
    

    if battle_button:
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.text("Loading Pokémon 1..")
        progress_bar.progress(25)
        pokemon1 = battle_pokemon(pokemon1_name, use_fallback_only=use_fallback)
        
        status_text.text("Loading Pokémon 2...")
        progress_bar.progress(50)
        pokemon2 = battle_pokemon(pokemon2_name, use_fallback_only=use_fallback)
        
        status_text.text("Preparing battle..")
        progress_bar.progress(75)
        
        if pokemon1 and pokemon2:
       
            progress_bar.progress(100)
            status_text.text("Battle ready!")
            time.sleep(0.5) 
            progress_bar.empty()
            status_text.empty()

            col1, col2 = st.columns(2)
            
            with col1:
                pokemon_card(pokemon1, "Pokémon 1")
            
            with col2:
                pokemon_card(pokemon2, "Pokémon 2")

            st.markdown("---")
            st.markdown("### ⚔️ Battle Simulation")
            
            with st.spinner("Simulating battle..."):
                result = simulate(pokemon1, pokemon2, seed=seed, max_turns=max_turns)
            
            winner = result["winner"]
            if winner != "Draw":
                st.markdown(f'<div class="winner-announcement">🏆 {winner.title()} Wins! 🏆</div>', 
                           unsafe_allow_html=True)
            else:
                st.markdown('<div class="winner-announcement">🤝 It\'s a Draw! 🤝</div>', 
                           unsafe_allow_html=True)
            battle_log(result["log"])

            st.markdown("### 📊 Battle Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Turns", len([line for line in result["log"] if "Turn" in line]))
            
            with col2:
                moves_used = len([line for line in result["log"] if "used" in line])
                st.metric("Moves Used", moves_used)
            
            with col3:
                status_effects = len([line for line in result["log"] if "affected by" in line])
                st.metric("Status Effects", status_effects)
        else:
            st.error("Failed to load one or both Pokémon. Please try again.")

    st.markdown("---")
   
if __name__ == "__main__":
    main()

