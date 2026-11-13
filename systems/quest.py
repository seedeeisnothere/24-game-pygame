# Quests: the objective shown bottom-right. The story gives them out one
# after another (see the "Story" section of scenes/overworld_scene.py).
#   text    = what the tracker shows
#   target  = enemy kind that counts as progress (None = finished by the story)
#   goal    = how many
#   turn_in = hint shown once done (None = clears itself a few seconds later)
HEADMAN_HINT = "Talk to the Village Headman"

QUESTS = {
    "find_fuel": {
        "text": "Ask the villagers for fuel",
        "target": None, "goal": 1, "turn_in": None,
    },
    "slime_hunt": {
        "text": "Kill slimes under the big tree",
        "target": "slime", "goal": 5, "turn_in": HEADMAN_HINT,
    },
    "forest_boss": {
        "text": "Upgrade yourself and defeat the Crimson Warden",
        "target": "boss_forest", "goal": 1, "turn_in": HEADMAN_HINT,
    },
    "cave_boss": {
        "text": "Defeat the monster in the cave",
        "target": "boss_cave", "goal": 1, "turn_in": HEADMAN_HINT,
    },
    "go_to_ship": {
        "text": "Go back to your ship",
        "target": None, "goal": 1, "turn_in": None,
    },
    "final_boss": {
        "text": "Defeat Jenny",
        "target": "boss_final", "goal": 1, "turn_in": None,
    },
}


class Quest:
    def __init__(self, quest_id):
        data = QUESTS[quest_id]
        self.id = quest_id
        self.text = data["text"]
        self.target = data["target"]
        self.goal = data["goal"]
        self.turn_in = data["turn_in"]
        self.progress = 0
        self.done_time = 0.0        # seconds since completed (for auto clear)

    @property
    def complete(self):
        return self.progress >= self.goal

    @property
    def remaining(self):
        return max(0, self.goal - self.progress)

    # Count a defeated enemy if it's the kind this quest wants.
    def record_kill(self, kind):
        if self.target and kind == self.target and not self.complete:
            self.progress += 1
