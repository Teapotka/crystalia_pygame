import pygame.mixer
from bridgeitem import BridgeItem
from config import *
from enemy import Enemy
from groups import *
from hero import Hero
from pytmx.util_pygame import load_pygame
from item import Item
from sprites import *
from time import time

class Game:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.running = True
        self.clock = pygame.time.Clock()
        pygame.display.set_caption("Crystalia")
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bridge = []
        self.camera_x = 0
        self.camera_y = 0
        self.setup_map()
        self.status = 'init'
        self.game_over_time = None
        self.last_time_updated = 0

        pygame.mixer.init()
        pygame.mixer.music.load(join('assets', 'audio', 'background_music.mp3'))  # Adjust the path
        pygame.mixer.music.set_volume(0.5)

    def setup_map(self):
        map = load_pygame(join('assets', 'map', 'map.tmx'))

        # Ground sprites
        for x, y, image in map.get_layer_by_name('bottom').tiles():
            Sprite((x * TILE_SIZE, y * TILE_SIZE), image, self.all_sprites)

        # Borders of the island
        for item in map.get_layer_by_name('collisions'):
            CollisionSprite((item.x, item.y), pygame.Surface((item.width, item.height)), self.collision_sprites)

        # Trees and stones
        for item in map.get_layer_by_name('objects'):
            if item.image is not None:
                CollisionSprite((item.x, item.y), item.image, (self.all_sprites, self.collision_sprites))

        # Borders of every bridge item
        for item in map.get_layer_by_name('bridge'):
            bridge_item = BridgeItem((item.x, item.y), int(item.type), self.all_sprites)
            self.bridge.append(bridge_item)

        # Hero, Enemies, Potions and Crystals
        for item in map.get_layer_by_name('entities'):
            self.create_entity(item)

    # Entity factory
    def create_entity(self, item):
        enemy_types = {'Inquisitor': 'inquisitor', 'Incubus': 'incubus', 'Warlock': 'warlock'}
        if item.name in enemy_types:
            enemy = Enemy((item.x + 50 if item.name == 'Inquisitor' else item.x, item.y - 50), self.all_sprites, self.collision_sprites, enemy_types[item.name])
            self.enemies.add(enemy)
        elif item.name == 'Hero':
            self.player = Hero((item.x, item.y), self.all_sprites, self.collision_sprites, self.enemies, self.bridge)
        elif item.name == 'Crystal':
            Item((item.x, item.y), self.all_sprites, str(item.type)+'crystal')
        elif item.name == 'Potion':
            Item((item.x, item.y), self.all_sprites, 'potion')

    # Health bar of every monster and Hero
    def draw_health_bar(self, entity):
        bar_width = 60
        bar_height = 8
        bar_x = entity.rect.centerx - bar_width // 2
        bar_y = entity.rect.top - bar_height - 5

        bar_x -= self.camera_x
        bar_y -= self.camera_y

        health_color = ({'warlock': (255, 0, 0),
                        'incubus': (255, 100, 0),
                        'inquisitor': (255, 255, 0),
                         'hero': (0, 255, 0)}).get(entity.enemy_type)

        if entity.enemy_type == 'warlock':
            bar_x += 300
            bar_y += 300
        elif entity.enemy_type == 'incubus':
            bar_x += 80
            bar_y += 100
        elif entity.enemy_type == 'inquisitor':
            bar_y += 70

        pygame.draw.rect(self.display_surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        health_width = (entity.health / entity.max_health) * bar_width

        pygame.draw.rect(self.display_surface, health_color, (bar_x, bar_y, health_width, bar_height))

    # Top left row with crystals
    def draw_crystals(self):
        x_offset = 10
        y_offset = 10

        for crystal_image in [item.image for item in self.player.collected_crystals]:
            self.display_surface.blit(crystal_image, (x_offset, y_offset))
            x_offset += crystal_image.get_width() + 5  # Add some spacing between crystals

    # Text labels
    def draw_hints(self, text, position, size, color = (255,255,255)):
        pygame.font.init()
        font = pygame.font.Font(pygame.font.get_default_font(), size)
        text_surface = font.render(text, True, color)

        world_x, world_y = position

        screen_x = world_x - self.camera_x
        screen_y = world_y - self.camera_y

        text_rect = text_surface.get_rect(topleft=(screen_x, screen_y))
        self.display_surface.blit(text_surface, text_rect)

    def show_start_screen(self):
        background = pygame.image.load(join('assets', 'background.png'))
        self.display_surface.blit(background, (0, 0))
        self.draw_hints('Press [SPACE] to Start', (WINDOW_WIDTH // 2 - 150, 200), 30, (0,0,0))
        pygame.display.flip()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        waiting = False

    def show_end_screen(self, message):
        self.camera_x = 0
        self.camera_y = 0
        background = pygame.image.load(join('assets', 'background.png'))
        self.display_surface.blit(background, (0, 0))  # Black background
        self.draw_hints(message, (WINDOW_WIDTH // 2 - 100, 200), 30, (0,0,0))
        self.draw_hints('Press [R] to Restart or [ESC] to Quit', (WINDOW_WIDTH // 2 - 200, 240), 20, (0,0,0))
        pygame.display.flip()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.__init__()
                        self.run()
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

    def run(self):
        self.show_start_screen()

        while self.running:
            delta = self.clock.tick() / 1000
            self.handle_events()

            self.update_sprites(delta)

            self.render()

            if self.check_game_over_conditions():
                break

            pygame.display.update()

        if self.status != 'init':
            self.show_end_screen(self.status)
        else:
            pygame.quit()
            sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update_sprites(self, delta):
        for sprite in self.all_sprites:
            if isinstance(sprite, Enemy):
                sprite.update(delta, self.player.rect, self.player)
            elif isinstance(sprite, Item):
                sprite.update(self.player)
            else:
                sprite.update(delta)

        self.camera_x = self.player.rect.centerx - WINDOW_WIDTH // 2
        self.camera_y = self.player.rect.centery - WINDOW_HEIGHT // 2

    def render(self):
        self.display_surface.fill((58, 35, 97))
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.play(-1)

        self.all_sprites.draw(self.player.rect.center)

        self.draw_health_bar(self.player)

        for enemy in self.enemies:
            self.draw_health_bar(enemy)

        self.draw_crystals()

        self.draw_hints('Use arrows to move', (1600, 600), 20)
        self.draw_hints('Press [W] when You stand on magic ground to unlock gate with crystal', (1500, 460), 15)
        self.draw_hints('Press [Q] or [E] to attack', (1000, 480), 20)
        self.draw_hints('Collect 5 crystals to open all gates', (800, 800), 20)
        self.draw_hints('Drink potion to heal', (510, 950), 20)

    def check_game_over_conditions(self):
        if self.player.health <= 0 and self.status == 'init':
            if self.game_over_time is None:
                self.game_over_time = time()
            elif time() - self.game_over_time > 3:
                self.status = 'Game Over!'
                pygame.mixer.music.stop()
                return True

        if self.player.rect.y <= 48 and (1200 <= self.player.rect.x <= 1900):
            self.status = 'You Won!'
            pygame.mixer.music.stop()
            return True
        return False

if __name__ == '__main__':
    game = Game()
    game.run()
