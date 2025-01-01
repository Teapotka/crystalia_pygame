from config import *
from time import time

class Item(pygame.sprite.Sprite):
    def __init__(self, position, groups, name):
        super().__init__(groups)  # Add item to sprite groups
        self.image = pygame.image.load(join('assets', 'items', name+'.png')).convert_alpha()
        self.rect = self.image.get_rect(topleft=position)  # Position the item
        self.name = name
        self.is_drunk = False
        self.index = int(name[0]) if name != 'potion' else -1
        self.type = 'potion' if name == 'potion' else 'crystal'

        self.item_sound = pygame.mixer.Sound(join('assets', 'audio', 'items', self.type+'.wav'))
        self.item_sound.set_volume(0.5)

    def update(self, hero):
        if self.rect.colliderect(hero.rect):
            # Applying effect
            if self.name == 'potion' and not self.is_drunk:
                self.is_drunk = True
                hero.heal()
            else:
                 # Collecting crystal
                 if self.name not in [crystal.name for crystal in hero.collected_crystals]:
                    hero.collected_crystals.append(self)
            if self.item_sound.get_num_channels() == 0:
                self.item_sound.play()
            self.kill()