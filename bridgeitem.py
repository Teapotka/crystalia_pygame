from config import *
from time import time

class BridgeItem(pygame.sprite.Sprite):

    def __init__(self, position, index, groups):
        super().__init__(groups)
        x, y = position
        self.index = index  # Index to track position in bridge
        self.rect = pygame.Rect(x, y, 192, 64)  # 5 parts, 448x43
        self.colors = [
            (255, 192, 203),
            (100, 0, 255),
            (255, 0, 0),
            (0, 0, 255),
            (0, 225, 0),
        ]
        self.color = self.colors[index]  # No color initially
        self.image = pygame.Surface(self.rect.size)  # Transparent surface
        self.image.fill(self.color)
        self.last_update_time = 0

    def remove(self):
        # Add color to this part and remove collision
        if time() - self.last_update_time > 1:  # Add color only every 1 second
            self.last_update_time = time()
            self.kill()