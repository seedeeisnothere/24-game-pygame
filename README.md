# 24 Game

A pixel-art adventure made with pygame. Your spaceship crash-lands on a strange
planet where the classic **24 math puzzle** decides everything, even how your
gun shoots. Help the villagers, beat the monsters, collect three pieces of fuel,
fix your ship, and find out what happened to Jenny.

## How to run

You need Python 3.12+ and [pygame-ce](https://pyga.me/).

```bash
pip install pygame-ce
```

```bash
python3 main.py
```

Run it from the project folder, because asset and data paths are relative to it.

## How to play

### Overworld

| Key | Action |
| --- | --- |
| WASD / arrow keys | Walk |
| E | Talk to a nearby villager, or fight the enemy in front of you |
| Left click | Talk to a villager you click on |
| Space | Open the status / inventory menu |
| M | Open the map |
| Esc | Settings (volume, credits, back to title) |

### Battle

Each battle is a 24 puzzle. You get four numbers. Click a number, an operator
(+ − × ÷), then another number, and keep going until only one number is left.
If it's 24, your gun fires. Solving puzzles in a row builds a combo, and the
combo adds damage.

While you solve, the enemy attacks. Each attack shows a letter, and you have to
type that letter before the attack lands, or you lose 1 HP.

| Key | Action |
| --- | --- |
| Left click | Pick a number or operator |
| Right click | Reset the current puzzle |
| Letter keys | Dodge the attack with that letter |
| Q | Drink a healing potion |
| E | Use a skip ticket (new puzzle) |
| Esc | Run away |

### Shop

Beating enemies gives coins. The shopkeeper sells potions, skip tickets and
equipment that permanently raises your damage or max HP.

## Project layout

```
main.py              entry point
game.py              window, main loop, sounds, scene switching
settings.py          screen size, colors, file paths, tuning values

scenes/              title, overworld, battle, game over, ending
entities/            player, enemies, NPCs, gate, gun pickup, ship wreck
systems/             dialogue, quests, shop, inventory, HUD, minimap, tilemap,
                     audio, transitions, crash intro, UI widgets
logic/               the 24 puzzle rules and the puzzle bank

data/
  dialogue.json      every conversation, keyed by dialogue id
  enemies.json       enemy HP, coin rewards and battle tuning
  item.json          equipment and its stat bonuses
  shop.json          what each shop sells and for how much
  puzzles.json       24 puzzles, grouped by difficulty
  maps/              Tiled maps (map1 = village/forest, map2 = cave)

assets/              sprites, tiles, fonts, music and sound effects
tests/               unit tests
```

### Editing content

- **Dialogue:** add or change lines in `data/dialogue.json`. A line can have
  `"cue": "<name>"` to trigger an event (camera pan, fuel handover, and so on).
  Cues are handled in `OverworldScene.play_cue`.
- **Villagers:** add a `(sprite number, tile col, tile row)` entry to
  `VILLAGERS` in `scenes/overworld_scene.py`. The sprite is
  `assets/sprites/npc/NPC_<number>.png` and the dialogue id is `npc_<number>`.
- **Enemies, items, shops, puzzles:** edit the matching file in `data/`.

## Running the tests

```bash
PYTHONPATH=. python3 -m unittest discover -s tests
```

## Credits

See [CREDITS.md](CREDITS.md).
