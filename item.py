from config import *
from time import time

class Item(pygame.sprite.Sprite):
    def __init__(self, position, groups, name):
        super().__init__(groups)  # Add item to sprite groups
        self.image = pygame.image.load(join('assets', 'items', name+'.png')).convert_alpha()
        self.rect = self.image.get_rect(topleft=position)  # Position the item
        self.name = name
        self.is_drunk = False
        self.index = -1
        type = 'potion' if name == 'potion' else 'crystal'
        self.item_sound = pygame.mixer.Sound(join('assets', 'audio', 'items', type+'.wav'))  # Load walking sound
        self.item_sound.set_volume(0.5)
        self.last_played_time = 0
        if(name != 'potion'):
            self.index = int(self.name[0])

    def update(self, hero):
        # Check for collision with the hero
        if self.rect.colliderect(hero.rect):
            if self.name == 'potion' and not self.is_drunk:
                self.is_drunk = True
                hero.heal()
                print('Hero health', hero.health)
            else:
                 if self.name not in [crystal.name for crystal in hero.collected_crystals]:
                    hero.collected_crystals.append(self)
                    print(hero.collected_crystals)
            if time() - self.last_played_time > 1:
                self.last_played_time = time()
                self.item_sound.play()
            self.kill()  # Remove the item from all sprite groups