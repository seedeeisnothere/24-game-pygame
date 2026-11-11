# Code Guide

A short map of how the game's code fits together. Start the game with `python main.py`.

## The big idea

The game is a top-down overworld. When an enemy catches you, a battle starts. In a battle you hit the enemy by solving **24 puzzles**: combine 4 numbers with + − × ÷ to make 24. At the same time you dodge attacks by typing letters. Winning gives coins, which you spend at a shop on items that boost HP or damage.

## Folders

| Folder | What's in it |
|---|---|
| `main.py`, `game.py` | Starting point, window, and the main loop |
| `settings.py` | All the constants: screen size, speeds, colours, file paths |
| `scenes/` | Whole screens: title, overworld, battle, game over |
| `entities/` | Things in the world: player sprite, enemies, NPCs, gates, the wreck |
| `logic/` | Pure game rules, no drawing: the 24 puzzle and the puzzle list |
| `systems/` | Reusable parts: UI, HUD, dialogue, shop, inventory, map loading, minimap |
| `data/` | JSON files: maps, enemies, items, shop stock, dialogue, puzzles |
| `tests/` | Unit tests for the logic: 24 solver, inventory, shop, enemy data |

## How the game runs

**1. Main loop** (`Game.run` in `game.py`). It runs once per frame, 60 times a second:
1. Measure `dt`, the seconds since the last frame. Everything moves by `speed * dt`, so the speed stays the same on fast and slow computers.
2. Read events (keys, mouse) and pass them to `scene.handle_events`.
3. `scene.update(dt)` changes the game state.
4. `scene.draw(screen)` draws it, then `pygame.display.flip()` shows the frame.

**2. Scenes** (`scenes/scene.py`). Every screen is a subclass of `Scene` with the same three methods: `handle_events`, `update` and `draw`. The `Game` object only ever talks to `self.scene`, so changing screens just means swapping that object. This is **polymorphism**: the loop doesn't care which scene it's running.

**3. Changing scenes** (`systems/transition.py`). `game.change_scene(...)` starts a `Curtain` that slides over the screen. Once the screen is fully covered, the new scene is created behind it and the curtain slides away. The curtain is a **state machine**: `idle → closing → covered → holding → opening → idle`.

**4. Order of screens:**
```
Title → (Start) → CrashIntro cutscene → Overworld ⇄ Battle
                                          ↓ lose
                                      Game Over → Title
```

## Key parts to know

**Overworld** (`scenes/overworld_scene.py`)
- **Map:** `systems/tilemap.py` reads a map made in the Tiled editor (JSON). It pre-draws the map into two big images: `below` is drawn under the player, `above` is drawn over them, for tree tops and roofs. Pre-drawing once is much faster than drawing every tile on every frame.
- **Collision:** the player has a small `hitbox` at their feet. It moves on X first, then on Y. If either move hits a wall, only that axis is undone, so you slide along walls instead of sticking to them.
- **Diagonal moves:** speed is multiplied by `3/4` so moving diagonally isn't faster than moving straight.
- **Camera:** follows the player but is clamped so it never shows past the map edge. Everything is drawn at `world position − camera`.
- **Maps:** `travel()` keeps visited maps in `game.overworlds`, so bosses, gates and enemies stay as you left them.

**Enemies** (`entities/enemy.py`)
- Each enemy is a state machine: `patrol → alert ("!") → chase → return`. Touching the player starts a battle.
- After winning or fleeing, the enemy is **stunned** for a few seconds so it doesn't catch you again straight away.
- `EnemySpawner` refills the coin-farm area with a new wave once you've beaten everyone and walked away.
- Beating a map's **boss** opens its `Gate`s.

**Battle** (`scenes/battle_scene.py`)
- **Attack:** click numbers and operators. `Game24` in `logic/game24.py` tracks the puzzle. When one number is left: 24 means you hit, anything else resets the puzzle.
- **Damage:** `combo + item damage bonus`. The combo goes up with fast solves and resets after a timer runs out.
- **Defend:** attacks appear in lanes, each with a letter. Type the letter before its timer runs out. A wrong letter makes the closest attack undodgeable.
- **Other keys:** Q drinks a potion, Esc flees, right-click resets the puzzle.
- **End of battle:** your HP is saved to `game.state`. Winning gives a random number of coins.

**The 24 solver** (`logic/game24.py`, `can_make`)
- It's **recursive**. Pick any two numbers and any operator, replace the pair with the result, and solve the shorter list. With one number left, check whether it equals 24.
- It uses `Fraction` instead of float so division is exact. For example, `8 / (3 - 8/3)` is exactly 24, with no rounding error.

**Player data** (`systems/game_state.py`)
- `GameState` holds coins, potions, HP and the `Inventory`. It survives scene changes because it lives on `game`, not on a scene.
- It stores **HP lost** instead of current HP. Then when an item raises max HP, your current HP stays correct automatically.
- `max_hp` and `damage_bonus` are `@property`s worked out from the equipped items.

**Shop and inventory** (`systems/shop.py`, `systems/inventory.py`)
- The buying rules (`Shop`) are kept separate from the drawing (`ShopMenu`). That's why the rules can be unit-tested without opening a window.
- Equipment can be bought once. Potions can be bought any number of times. You have 3 equip slots.

**Other systems:** `dialouge.py` (NPC text boxes with word wrap), `hud.py` (HP bar that slides smoothly, coin counter), `minimap.py` (small map that M expands, built from the map data), `crash_intro.py` (opening cutscene: the ship flies along a Bezier curve, then shake and a white flash), `ui.py` (buttons and sliders), `tween.py` (easing curves for smooth animation).

## Questions your professor might ask

- **Why use `dt`?** So movement and timers run at the same speed whatever the frame rate.
- **Why separate `logic/` from `scenes/`?** The rules have no pygame drawing in them, so they're easy to test and reuse.
- **How do scenes share data?** Through the single `Game` object: `game.state`, `game.overworlds` and the sounds.
- **What design patterns are used?** State machines (enemy, curtain, settings panel), polymorphism (scenes), data-driven design (enemies, items, shops and puzzles come from JSON, not code).
- **How is collision done?** Rectangle hitboxes checked against a set of solid tile cells, moving one axis at a time.
- **Why import `OverworldScene` inside a function in `title_scene.py`?** It's a "lazy import" that only runs when the intro ends. People often do this to avoid circular imports, where two modules import each other. There's no actual cycle right now, so moving it to the top of the file would also work.

## Known weak spots (be ready to discuss)

- `tests/test_enemies.py`: `test_every_enemy_is_valid` uses `enemy` before the loop that sets it, so it always crashes.
- `battle_scene.py` sets `player_hp` twice in `__init__`, and the first value is thrown away.
- `logic/dodge.py` seems unused. The battle reads attack settings from `data/enemies.json` instead.
- Enemies borrow the player's sprites as a placeholder.
