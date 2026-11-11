# Base class for every scene; subclasses override these three hooks.
class Scene:
    def __init__(self, game):
        self.game = game

    def handle_events(self, events):
        pass

    def update(self, dt):
        pass

    def draw(self, screen):
        pass
