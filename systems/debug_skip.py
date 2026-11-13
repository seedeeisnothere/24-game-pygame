# TEMPORARY dev shortcut: press F9 in the overworld to skip the story up to
# the feature currently being tested. Delete this file and the two lines
# marked "DEBUG SKIP" in scenes/overworld_scene.py to remove it.
#
# Pressing it again resets to the same point, so a scene can be replayed.
import pygame

DEBUG_SKIP_KEY = pygame.K_F9

# Where F9 goes right now. Change it to any name in CHECKPOINTS below.
CHECKPOINT = "ship_repair"

# name: (what's done already, where you stand, what to do next)
#   boss_cutscene  slimes killed (5/5)            next to the headman  -> talk to him
#   forest_boss    Warden is out, fuel 1          below the Warden     -> walk up to it
#   forest_turn_in Warden beaten                  next to the headman  -> talk to him
#   cave_boss      cave quest taken, fuel 2       in the cave          -> walk up the bridge
#   cave_turn_in   cave monster beaten            next to the headman  -> talk to him
#   jenny          fuel 3, Jenny at the ship      right of the wreck   -> walk left to her
#   ship_repair    Jenny just beaten              where she stood      -> watch the repair
CHECKPOINTS = ["boss_cutscene", "forest_boss", "forest_turn_in",
               "cave_boss", "cave_turn_in", "jenny", "ship_repair"]


def skip_to_checkpoint(scene, checkpoint=None):
    from scenes.overworld_scene import OverworldScene, travel, WRECK_POS   # avoid a circular import
    from entities.wreck import Wreck
    checkpoint = checkpoint or CHECKPOINT
    stage = CHECKPOINTS.index(checkpoint)
    game = scene.game
    state = game.state
    scene.close_popups()

    # Both maps exist from here on, so their bosses can be set up.
    maps = {map_id: game.overworlds.get(map_id) or OverworldScene(game, map_id)
            for map_id in ("map1", "map2")}
    forest = maps["map1"]
    cave = maps["map2"]

    # --- story progress (fresh each time)
    state.has_gun = True
    state.quest = None
    state.finished_quests = {"find_fuel"}
    state.flags = {"forest_boss_appeared"} if stage >= 1 else set()
    state.fuel = 0

    def boss_state(map_scene, beaten):
        boss = map_scene.boss
        boss.defeated = beaten
        boss._respawn()
        if boss in map_scene.encounter.enemies:
            map_scene.encounter.enemies.remove(boss)

    boss_state(forest, beaten=stage >= 2)
    boss_state(cave, beaten=stage >= 4)
    jenny = forest.jenny_enemy
    jenny.defeated = checkpoint == "ship_repair"
    # Broken ship again (the repair cutscene swaps it for the fixed one).
    forest.wreck = Wreck(*WRECK_POS)

    def finish(*quest_ids):
        state.finished_quests.update(quest_ids)

    if checkpoint == "boss_cutscene":
        state.start_quest("slime_hunt")
        state.quest.progress = 5
    elif checkpoint in ("forest_boss", "forest_turn_in"):
        finish("slime_hunt")
        state.fuel = 1
        state.start_quest("forest_boss")
        state.quest.progress = 1 if checkpoint == "forest_turn_in" else 0
    elif checkpoint in ("cave_boss", "cave_turn_in"):
        finish("slime_hunt", "forest_boss")
        state.fuel = 2
        state.flags.add("cave_boss_appeared")
        state.start_quest("cave_boss")
        state.quest.progress = 1 if checkpoint == "cave_turn_in" else 0
    elif checkpoint in ("jenny", "ship_repair"):
        finish("slime_hunt", "forest_boss", "cave_boss")
        state.fuel = 3
        state.flags |= {"cave_boss_appeared", "jenny_at_ship"}
        if checkpoint == "jenny":
            state.start_quest("go_to_ship")
        else:
            finish("go_to_ship")
            state.flags |= {"jenny_met", "jenny_revealed"}
            state.start_quest("final_boss")

    # --- where to stand
    if checkpoint == "cave_boss":
        target = travel(game, "map2")
        boss = target.boss
        target.place_player((boss.rect.centerx, boss.rect.bottom + 330))
    else:
        target = travel(game, "map1")
        if checkpoint == "forest_boss":
            boss = target.boss
            target.place_player((boss.rect.centerx, boss.rect.bottom + 260))
        elif checkpoint == "jenny":
            feet = target.jenny.feet
            target.place_player((feet[0] + 330, feet[1]))
        elif checkpoint == "ship_repair":
            feet = target.jenny.feet
            target.place_player((feet[0] + 120, feet[1] + 40))
        else:
            headman = target.headman
            target.place_player((headman.hitbox.left - 30, headman.hitbox.centery))

    target.crash_fade = 0.0
    target.flash = 0.0
    target.intro = None
    target.intro_path = []
    target.repair = None
    target.repair_path = []
    target.battle_result = None
    if checkpoint == "ship_repair":
        # As if we just came back from beating her: outro line, then the repair.
        target.battle_result = (jenny, "win")
    for map_scene in maps.values():
        map_scene.sync_boss()
    forest.sync_jenny()
    target.update_camera()
    game.scene = target
    game.play_scene_music()
    print(f"[debug skip] -> {checkpoint}")
