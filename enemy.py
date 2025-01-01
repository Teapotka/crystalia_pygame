from config import *
from time import time

class Enemy(pygame.sprite.Sprite):
    def __init__(self, position, groups, collision_sprites, enemy_type):
        super().__init__(groups)
        # Initial attributes
        self.enemy_type = enemy_type
        self.state = 'idle'
        self.frame_index = 0
        self.scale_index = 2 if enemy_type == 'inquisitor' else 3
        self.load_images(enemy_type)
        self.image = self.frames['idle'][0]
        self.rect = self.image.get_rect(center=position)
        stats = {
            'inquisitor': {'damage': 5, 'health': 50},
            'incubus': {'damage': 10, 'health': 100},
            'warlock': {'damage': 20, 'health': 200}
        }
        self.damage = stats[self.enemy_type]['damage']
        self.health = self.max_health = stats[self.enemy_type]['health']
        self.rect.width = 140

        # Flags
        self.is_attacking = False
        self.damage_applied = False
        self.is_dead = False
        self.death_played = False
        self.last_attack_time = 0

        # Group
        self.collision_sprites = collision_sprites

        self.load_sounds()

    def load_images(self, enemy_type):
        self.frames = {'idle': [], 'attack': [], 'death': []}
        for state in self.frames.keys():
            for folder_path, sub_folders, file_names in walk(join('assets', enemy_type, state)):
                if file_names:
                    for file_name in sorted(file_names, key=lambda name: int(name.split('.')[0])):
                        full_path = join(folder_path, file_name)
                        surface = pygame.image.load(full_path).convert_alpha()
                        # Scaling of monsters
                        surface = pygame.transform.scale(surface, (surface.get_width() * self.scale_index, surface.get_height()*self.scale_index))
                        self.frames[state].append(surface)

    def load_sounds(self):
        self.attack_sound = self.load_sound(self.enemy_type, 'attack.wav')
        self.death_sound = self.load_sound(self.enemy_type, 'death.wav')

    def load_sound(self, folder, file):
        sound = pygame.mixer.Sound(join('assets', 'audio', folder, file))
        sound.set_volume(0.5)
        return sound

    # Enemies except for incubus are mirrored
    def update_image(self):
        self.image = self.frames[self.state][int(self.frame_index)]
        self.image = pygame.transform.flip(self.image, self.enemy_type != 'incubus', False)

    def handle_death_animation(self, delta):
        if self.death_sound.get_num_channels() == 0:
            self.death_sound.play()
        self.frame_index += 10 * delta
        if self.frame_index >= len(self.frames['death']):
            self.frame_index = len(self.frames['death']) - 1
            self.death_played = True
            self.kill()

        self.update_image()

    def handle_movement_animation(self, delta):
        if self.is_attacking:
            if self.attack_sound.get_num_channels() == 0:
                self.attack_sound.play()
            self.state = 'attack'
            self.frame_index += 15 * delta
            if self.frame_index >= len(self.frames['attack']):
                self.frame_index = 0
                self.is_attacking = False
                self.attack_sound.stop()
        else:
            self.state = 'idle'
            self.frame_index += 10 * delta
            self.frame_index %= len(self.frames['idle'])
            self.update_image()
        self.update_image()

    def animate(self, delta):
        if self.is_dead:
            self.state = 'death'
            if not self.death_played:
                self.handle_death_animation(delta)
        else:
            self.handle_movement_animation(delta)

    def collision(self, hero_rect, hero):
        # Attack reachable areas
        enemy_rects = ({
            'inquisitor': pygame.Rect(529, 640, 230, 200),
            'incubus': pygame.Rect(153, 2200, 250, 200),
            'warlock': pygame.Rect(2563, 2409, 350, 400)
        })
        if enemy_rects[self.enemy_type].colliderect(hero_rect):
            if time() - self.last_attack_time > 1:
                self.last_attack_time = time()
                self.is_attacking = True
                self.damage_applied = False
                self.state = 'attack'
            if self.is_attacking and not self.damage_applied:
                hero.take_damage(self.damage)
                self.damage_applied = True

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.die()

    def die(self):
        if not self.is_dead:
            self.is_dead = True
            self.state = 'death'
            self.frame_index = 0

    def update(self, delta, hero_rect, hero):
        if not self.is_dead:
            self.collision(hero_rect, hero)
        self.animate(delta)
