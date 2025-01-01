import pygame.sprite
from pygame.transform import scale
from time import time
from config import *

class Hero(pygame.sprite.Sprite):
    def __init__(self, position, groups, collision_sprites, enemies, bridge):
        super().__init__(groups)
        # Initial attributes
        self.load_images()
        self.enemy_type = 'hero'
        self.state = 'idle'
        self.frame_index = 0
        self.image = self.frames['idle'][0]
        self.rect = self.image.get_rect(center=position)
        self.direction = pygame.Vector2()
        self.speed = 500
        self.health = self.max_health = 300
        self.damage = 10

        # Flags
        self.is_attacking = False
        self.damage_applied = False
        self.is_mirrored = False
        self.is_dead = False
        self.death_played = False
        self.attack_playing = False
        self.last_attack_time \
            = self.last_heal_time \
            = self.last_remove_time = 0

        # Groups
        self.collision_sprites = collision_sprites
        self.enemies = enemies
        self.bridge = bridge
        self.collected_crystals = []

        self.load_sounds()

    def load_images(self):
        self.frames = {'left': [], 'right': [], 'idle': [], 'attack': [], 'death': []}
        for state in self.frames.keys():
            for folder_path, sub_folders, file_names in walk(join('assets', 'hero', state)):
                if file_names:
                    for file_name in sorted(file_names, key=lambda name: int(name.split('.')[0])):
                        full_path = join(folder_path, file_name)
                        surface = pygame.image.load(full_path).convert_alpha()
                        surface = pygame.transform.scale(surface, (surface.get_width() * 2, surface.get_height()*2))
                        self.frames[state].append(surface)

    def load_sounds(self):
        self.walk_sound = self.load_sound('hero', 'walk.mp3')
        self.attack_sound = self.load_sound('hero', 'attack.wav')
        self.dying_sound = self.load_sound('hero', 'death.wav')
        self.bridge_sound = self.load_sound('items', 'bridge.wav')

    def load_sound(self, folder, file):
        sound = pygame.mixer.Sound(join('assets', 'audio', folder, file))
        sound.set_volume(0.5)
        return sound

    def handle_movement_animation(self, delta):
        if not self.is_attacking:
            self.attack_sound.stop()
            if self.direction.magnitude() == 0:
                self.walk_sound.stop()
            elif not self.walk_sound.get_num_channels() :
                self.walk_sound.play()

        if self.is_attacking:
            self.state = 'attack'
        elif self.direction.magnitude() == 0:
            self.state = 'idle'
        else:
            if self.direction.x != 0:
                self.state = 'right' if self.direction.x > 0 else 'left'
            if self.direction.y != 0:
                if self.direction.x == 0:
                    self.state = 'left' if self.direction.y > 0 else 'right'
                else:
                    self.state = 'right' if self.direction.x > 0 else 'left'

        if self.is_attacking:
            self.animate_attack(delta)
        else:
            self.frame_index = (self.frame_index + 10 * delta) % len(self.frames[self.state])

        self.update_image()

    def animate_attack(self, delta):
        if not self.attack_sound.get_num_channels():
            self.attack_sound.play()
        self.frame_index += 15 * delta
        if self.frame_index >= len(self.frames['attack']):
            self.is_attacking = False
            self.attack_playing = False
            self.is_mirrored = False
            self.frame_index = 0
            self.attack_sound.stop()

    def handle_death_animation(self, delta):
        if self.dying_sound.get_num_channels() == 0:
            self.dying_sound.play()
        self.frame_index += 10 * delta
        if self.frame_index >= len(self.frames['death']):
            self.frame_index = 9
            self.death_played = True

        self.update_image()

    def update_image(self):
        self.image = self.frames[self.state][int(self.frame_index)]
        self.image = pygame.transform.flip(self.image, self.is_mirrored, False)

    def animate(self, delta):
        if self.is_dead:
            self.state = 'death'
            if not self.death_played:
                self.handle_death_animation(delta)
        else:
            self.handle_movement_animation(delta)

    # Collision with trees, stones, borders, enemies and bridge
    def collision(self, direction):
        collision_rect = pygame.Rect(self.rect.centerx - 40, self.rect.centery - 40, 80, 80)
        self.handle_bridge_collision(collision_rect, direction)
        self.handle_enemy_collision(collision_rect, direction)
        self.handle_sprite_collision(collision_rect, direction)
        self.rect.center = collision_rect.center

    def handle_bridge_collision(self, collision_rect, direction):
        for item in self.bridge:
            self.resolve_collision(collision_rect, item.rect, direction)

    def handle_enemy_collision(self, collision_rect, direction):
        # Enemy collision areas
        enemy_rects = ({
            'inquisitor': pygame.Rect(529, 650, 130, 100),
            'incubus': pygame.Rect(153, 2305, 220, 200),
            'warlock': pygame.Rect(2743, 2509, 250, 200)
                        })
        for enemy in self.enemies:
            enemy_rect = enemy_rects[enemy.enemy_type]
            self.resolve_collision(collision_rect, enemy_rect, direction)

    def handle_sprite_collision(self, collision_rect, direction):
        for sprite in self.collision_sprites:
            self.resolve_collision(collision_rect, sprite.rect, direction)

    def resolve_collision(self, collider, target, direction):
        if collider.colliderect(target):
            if direction == 'horizontal':
                if self.direction.x > 0:
                    collider.right = min(collider.right, target.left)
                else:
                    collider.left = max(collider.left, target.right)
            elif direction == 'vertical':
                if self.direction.y > 0:
                    collider.bottom = min(collider.bottom, target.top)
                else:
                    collider.top = max(collider.top, target.bottom)

    def attack_check(self):
        # Attack reachable area
        collision_rect = pygame.Rect(self.rect.centerx - 40, self.rect.centery - 40, 80, 80)
        enemy_rects = ({
            'inquisitor': pygame.Rect(529, 670, 180, 100),
            'incubus': pygame.Rect(153, 2205, 250, 200),
            'warlock': pygame.Rect(2663, 2509, 250, 200)
        })
        for enemy in self.enemies:
            enemy_rect = enemy_rects[enemy.enemy_type]
            if collision_rect.colliderect(enemy_rect):
                if time() - self.last_attack_time > 0.5:
                    self.last_attack_time = time()
                    enemy.take_damage(self.damage)

    def move(self, delta):
        if not self.is_attacking and not self.is_dead:
            self.rect.x += self.direction.x * self.speed * delta
            self.collision("horizontal")
            self.rect.y += self.direction.y * self.speed * delta
            self.collision("vertical")

    # Drinking potion effect
    def heal(self):
        if time() - self.last_heal_time > 1:
            self.health = min(self.health + 25, self.max_health)
            self.last_heal_time = time()

    # Removes crystals only on magic ground
    def remove_crystal(self):
        if(
            not ((1574 <= self.rect.x <= 1638) and
            (432 <= self.rect.y <= 496))
        ):
            return

        if time() - self.last_remove_time > 0.5:
            self.last_remove_time = time()
            if self.collected_crystals:
                crystal = self.collected_crystals.pop()
                for item in self.bridge:
                    if item.index == crystal.index:
                        item.remove()
                self.bridge = [item for item in self.bridge if item.index != crystal.index]
                self.bridge_sound.play()

    def input(self):
        if self.is_dead:
            return

        # Block of input while attack
        if self.attack_playing:
            return

        keys = pygame.key.get_pressed()
        if not self.is_attacking:
            self.direction.x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
            self.direction.y = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
            self.direction = self.direction.normalize() if self.direction else self.direction

        if keys[pygame.K_e]:
            self.is_attacking = True
            self.attack_playing = True
            self.frame_index = 0
            self.state = 'attack'
            self.is_mirrored = False
            self.attack_check()

        if keys[pygame.K_q]:
            self.is_attacking = True
            self.attack_playing = True
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
        if self.health <= 0:
            self.die()

    def die(self):
        if not self.is_dead:
            self.is_dead = True
            self.state = 'death'
            self.frame_index = 0

    def update(self, delta):
        if not self.is_dead:
            self.input()
            self.move(delta)
        self.animate(delta)