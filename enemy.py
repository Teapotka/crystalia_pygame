from config import *
from time import time

class Enemy(pygame.sprite.Sprite):
    def __init__(self, position, groups, collision_sprites, enemy_type):
        super().__init__(groups)  # Add the enemy to the sprite groups
        self.enemy_type = enemy_type  # Type of the enemy (inquisitor, warlock, incubus)
        self.frames = {'idle': [], 'attack': [], 'death': []}  # Animations for the enemy
        self.scale_index = 2 if enemy_type == 'inquisitor' else 3
        self.load_images(enemy_type)  # Load animations from disk
        self.state = 'idle'  # Initial state
        self.frame_index = 0  # Animation index
        self.image = pygame.image.load(join('assets', self.enemy_type, self.state, '0.png')).convert_alpha()
        self.image = pygame.transform.scale(self.image, (self.image.get_width() * self.scale_index,
                                                         self.image.get_height() * self.scale_index))
        self.rect = self.image.get_rect(center=position)  # Rectangle for collision and positioning
        self.rect.width = 140
        self.collision_sprites = collision_sprites  # Collision detection
        self.attack_timer = 0  # Timer for tracking attack animation duration
        self.is_attacking = False  # Attack state flag
        self.last_attack_time = 0  # Time tracking for attack cooldown
        self.damage_applied = False
        self.health = 50
        self.damage = 0
        self.max_health = 50
        self.attack_sound = pygame.mixer.Sound(join('assets', 'audio', enemy_type, 'attack.wav'))  # Load walking sound
        self.attack_sound.set_volume(0.5)
        self.last_play_time = 0
        self.death_sound = pygame.mixer.Sound(join('assets', 'audio', enemy_type, 'death.wav'))  # Load walking sound
        self.death_sound.set_volume(0.5)
        self.last_death_time = 0

        if enemy_type == 'inquisitor':
            self.damage = 5
            self.health = 50
            self.max_health = 50
        elif enemy_type == 'incubus':
            self.damage = 10
            self.health = 100
            self.max_health = 100
        else:
            self.damage = 20
            self.health = 200
            self.max_health = 200

        self.is_dead = False  # Flag to track if the enemy is dead
        self.death_played = False

    def load_images(self, enemy_type):
        # Load animations for the enemy based on its type
        for state in self.frames.keys():
            for folder_path, sub_folders, file_names in walk(join('assets', enemy_type, state)):
                if file_names:
                    for file_name in sorted(file_names, key=lambda name: int(name.split('.')[0])):
                        full_path = join(folder_path, file_name)  # Path to image
                        surface = pygame.image.load(full_path).convert_alpha()  # Load image
                        surface = pygame.transform.scale(surface, (surface.get_width() * self.scale_index, surface.get_height()*self.scale_index))
                        self.frames[state].append(surface)  # Store in the animation dictionary

    def animate(self, delta):
        if not self.is_dead:
            if self.is_attacking:
                if time() - self.last_play_time > 1:
                    self.last_play_time = time()
                    self.attack_sound.play()
                # Play attack animation
                self.frame_index += 15 * delta
                if self.frame_index >= len(self.frames['attack']):
                    self.is_attacking = False  # Reset attack state after animation
                    self.frame_index = 0
                    self.state = 'idle'  # Return to idle state after attack
                    self.damage_applied = False
            else:
                # Play idle animation when not attacking
                self.frame_index += 10 * delta
                self.frame_index %= len(self.frames['idle'])  # Loop idle animation
        else:
            if self.state == 'death' and not self.death_played:
                if time() - self.last_death_time > 1:
                    self.last_death_time = time()
                    self.death_sound.play()
                self.frame_index += 10 * delta
                if self.frame_index >= len(self.frames['death']):
                    self.frame_index = len(self.frames['death']) - 1
                    self.death_played = True
                    self.kill()
                self.frame_index %= len(self.frames[self.state])

        self.image = self.frames[self.state][int(self.frame_index)]  # Set the current image for the sprite
        if self.enemy_type == 'inquisitor' or self.enemy_type == 'warlock':
            self.image = pygame.transform.flip(self.image, True, False)

    def collision(self, hero_rect, hero):
        # Check for collision with the hero (attack upon collision)
        collision_rect = pygame.Rect(self.rect.centerx + 100, self.rect.centery - 40, 100, 100) if self.enemy_type == 'warlock' else self.rect

        if collision_rect.colliderect(hero_rect):
            if time() - self.last_attack_time > 1:  # Avoid continuous attacks, cooldown of 1 second
                self.last_attack_time = time()
                self.is_attacking = True
                self.damage_applied = False
                self.state = 'attack'  # Switch to attack state
            if self.is_attacking and not self.damage_applied:
                hero.take_damage(self.damage)
                self.damage_applied = True
                print("Attack")

    def take_damage(self, amount):
        self.health -= amount
        print(self.enemy_type, "Heath is", self.health)
        if self.health <= 0:
            self.die()

    def die(self):
        if not self.is_dead:
            self.is_dead = True
            self.state = 'death'
            self.frame_index = 0

    def update(self, delta, hero_rect, hero):
        # Update the enemy: check for collision and animate
        if not self.is_dead:
            self.collision(hero_rect, hero)
        self.animate(delta)
