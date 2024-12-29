from gc import enable
from turtledemo.clock import setup

import pygame.sprite
from pygame.transform import scale
from time import time

from config import *

class Hero(pygame.sprite.Sprite):
    def __init__(self, position, groups, collision_sprites, enemies, bridge):
        super().__init__(groups)  # Pridanie hráča do skupiny spriteov
        self.frames = {'left': [], 'right': [], 'idle': [], 'attack': [], 'death': []}  # Animácie pre každý smer
        self.load_images()  # Načítanie animácií z disku
        self.state = 'idle' # Počiatočný smer
        self.frame_index = 0  # index animácie
        self.image = pygame.image.load(join('assets', 'hero', self.state, '0.png')).convert_alpha()  # Počiatočný obrázok hráča
        self.image = pygame.transform.scale(self.image, (self.image.get_width()*2, self.image.get_height()*2))
        self.rect = self.image.get_rect(center=position)  # Obdĺžnik pre kolízie a pozíciu hráča
        self.direction = pygame.Vector2()  # Smer pohybu (vektor)
        self.speed = 500  # Rýchlosť hráča
        self.collision_sprites = collision_sprites  # Objekty na detekciu kolízií
        self.enemies = enemies
        self.bridge = bridge
        self.collected_crystals = []
        self.is_attacking = False  # Attack state flag
        self.attack_timer = 0  # Timer to track attack animation
        self.last_attack_time = 0
        self.last_heal_time = 0
        self.last_remove_time = 0
        self.damage_applied = False
        self.is_mirrored = False
        self.health = 300  # Initialize health to 100
        self.max_health = 300
        self.damage = 10   # Hero's damage
        self.is_dead = False  # Flag to track if the hero is dead
        self.death_played = False
        self.walk_sound = pygame.mixer.Sound(join('assets', 'audio', 'hero', 'walk.mp3'))  # Load walking sound
        self.walk_sound.set_volume(0.5)
        self.last_walk_play = 0
        self.attack_sound = pygame.mixer.Sound(join('assets', 'audio', 'hero', 'attack.wav'))  # Load walking sound
        self.attack_sound.set_volume(0.5)
        self.last_attack_play = False
        self.dying_sound = pygame.mixer.Sound(join('assets', 'audio', 'hero', 'death.wav'))  # Load walking sound
        self.dying_sound.set_volume(0.5)
        self.last_death_play = 0
        self.bridge_sound = pygame.mixer.Sound(join('assets', 'audio', 'items', 'bridge.wav'))
        self.bridge_sound.set_volume(0.5)

    def load_images(self):
        # Načítanie animácií pre všetky smery
        for state in self.frames.keys():
            for folder_path, sub_folders, file_names in walk(join('assets', 'hero', state)):
                if file_names:
                    for file_name in sorted(file_names, key=lambda name: int(name.split('.')[0])):
                        full_path = join(folder_path, file_name)  # Cesta k obrázku
                        surface = pygame.image.load(full_path).convert_alpha()  # Načítanie obrázku
                        surface = pygame.transform.scale(surface, (surface.get_width() * 2, surface.get_height()*2))
                        self.frames[state].append(surface)  # Uloženie do slovníka animácií

    def animate(self, delta):
        if not self.is_dead:
            if self.is_attacking:
                self.walk_sound.stop()
                if not self.last_attack_play:
                    self.last_attack_play = True
                    self.attack_sound.play(1)
                self.frame_index += 15 * delta
                if self.state == 'attack':
                    if self.frame_index >= len(self.frames['attack']):
                        self.is_attacking = False  # Reset attack after animation
                        self.frame_index = 0
                        self.attack_sound.stop()
                        self.last_attack_play = False
                        self.is_mirrored = False
                        self.state = 'idle' if self.direction.magnitude() == 0 else self.state
            else:
                if self.direction.magnitude() == 0:
                    self.state = 'idle'
                    self.walk_sound.stop()
                else:
                    if not pygame.mixer.get_busy():
                        self.walk_sound.play()
                # Nastavenie animácie na základe pohybu
                if self.direction.x != 0:
                    self.state = 'right' if self.direction.x > 0 else 'left'
                if self.direction.y != 0:
                    if self.direction.x == 0:
                        self.state = 'left' if self.direction.y > 0 else 'right'
                    else:
                        self.state = 'right' if self.direction.x > 0 else 'left'

                # Aktualizácia indexu animácie
                self.frame_index += 10 * delta

                if self.state == 'idle':
                    self.frame_index = (self.frame_index + 5 * delta) % len(self.frames['idle'])  # Slow idle animation
                else:
                    self.frame_index %= len(self.frames[self.state])
        else:
            if self.state == 'death' and not self.death_played:
                self.walk_sound.stop()
                self.attack_sound.stop()
                if time() - self.last_death_play > 1:
                    self.last_death_play = time()
                    self.dying_sound.play()
                self.frame_index += 10 * delta

                if self.frame_index >= len(self.frames['death']):
                    self.frame_index = 9
                    print('Hey')
                    self.death_played = True

                self.frame_index %= len(self.frames[self.state])

        self.image = self.frames[self.state][int(self.frame_index)]
        if self.is_mirrored:
            self.image = pygame.transform.flip(self.image, True, False)

    def collision(self, direction):
        # Riešenie kolízií s objektmi
        collision_rect = pygame.Rect(self.rect.centerx - 40, self.rect.centery - 40, 80, 80)

        for item in self.bridge:
            if collision_rect.colliderect(item.rect):  # Detect collision with adjusted size
                if direction == 'horizontal':  # Horizontal collision
                    if self.direction.x > 0:  # Moving right
                        if collision_rect.right > item.rect.left:
                            collision_rect.right = item.rect.left
                    if self.direction.x < 0:  # Moving left
                        if collision_rect.left < item.rect.right:
                            collision_rect.left = item.rect.right

                if direction == 'vertical':  # Vertical collision
                    if self.direction.y > 0:  # Moving down
                        if collision_rect.bottom > item.rect.top:
                            collision_rect.bottom = item.rect.top
                    if self.direction.y < 0:  # Moving up
                        if collision_rect.top < item.rect.bottom:
                            collision_rect.top = item.rect.bottom

        for enemy in self.enemies:
            enemy_rect = pygame.Rect(enemy.rect.x + 290, enemy.rect.y + 50, enemy.rect.width, enemy.rect.height - 50) if enemy.enemy_type == 'warlock' else pygame.Rect(enemy.rect.x, enemy.rect.y + 50, enemy.rect.width, enemy.rect.height - 50)
            if collision_rect.colliderect(enemy_rect):
                if direction == 'horizontal':  # Horizontal collision
                    if self.direction.x > 0:  # Moving right
                        if collision_rect.right > enemy_rect.left:
                            collision_rect.right = enemy_rect.left
                    if self.direction.x < 0:  # Moving left
                        if collision_rect.left < enemy_rect.right:
                            collision_rect.left = enemy_rect.right

                if direction == 'vertical':  # Vertical collision
                    if self.direction.y > 0:  # Moving down
                        if collision_rect.bottom > enemy_rect.top:
                            collision_rect.bottom = enemy_rect.top
                    if self.direction.y < 0:  # Moving up
                        if collision_rect.top < enemy_rect.bottom:
                            collision_rect.top = enemy_rect.bottom

        for sprite in self.collision_sprites:
            if collision_rect.colliderect(sprite.rect):  # Detect collision with adjusted size
                if direction == 'horizontal':  # Horizontal collision
                    if self.direction.x > 0:  # Moving right
                        if collision_rect.right > sprite.rect.left:
                            collision_rect.right = sprite.rect.left
                    if self.direction.x < 0:  # Moving left
                        if collision_rect.left < sprite.rect.right:
                            collision_rect.left = sprite.rect.right

                if direction == 'vertical':  # Vertical collision
                    if self.direction.y > 0:  # Moving down
                        if collision_rect.bottom > sprite.rect.top:
                            collision_rect.bottom = sprite.rect.top
                    if self.direction.y < 0:  # Moving up
                        if collision_rect.top < sprite.rect.bottom:
                            collision_rect.top = sprite.rect.bottom

        self.rect.centerx = collision_rect.centerx
        self.rect.centery = collision_rect.centery

    def attack_check(self):
        collision_rect = pygame.Rect(self.rect.centerx - 40, self.rect.centery - 40, 80, 80)
        for enemy in self.enemies:
            enemy_rect = pygame.Rect(enemy.rect.x, enemy.rect.y - 50, enemy.rect.width + 100, enemy.rect.height + 100)
            if collision_rect.colliderect(enemy_rect):
                if time() - self.last_attack_time > 0.5:
                    self.last_attack_time = time()
                    enemy.take_damage(self.damage)

    def move(self, delta):
        # Pohyb hráča s detekciou kolízií
        if not self.is_attacking and not self.is_dead:
            self.rect.x += self.direction.x * self.speed * delta  # Pohyb horizontálne
            self.collision("horizontal")  # Kontrola kolízií horizontálne
            self.rect.y += self.direction.y * self.speed * delta  # Pohyb vertikálne
            self.collision("vertical")  # Kontrola kolízií vertikálne

    def heal(self):
        if time() - self.last_heal_time > 1:
            if self.health + 25 <= 300:
                self.health += 25
            else:
                self.health = 300
            self.last_heal_time = time()

    def remove_crystal(self):
        if(
            not ((1574 <= self.rect.x <= 1638) and
            (432 <= self.rect.y <= 496))
        ):
            return

        if time() - self.last_remove_time > 0.5:
            self.last_remove_time = time()
            if len(self.collected_crystals):
                print(self.collected_crystals, self.bridge)
                crystal = self.collected_crystals.pop()
                print(crystal.index)
                for item in self.bridge:
                    if item.index == crystal.index:
                        item.remove()
                self.bridge = [item for item in self.bridge if item.index != crystal.index]
                self.bridge_sound.play()

    def input(self):
        if self.is_dead:
            return
        # Spracovanie vstupu od používateľa
        keys = pygame.key.get_pressed()
        if not self.is_attacking:
            self.direction.x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
            self.direction.y = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
            self.direction = self.direction.normalize() if self.direction else self.direction

        if keys[pygame.K_e]:  # Trigger attack
            self.is_attacking = True
            self.frame_index = 0
            self.state = 'attack'
            self.is_mirrored = False
            self.attack_check()

        if keys[pygame.K_q]:  # Trigger attack left
            self.is_attacking = True
            self.frame_index = 0
            self.state = 'attack'
            self.is_mirrored = True
            self.attack_check()

        if keys[pygame.K_w]:
            self.remove_crystal()



    def take_damage(self, amount):
        if self.health <= 0:
            return
        self.health -= amount
        print('Hero health', self.health)
        if self.health <= 0:
            self.die()

    def die(self):
        if not self.is_dead:
            self.is_dead = True
            self.state = 'death'
            self.frame_index = 0

    def update(self, delta):
        # Hlavná aktualizácia hráča (vstup, pohyb, animácia)
        if not self.is_dead:
            self.input()
            self.move(delta)
        self.animate(delta)