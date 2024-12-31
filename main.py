from inspect import stack

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
        self.clock = pygame.time.Clock()   # Hodiny na riadenie snímkovej frekvencie
        pygame.display.set_caption("Crystalia")
        # Skupiny pre sprity
        self.all_sprites = AllSprites()  # Vlastná skupina pre všetky sprity
        self.collision_sprites = pygame.sprite.Group()  # Skupina pre sprity s kolíziami
        self.enemies = pygame.sprite.Group()
        self.bridge = []
        self.camera_x = 0  # Camera X position
        self.camera_y = 0  # Camera Y position
        self.setup_map()
        self.status = 'init'
        self.game_over_time = None
        self.last_time_updated = 0

        pygame.mixer.init()
        pygame.mixer.music.load(join('assets', 'audio', 'background_music.mp3'))  # Adjust the path
        pygame.mixer.music.set_volume(0.5)

    def setup_map(self):
        map = load_pygame(join('assets', 'map', 'map.tmx'))

        for x, y, image in map.get_layer_by_name('bottom').tiles():
            Sprite((x * TILE_SIZE, y * TILE_SIZE), image, self.all_sprites)

        # Spracovanie vrstvy "collisions" (prázdne objekty na detekciu kolízií)
        for item in map.get_layer_by_name('collisions'):
            CollisionSprite((item.x, item.y), pygame.Surface((item.width, item.height)), self.collision_sprites)

        for item in map.get_layer_by_name('objects'):
            if item.image is not None:
                CollisionSprite((item.x, item.y), item.image, (self.all_sprites, self.collision_sprites))

        bridge_index = 0
        for item in map.get_layer_by_name('bridge'):
            bridge_item = BridgeItem((item.x, item.y), bridge_index, self.all_sprites)
            self.bridge.append(bridge_item)
            bridge_index += 1

        for item in map.get_layer_by_name('entities'):
            if item.name == 'Inquisitor':
                enemy = Enemy((item.x + 50, item.y - 50), self.all_sprites, self.collision_sprites, 'inquisitor')
                self.enemies.add(enemy)

            if item.name == 'Incubus':
                enemy = Enemy((item.x, item.y - 50), self.all_sprites, self.collision_sprites, 'incubus')
                self.enemies.add(enemy)

            if item.name == 'Warlock':
                enemy = Enemy((item.x, item.y - 50), self.all_sprites, self.collision_sprites, 'warlock')
                self.enemies.add(enemy)

            if item.name == 'Hero':  # Ak sa objekt volá "Player", inicializuj hráča
                self.player = Hero((item.x, item.y), self.all_sprites, self.collision_sprites, self.enemies, self.bridge)

            crystal_index = 0
            for item in map.get_layer_by_name('entities'):
                if item.name == 'Crystal':
                    Item((item.x, item.y), self.all_sprites, str(crystal_index)+'crystal')
                    crystal_index += 1
                if item.name == 'Potion':
                    Item((item.x, item.y), self.all_sprites, 'potion')

    def draw_health_bar(self, entity):
        # Positioning the health bar at the bottom center
        bar_width = 60  # Width of the health bar
        bar_height = 8  # Height of the health bar
        bar_x = entity.rect.centerx - bar_width // 2  # Center horizontally above the entity
        bar_y = entity.rect.top - bar_height - 5  # Position it above the entity

        # Adjust for camera position (this keeps health bars fixed)
        bar_x -= self.camera_x
        bar_y -= self.camera_y

        if isinstance(entity, Enemy):
            if entity.enemy_type == 'warlock':
                bar_x += 300
                bar_y += 300
            elif entity.enemy_type == 'incubus':
                bar_x += 80
                bar_y += 100
            else:
                bar_y += 70


        # Draw the background of the health bar (gray)
        pygame.draw.rect(self.display_surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))

        # Calculate the width of the current health portion
        health_width = (entity.health / entity.max_health) * bar_width

        # Draw the health portion (green)
        color = (0, 255, 0)
        if isinstance(entity, Enemy):
            if entity.enemy_type == 'warlock':
                color = (255, 0, 0)
            elif entity.enemy_type == 'incubus':
                color = (255, 100, 0)
            else:
                color = (255, 255, 0)

        pygame.draw.rect(self.display_surface, color, (bar_x, bar_y, health_width, bar_height))

    def draw_crystals(self):
        x_offset = 10  # X position of the first crystal
        y_offset = 10  # Y position of the first crystal

        for crystal_image in [item.image for item in self.player.collected_crystals]:
            self.display_surface.blit(crystal_image, (x_offset, y_offset))
            x_offset += crystal_image.get_width() + 5  # Add some spacing between crystals

    def draw_hints(self, text, position, size, color = (255,255,255)):
        pygame.font.init()
        font = pygame.font.Font(pygame.font.get_default_font(), size)
        text_surface = font.render(text, True, color)

        world_x, world_y = position

        screen_x = world_x - self.camera_x
        screen_y = world_y - self.camera_y

        # Render the text at the adjusted position
        text_rect = text_surface.get_rect(topleft=(screen_x, screen_y))
        self.display_surface.blit(text_surface, text_rect)

    def show_start_screen(self):
        background = pygame.image.load(join('assets', 'background.png'))
        self.display_surface.blit(background, (0, 0))  # Draw the background image
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
        self.camera_x = 0  # Camera X position
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
                    if event.key == pygame.K_r:  # Restart the game
                        self.__init__()  # Reinitialize the game
                        self.run()
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

    def run(self):
        self.show_start_screen()

        while self.running:
            delta = self.clock.tick() / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            for sprite in self.all_sprites:
                if isinstance(sprite, Enemy):
                    sprite.update(delta, self.player.rect, self.player)  # Pass hero's rect to the enemy's update method
                elif isinstance(sprite, Item):
                    sprite.update(self.player)
                else:
                    sprite.update(delta)

            # self.all_sprites.update(delta)
            self.camera_x = self.player.rect.centerx - WINDOW_WIDTH // 2
            self.camera_y = self.player.rect.centery - WINDOW_HEIGHT // 2
            self.display_surface.fill('purple')
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.play(-1)

            self.all_sprites.draw(self.player.rect.center)

            # Draw the hero's health bar
            self.draw_health_bar(self.player)

            # Draw health bars for enemies (above their heads)
            for enemy in self.enemies:
                self.draw_health_bar(enemy)

            self.draw_crystals()

            self.draw_hints('Use arrows to move', (1600, 600), 20)
            self.draw_hints('Press [W] when You stand on magic ground to unlock gate with crystal', (1500, 460), 15)
            self.draw_hints('Press [Q] or [E] to attack', (1000, 480), 20)
            self.draw_hints('Collect 5 crystals to open all gates', (800, 800), 20)
            self.draw_hints('Drink potion to heal', (510, 950), 20)

            if self.player.health <= 0 and self.status == 'init':
                if self.game_over_time is None:
                    self.game_over_time = time()
                elif time() - self.game_over_time > 3:
                    self.status = 'Game Over!'
                    pygame.mixer.music.stop()
                    break
                print(time() - self.game_over_time)

            if self.player.rect.y <= 48 and (1200 <= self.player.rect.x <= 1900):
                self.status = 'You Won!'
                pygame.mixer.music.stop()
                break

            pygame.display.update()
        if self.status != 'init':
            self.show_end_screen(self.status)
        else:
            pygame.quit()
            sys.exit()

if __name__ == '__main__':
    game = Game()
    game.run()
