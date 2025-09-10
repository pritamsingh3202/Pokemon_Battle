
# Pokémon MCP Server  Data Resource + Battle Simulation Tool

## Overview

This project implements an MCP (Model Context Protocol) server that provides AI models with access to two key capabilities:

1- Pokémon Data Resource – a resource that exposes comprehensive Pokémon data from the public PokéAPI ( https://pokeapi.co/ ).

2- Battle Simulation Tool – a tool that simulates battles between any two Pokémon, including type effectiveness, stats-based damage, turn order, and basic status effects.

This server acts as a bridge between AI and the Pokémon world, enabling LLMs to both retrieve knowledge and interactively simulate battles.

## Part 1: Pokémon Data Resource

### Implementation

- Connects to the public PokéAPI ( https://pokeapi.co/  )
  
- Exposes comprehensive Pokémon information including:
- Base stats: HP, Attack, Defense, Special Attack, Special Defense, Speed
- Types (e.g., Fire, Water, Grass)
- Abilities
- Available moves and their effects (power, accuracy, type, effect text)
- Evolution information


### MCP Resource

- Resource: pokemon://{name}
- Returns JSON including stats, types, abilities, moves (with effects), and evolution chain.
- Implements MCP resource design patterns to make this data accessible to LLMs.


### Deliverables

- Code for the MCP server with the Pokémon data resource.
- Documentation (this README) describing how the resource exposes data.
- Example queries (examples/llm_examples.md).


## Part 2: Battle Simulation Tool

### Implementation

- Tool: simulate_battle(pokemon_a, pokemon_b, max_turns=100, seed=None)

- Simulates a battle between any two Pokémon using:
- Type effectiveness calculations (e.g., Water > Fire)
- Damage calculations based on stats and move power
- Turn order based on Speed stat

### Status effects:
- Paralysis – chance to skip a turn
- Burn – recurring HP loss
- Poison – recurring HP loss
- Detailed battle logs showing each turn’s actions and outcomes
- Winner determination (first Pokémon to faint, or higher HP after max turns)


### MCP Tool


- Exposed via MCP as a callable tool: simulate_battle
- Returns JSON object, e.g.:
```json
{
  "winner": "blastoise",
  "log": [
    "--- Turn 1 ---",
    "charizard used fire-punch → blastoise lost 14 HP!",
    "blastoise is now affected by burn!",
    ...
  ]
}
```



### Deliverables

-  Code for the battle simulation tool following MCP tool specification
-  Example usage in examples/llm_examples.md

#### Requirements


- Python 3.10+
- Virtual environment recommended

```bash
python -m pkmon_core.server
```

Note: The server runs in stdio mode and will appear idle, waiting for an MCP client. Stop with Ctrl+C.


#### Expected output:

- JSON data for Pikachu (types, stats, moves, evolution chain)
- Battle log with turn-by-turn actions and a winner (e.g., Blastoise)


### Examples for LLM Usage

See examples/llm_examples.md for prompt examples, such as:

- Summarizing a Pokémon’s stats, moves, and evolution
- Simulating a battle and explaining why the winner won

See [`examples/llm_examples.md`](examples/llm_examples.md) for prompt examples.

### Notes

- Simplified mechanics: ignores PP, items, weather, etc.
- Focused on clarity and educational battle simulation
- Easily extensible to add more mechanics


``
# Pokémon Battle Simulator - Streamlit App

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Streamlit App**
   ```bash
   streamlit run streamlit_app.py
   ```

3. **Open Your Browser** 

   - The app will automatically open in your default browser
   - If not, navigate to `http://localhost:8501`

## Features

- **Pokémon Selection**: Choose from 24 popular Pokémon
- **Real-time Battle Simulation**: Watch battles unfold with detailed logs
- **Visual Stats Display**: See each Pokémon's stats with color-coded bars
- **Type Effectiveness**: Full type chart implementation
- **Status Effects**: Paralysis, burn, and poison effects
- **Battle Statistics**: Turn count, moves used, and status effects

## Technical Details

- Built with Streamlit for the web interface
- Uses the existing `pkmon_core` battle system
- Fetches real Pokémon data from PokéAPI
- Implements full type effectiveness calculations
- Supports status effects and turn-based combat

## Troubleshooting

- If Pokémon data fails to load, check your internet connection.
- The app requires Python 3.10+ and all dependencies from requirements.txt
- Make sure you're in the correct directory when running the command.