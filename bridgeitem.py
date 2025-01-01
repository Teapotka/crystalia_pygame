from config import *
from time import time

class BridgeItem(pygame.sprite.Sprite):

    def __init__(self, position, index, groups):
        super().__init__(groups)
        x, y = position
        self.index = index
        self.rect = pygame.Rect(x, y, 192, 64)
        self.image = pygame.image.load(join('assets', 'bridge', str(self.index) + 'item.png')).convert_alpha()
        self.last_update_time = 0

    # Removing of obstacle
    def remove(self):
        if time() - self.last_update_time > 1:
            self.last_update_time = time()
            self.kill()