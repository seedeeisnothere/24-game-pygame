import random
from settings import *


class DodgeEvent:

    def __init__(self, lane_count):
        self.lane_count = lane_count
        self.attacks = []
        self.wave_delays = []
        self.attack_timer = random.uniform(*ATTACK_WAIT)
        self.results = []

    def clear(self):
        self.attacks = []
        self.wave_delays = []

    def start_wave(self):
        delays, t = [], 0.0
        for _ in range(random.choice(WAVE_SIZES)):
            delays.append(t)
            t += random.uniform(*ATTACK_GAP)
        self.wave_delays = delays
        self.attack_timer = random.uniform(*ATTACK_WAIT)

    def spawn_attack(self):
        used_keys = {a["key"] for a in self.attacks}
        used_lanes = {a["lane"] for a in self.attacks}
        keys = [k for k in DODGE_KEYS if k not in used_keys]
        lanes = [i for i in range(self.lane_count) if i not in used_lanes]
        if keys and lanes and len(self.attacks) < MAX_ATTACKS:
            self.attacks.append({"key": random.choice(keys), "left": DODGE_TIME,
                                 "lane": random.choice(lanes)})

    def press(self, letter):
        for attack in self.attacks:
            if attack["key"] == letter:
                self.attacks.remove(attack)
                self.results.append("dodged")
                return

    def update(self, dt):
        if not self.attacks and not self.wave_delays:
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.start_wave()

        self.wave_delays = [d - dt for d in self.wave_delays]
        while self.wave_delays and self.wave_delays[0] <= 0:
            self.wave_delays.pop(0)
            self.spawn_attack()

        for attack in list(self.attacks):
            attack["left"] -= dt
            if attack["left"] <= 0:
                self.attacks.remove(attack)
                self.results.append("hit")

    def consume_results(self):
        results = self.results
        self.results = []
        return results