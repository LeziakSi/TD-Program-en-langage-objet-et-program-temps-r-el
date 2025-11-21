import pygame
import sys
import math
import os
import random

# ----------------------------------------
# CONFIGURACIÓN INICIAL
# ----------------------------------------
# Mixer antes para evitar problemas de sonido
try:
    pygame.mixer.pre_init(44100, -16, 2, 512)
except Exception:
    pass

pygame.init()

WIDTH, HEIGHT = 800, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chroniques Pixel - Assaut des Boss")

CLOCK = pygame.time.Clock()
FPS = 60

# Fuente estilo gótica (si no está, cae a la de sistema)
GOTHIC_FONT_NAME = "Old English Text MT"
FONT = pygame.font.SysFont(GOTHIC_FONT_NAME, 24)
BIG_FONT = pygame.font.SysFont(GOTHIC_FONT_NAME, 48)

# Colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (200, 60, 60)
GREEN = (60, 200, 60)
BLUE = (60, 60, 200)
YELLOW = (230, 230, 40)
GREY = (40, 40, 40)
PURPLE = (160, 80, 200)
CYAN = (80, 200, 200)
ORANGE = (255, 160, 60)

# Estados del juego
STATE_TITLE = "TITLE"
STATE_PLAYING = "PLAYING"
STATE_PAUSED = "PAUSED"
STATE_GAME_OVER = "GAME_OVER"
STATE_UPGRADE = "UPGRADE"

# Carpeta base del script (para cargar música)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Música
MUSIC_VOLUME = 0.6
music_muted = False
music_paused = False


# ----------------------------------------
# MÚSICA
# ----------------------------------------
def start_music():
    global music_muted, music_paused
    music_muted = False
    music_paused = False
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        music_paths = [
            os.path.join(BASE_DIR, "music_8bit.ogg"),
            os.path.join(BASE_DIR, "music_8bit.mp3"),
        ]

        loaded = False
        for path in music_paths:
            if os.path.exists(path):
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(MUSIC_VOLUME)
                pygame.mixer.music.play(-1)  # loop infinito
                print(f"[MUSICA] Reproduciendo: {path}")
                loaded = True
                break

        if not loaded:
            print("[MUSICA] No se encontró music_8bit.ogg ni music_8bit.mp3 en la carpeta del juego.")

    except Exception as e:
        print(f"[MUSICA] Error al iniciar la música: {e}")


def toggle_mute_music():
    global music_muted
    if not pygame.mixer.get_init():
        return
    if not pygame.mixer.music.get_busy() and not music_paused:
        return
    if not music_muted:
        pygame.mixer.music.set_volume(0.0)
        music_muted = True
        print("[MUSICA] Mute ON")
    else:
        pygame.mixer.music.set_volume(MUSIC_VOLUME)
        music_muted = False
        print("[MUSICA] Mute OFF")


def toggle_pause_music():
    global music_paused
    if not pygame.mixer.get_init():
        return
    if not music_paused:
        pygame.mixer.music.pause()
        music_paused = True
        print("[MUSICA] Pausa ON")
    else:
        pygame.mixer.music.unpause()
        music_paused = False
        print("[MUSICA] Pausa OFF")


# ----------------------------------------
# CLASES PRINCIPALES
# ----------------------------------------
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Sprite pixelart con "cuerpo" y ojos
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        self._draw_player_sprite()
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT - 80))

        self.base_speed = 5
        self.slow_speed = 2
        self.fast_speed = 8  # velocidad con CTRL
        self.max_hp = 100
        self.hp = self.max_hp

        self.shoot_cooldown = 0
        self.shoot_cooldown_max = 10
        self.special_cooldown = 0
        self.special_charges = 3  # Cargas del poder especial (X)

        # Mejoras
        self.bullet_speed = 9
        self.bullet_damage = 8

    def _draw_player_sprite(self):
        surf = self.image
        surf.fill((0, 0, 0, 0))
        # contorno
        pygame.draw.rect(surf, (10, 30, 10), (0, 0, 32, 32))
        # cuerpo
        pygame.draw.rect(surf, GREEN, (3, 6, 26, 22))
        # pecho brillante
        pygame.draw.rect(surf, (120, 255, 120), (10, 10, 12, 8))
        # ojos
        pygame.draw.rect(surf, WHITE, (8, 18, 4, 4))
        pygame.draw.rect(surf, WHITE, (20, 18, 4, 4))
        pygame.draw.rect(surf, BLUE, (9, 19, 2, 2))
        pygame.draw.rect(surf, BLUE, (21, 19, 2, 2))
        # sombreado inferior
        pygame.draw.rect(surf, (20, 60, 20), (3, 22, 26, 6))

    def update(self, keys):
        # Movimiento con flechas + Shift (lento) + Ctrl (rápido)
        vx, vy = 0, 0
        if keys[pygame.K_LEFT]:
            vx -= 1
        if keys[pygame.K_RIGHT]:
            vx += 1
        if keys[pygame.K_UP]:
            vy -= 1
        if keys[pygame.K_DOWN]:
            vy += 1

        if vx != 0 or vy != 0:
            length = math.hypot(vx, vy)
            if length == 0:
                length = 1
            vx /= length
            vy /= length

            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                speed = self.slow_speed
            elif keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
                speed = self.fast_speed
            else:
                speed = self.base_speed

            self.rect.x += vx * speed
            self.rect.y += vy * speed

        # Mantener dentro de la pantalla
        self.rect.left = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, WIDTH)
        self.rect.top = max(self.rect.top, 0)
        self.rect.bottom = min(self.rect.bottom, HEIGHT)

        # Enfriamientos
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.special_cooldown > 0:
            self.special_cooldown -= 1

    def can_shoot(self):
        return self.shoot_cooldown <= 0

    def shoot(self, boss):
        """Disparo normal (Z) con auto-aim hacia el boss."""
        self.shoot_cooldown = self.shoot_cooldown_max  # frames de cooldown
        return Bullet(self.rect.centerx, self.rect.centery, boss, self.bullet_speed)

    def can_use_special(self):
        return self.special_charges > 0 and self.special_cooldown <= 0

    def use_special(self, special_group):
        """
        Poder especial (X):
        - Lanza un rayo láser vertical que atraviesa todo el escenario.
        """
        if not self.can_use_special():
            return

        beam = SpecialAttack(self.rect.centerx)
        special_group.add(beam)

        self.special_charges -= 1
        self.special_cooldown = FPS * 2  # 2 segundos de cooldown


class Bullet(pygame.sprite.Sprite):
    """Bala del jugador, auto-dirigida al boss."""

    def __init__(self, x, y, target_boss, speed):
        super().__init__()
        self.image = pygame.Surface((12, 12), pygame.SRCALPHA)
        self._draw_bullet_sprite()
        self.rect = self.image.get_rect(center=(x, y))

        self.speed = speed
        if target_boss is not None:
            tx, ty = target_boss.rect.center
            dx = tx - x
            dy = ty - y
            dist = math.hypot(dx, dy)
            if dist == 0:
                dist = 1
            self.vx = dx / dist * self.speed
            self.vy = dy / dist * self.speed
        else:
            # Caso de seguridad: dispara hacia arriba
            self.vx = 0
            self.vy = -self.speed

    def _draw_bullet_sprite(self):
        surf = self.image
        surf.fill((0, 0, 0, 0))
        # halo exterior
        pygame.draw.circle(surf, (250, 230, 80), (6, 6), 6)
        # núcleo
        pygame.draw.circle(surf, (255, 255, 255), (6, 6), 3)

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy

        # Si sale de pantalla se destruye
        if (
            self.rect.bottom < 0
            or self.rect.top > HEIGHT
            or self.rect.right < 0
            or self.rect.left > WIDTH
        ):
            self.kill()


class EnemyBullet(pygame.sprite.Sprite):
    """Bala del boss (puede ser dirigida o de patrón)."""

    def __init__(self, x, y, vx, vy):
        super().__init__()
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        self._draw_enemy_bullet_sprite()
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = vx
        self.vy = vy

    def _draw_enemy_bullet_sprite(self):
        surf = self.image
        surf.fill((0, 0, 0, 0))
        pygame.draw.circle(surf, ORANGE, (5, 5), 5)
        pygame.draw.circle(surf, (255, 255, 255), (5, 4), 2)

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy

        if (
            self.rect.bottom < 0
            or self.rect.top > HEIGHT
            or self.rect.right < 0
            or self.rect.left > WIDTH
        ):
            self.kill()


class SpecialAttack(pygame.sprite.Sprite):
    """Rayo especial vertical del jugador (ataque X)."""

    def __init__(self, x):
        super().__init__()
        self.image = pygame.Surface((60, HEIGHT), pygame.SRCALPHA)
        self._draw_beam()
        self.rect = self.image.get_rect(center=(x, HEIGHT // 2))
        self.lifetime = 20  # frames

    def _draw_beam(self):
        surf = self.image
        surf.fill((0, 0, 0, 0))
        # capa exterior
        pygame.draw.rect(surf, (130, 0, 200, 140), (10, 0, 40, HEIGHT))
        # núcleo
        pygame.draw.rect(surf, (255, 255, 255, 220), (26, 0, 8, HEIGHT))

    def update(self):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()


class Boss(pygame.sprite.Sprite):
    def __init__(self, level):
        super().__init__()
        self.image = pygame.Surface((160, 90), pygame.SRCALPHA)
        self.level = level
        self._draw_boss_sprite()
        self.rect = self.image.get_rect(center=(WIDTH // 2, 100))

        # Estadísticas en función del nivel
        self.max_hp = 120 + level * 50
        self.hp = self.max_hp
        self.speed_x = 2 + level  # más rápido con nivel
        self.shoot_timer = 0
        self.shoot_interval = max(25 - level * 2, 8)  # dispara más rápido en niveles altos

        # Sistema de patrones
        self.pattern_time = 0
        self.pattern_duration = FPS * 3
        self.current_pattern = 0  # 0, 1 o 2

    def _draw_boss_sprite(self):
        surf = self.image
        surf.fill((0, 0, 0, 0))
        # cuerpo
        pygame.draw.rect(surf, (40, 0, 0), (0, 0, 160, 90))
        pygame.draw.rect(surf, RED, (6, 10, 148, 60))
        # "cascos" laterales
        pygame.draw.rect(surf, (90, 0, 0), (0, 20, 10, 40))
        pygame.draw.rect(surf, (90, 0, 0), (150, 20, 10, 40))
        # ojos
        pygame.draw.rect(surf, WHITE, (40, 30, 18, 12))
        pygame.draw.rect(surf, WHITE, (102, 30, 18, 12))
        pygame.draw.rect(surf, (255, 60, 60), (44, 34, 10, 4))
        pygame.draw.rect(surf, (255, 60, 60), (106, 34, 10, 4))
        # boca
        pygame.draw.rect(surf, (30, 0, 0), (50, 50, 60, 10))
        for i in range(6):
            pygame.draw.rect(surf, (200, 200, 200), (52 + i * 9, 52, 5, 6))

    def update(self):
        # Movimiento horizontal simple, rebotando en los bordes
        self.rect.x += self.speed_x
        if self.rect.left <= 0 or self.rect.right >= WIDTH:
            self.speed_x *= -1

        # Cambiar de patrón cada cierto tiempo
        self.pattern_time += 1
        if self.pattern_time >= self.pattern_duration:
            self.pattern_time = 0
            patterns = [0, 1, 2]
            patterns.remove(self.current_pattern)
            self.current_pattern = random.choice(patterns)

        if self.shoot_timer > 0:
            self.shoot_timer -= 1

    def maybe_shoot(self, player, enemy_bullets_group):
        """Dispara según el temporizador interno y el patrón actual."""
        if self.shoot_timer > 0:
            return

        self.shoot_timer = self.shoot_interval

        # Patrón 0: ráfaga dirigida
        if self.current_pattern == 0 and player is not None:
            speeds = [5, 5, 5]
            offsets = [0, -30, 30]
            for offset, spd in zip(offsets, speeds):
                px, py = player.rect.center
                sx = self.rect.centerx + offset
                sy = self.rect.bottom
                dx = px - sx
                dy = py - sy
                dist = math.hypot(dx, dy)
                if dist == 0:
                    dist = 1
                vx = dx / dist * spd
                vy = dy / dist * spd
                bullet = EnemyBullet(sx, sy, vx, vy)
                enemy_bullets_group.add(bullet)

        # Patrón 1: lluvia vertical de balas
        elif self.current_pattern == 1:
            for _ in range(7):
                x = random.randint(60, WIDTH - 60)
                y = self.rect.bottom
                vx = 0
                vy = 6
                bullet = EnemyBullet(x, y, vx, vy)
                enemy_bullets_group.add(bullet)

        # Patrón 2: círculo de balas radial
        elif self.current_pattern == 2:
            num_bullets = 14
            speed = 4.5
            for i in range(num_bullets):
                angle = (2 * math.pi / num_bullets) * i
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                bullet = EnemyBullet(self.rect.centerx, self.rect.centery, vx, vy)
                enemy_bullets_group.add(bullet)


# ----------------------------------------
# FONDO / BACKGROUND
# ----------------------------------------
def init_stars(num=60):
    stars = []
    for _ in range(num):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        speed = random.uniform(0.5, 2.0)
        size = random.randint(1, 3)
        stars.append([x, y, speed, size])
    return stars


def update_and_draw_background(surface, stars):
    # Fondo degradado tipo galaxia
    surface.fill((5, 5, 20))
    for i in range(0, HEIGHT, 40):
        shade = 5 + int(20 * (i / HEIGHT))
        pygame.draw.rect(surface, (shade, shade, 40 + shade), (0, i, WIDTH, 40))

    # Estrellas en movimiento
    for star in stars:
        x, y, speed, size = star
        y += speed
        if y > HEIGHT:
            y = 0
            x = random.randint(0, WIDTH)
            speed = random.uniform(0.5, 2.0)
            size = random.randint(1, 3)
        star[0], star[1], star[2], star[3] = x, y, speed, size
        pygame.draw.rect(surface, (200, 200, 255), (x, y, size, size))


# ----------------------------------------
# FUNCIONES DE DIBUJO (UI)
# ----------------------------------------
def draw_text(surface, text, font, color, x, y, center=False):
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(img, rect)


def draw_health_bar(surface, x, y, w, h, hp, max_hp, color):
    ratio = max(hp, 0) / max_hp
    pygame.draw.rect(surface, GREY, (x, y, w, h))
    pygame.draw.rect(surface, color, (x, y, w * ratio, h))


def draw_title_screen(stars):
    update_and_draw_background(SCREEN, stars)
    draw_text(SCREEN, "CHRONIQUES PIXEL", BIG_FONT, YELLOW, WIDTH // 2, HEIGHT // 4, center=True)
    draw_text(SCREEN, "Assaut des Boss", FONT, WHITE, WIDTH // 2, HEIGHT // 4 + 60, center=True)
    draw_text(SCREEN, "By Leziak", FONT, CYAN, WIDTH // 2, HEIGHT // 4 + 100, center=True)

    draw_text(SCREEN, "CONTROLES", FONT, WHITE, WIDTH // 2, HEIGHT // 2 - 30, center=True)
    draw_text(SCREEN, "Fleches : se deplacer", FONT, WHITE, WIDTH // 2, HEIGHT // 2, center=True)
    draw_text(SCREEN, "Shift : deplacement lent", FONT, WHITE, WIDTH // 2, HEIGHT // 2 + 30, center=True)
    draw_text(SCREEN, "Ctrl : deplacement rapide", FONT, WHITE, WIDTH // 2, HEIGHT // 2 + 60, center=True)
    draw_text(SCREEN, "Z : tir auto vers le boss", FONT, WHITE, WIDTH // 2, HEIGHT // 2 + 90, center=True)
    draw_text(SCREEN, "X : attaque speciale (laser)", FONT, WHITE, WIDTH // 2, HEIGHT // 2 + 120, center=True)
    draw_text(SCREEN, "M : mute musique | B : pause musique", FONT, WHITE, WIDTH // 2, HEIGHT // 2 + 150, center=True)

    draw_text(SCREEN, "Appuie sur ENTREE pour commencer", FONT, GREEN, WIDTH // 2, HEIGHT - 80, center=True)


def draw_pause_overlay():
    # Fondo semitransparente
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    SCREEN.blit(overlay, (0, 0))

    draw_text(SCREEN, "PAUSE", BIG_FONT, YELLOW, WIDTH // 2, HEIGHT // 3, center=True)
    draw_text(SCREEN, "R : reprendre la partie", FONT, WHITE, WIDTH // 2, HEIGHT // 2, center=True)
    draw_text(SCREEN, "T : retour a l'ecran titre", FONT, WHITE, WIDTH // 2, HEIGHT // 2 + 40, center=True)
    draw_text(SCREEN, "M : mute musique | B : pause musique", FONT, WHITE, WIDTH // 2, HEIGHT // 2 + 80, center=True)


def draw_game_over(level, stars):
    update_and_draw_background(SCREEN, stars)
    draw_text(SCREEN, "GAME OVER", BIG_FONT, RED, WIDTH // 2, HEIGHT // 3, center=True)
    draw_text(SCREEN, f"Tu es arrive au niveau {level}", FONT, WHITE, WIDTH // 2, HEIGHT // 2, center=True)
    draw_text(SCREEN, "Appuie sur ENTREE pour retourner au titre", FONT, WHITE, WIDTH // 2, HEIGHT // 2 + 60, center=True)


def draw_hud(player, boss, level):
    # HUD del jugador
    draw_text(SCREEN, "PV", FONT, WHITE, 20, 20)
    draw_health_bar(SCREEN, 60, 22, 200, 16, player.hp, player.max_hp, GREEN)

    draw_text(SCREEN, f"Pouvoirs (X) : {player.special_charges}", FONT, WHITE, 20, 50)
    draw_text(SCREEN, f"Niveau : {level}", FONT, WHITE, WIDTH - 220, 20)

    # HP del boss con cambio de color si está muy bajo
    if boss is not None:
        boss_color = RED if boss.hp > boss.max_hp * 0.3 else ORANGE
        draw_text(SCREEN, "Boss", FONT, WHITE, WIDTH // 2 - 80, 20)
        draw_health_bar(SCREEN, WIDTH // 2, 22, 200, 16, boss.hp, boss.max_hp, boss_color)


# ----------------------------------------
# SISTEMA DE MEJORAS (UPGRADES)
# ----------------------------------------
def get_upgrade_options(player):
    """
    Devuelve una lista de 3 mejoras a elegir.
    Cada mejora es un dict con:
      - 'name'
      - 'desc'
      - 'apply' (función que modifica al jugador)
    """
    def up_fire_rate(p):
        p.shoot_cooldown_max = max(3, p.shoot_cooldown_max - 2)

    def up_bullet_speed(p):
        p.bullet_speed += 2

    def up_move_speed(p):
        p.base_speed += 1
        p.fast_speed += 1

    def up_hp(p):
        p.max_hp += 20
        p.hp = p.max_hp

    def up_special_charge(p):
        p.special_charges += 1

    all_upgrades = [
        {
            "name": "Cadence de tir",
            "desc": "Tirs plus rapides (Z)",
            "apply": up_fire_rate,
        },
        {
            "name": "Vitesse des projectiles",
            "desc": "Les balles voyagent plus vite",
            "apply": up_bullet_speed,
        },
        {
            "name": "Vitesse de deplacement",
            "desc": "Tu te deplaces plus vite",
            "apply": up_move_speed,
        },
        {
            "name": "PV max +20",
            "desc": "Plus de points de vie",
            "apply": up_hp,
        },
        {
            "name": "Charge speciale +1",
            "desc": "Une attaque X supplementaire",
            "apply": up_special_charge,
        },
    ]

    options = random.sample(all_upgrades, 3)
    return options


def draw_upgrade_screen(stars, upgrade_options, mouse_pos):
    update_and_draw_background(SCREEN, stars)
    draw_text(SCREEN, "AMELIORATION", BIG_FONT, CYAN, WIDTH // 2, 80, center=True)
    draw_text(SCREEN, "Choisis une amelioration avec la souris", FONT, WHITE, WIDTH // 2, 130, center=True)

    cards = []
    card_width = 230
    card_height = 150
    margin = 40
    total_width = 3 * card_width + 2 * margin
    start_x = (WIDTH - total_width) // 2
    y = HEIGHT // 2 - card_height // 2

    for i, upgrade in enumerate(upgrade_options):
        x = start_x + i * (card_width + margin)
        rect = pygame.Rect(x, y, card_width, card_height)

        # Hover
        hovered = rect.collidepoint(mouse_pos)
        bg_color = (25, 25, 60) if not hovered else (40, 40, 90)
        border_color = CYAN if not hovered else YELLOW
        border_width = 3 if not hovered else 5

        pygame.draw.rect(SCREEN, bg_color, rect)
        pygame.draw.rect(SCREEN, border_color, rect, border_width)

        draw_text(SCREEN, upgrade["name"], FONT, YELLOW, x + 10, y + 10, center=False)
        draw_text(SCREEN, upgrade["desc"], FONT, WHITE, x + 10, y + 60, center=False)

        cards.append(rect)

    draw_text(SCREEN, "Clique sur une carte", FONT, WHITE, WIDTH // 2, HEIGHT - 60, center=True)
    return cards


# ----------------------------------------
# BUCLE PRINCIPAL DEL JUEGO
# ----------------------------------------
# ----------------------------------------
# BUCLE PRINCIPAL DEL JUEGO
# ----------------------------------------
def main():
    start_music()

    state = STATE_TITLE
    level = 1

    player = None
    boss = None
    bullets_group = pygame.sprite.Group()
    enemy_bullets_group = pygame.sprite.Group()
    special_group = pygame.sprite.Group()

    stars = init_stars()

    # Para sistema de mejoras
    upgrade_options = []
    upgrade_cards = []

    def start_new_game():
        nonlocal player, boss, bullets_group, enemy_bullets_group, special_group, level
        level = 1
        player = Player()
        boss = Boss(level)

        bullets_group = pygame.sprite.Group()
        enemy_bullets_group = pygame.sprite.Group()
        special_group = pygame.sprite.Group()

    def next_level():
        nonlocal player, boss, bullets_group, enemy_bullets_group, special_group, level, state, upgrade_options
        level += 1
        # Pantalla de mejoras antes del nuevo boss
        upgrade_options = get_upgrade_options(player)
        state = STATE_UPGRADE

        bullets_group.empty()
        enemy_bullets_group.empty()
        special_group.empty()

    def apply_upgrade_and_spawn_boss(chosen_upgrade):
        nonlocal player, boss, level, state
        # Aplicar mejora
        chosen_upgrade["apply"](player)
        # Nuevo boss
        boss = Boss(level)
        state = STATE_PLAYING

    running = True
    while running:
        CLOCK.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        # ----------------------------------
        # GESTIÓN DE EVENTOS
        # ----------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Controles globales de música
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    toggle_mute_music()
                if event.key == pygame.K_b:
                    toggle_pause_music()

            # Estados
            if state == STATE_TITLE:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    start_new_game()
                    state = STATE_PLAYING

            elif state == STATE_PLAYING:
                if event.type == pygame.KEYDOWN:
                    # Pausa
                    if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                        state = STATE_PAUSED
                    # Poder especial X
                    if event.key == pygame.K_x and player is not None:
                        player.use_special(special_group)

            elif state == STATE_PAUSED:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        state = STATE_PLAYING
                    elif event.key == pygame.K_t:
                        state = STATE_TITLE

            elif state == STATE_GAME_OVER:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    state = STATE_TITLE

            elif state == STATE_UPGRADE:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for idx, rect in enumerate(upgrade_cards):
                        if rect.collidepoint(mouse_pos):
                            chosen_upgrade = upgrade_options[idx]
                            apply_upgrade_and_spawn_boss(chosen_upgrade)
                            break

        # ----------------------------------
        # LÓGICA SEGÚN ESTADO
        # ----------------------------------
        if state == STATE_TITLE:
            draw_title_screen(stars)

        elif state == STATE_PLAYING:
            keys = pygame.key.get_pressed()
            update_and_draw_background(SCREEN, stars)

            # Player
            if player is not None:
                player.update(keys)
                if keys[pygame.K_z] and player.can_shoot():
                    bullet = player.shoot(boss)
                    bullets_group.add(bullet)

            # Boss y disparos
            if boss is not None:
                boss.update()
                boss.maybe_shoot(player, enemy_bullets_group)

            bullets_group.update()
            enemy_bullets_group.update()
            special_group.update()

            # Colisiones con boss
            if boss is not None:
                hits_on_boss = pygame.sprite.spritecollide(boss, bullets_group, True)
                for _ in hits_on_boss:
                    boss.hp -= player.bullet_damage

                hits_special_on_boss = pygame.sprite.spritecollide(boss, special_group, False)
                for _ in hits_special_on_boss:
                    boss.hp -= 4  # daño por frame del láser

            # Láser limpia balas enemigas
            for beam in special_group:
                pygame.sprite.spritecollide(beam, enemy_bullets_group, True)

            # Boss muerto
            if boss is not None and boss.hp <= 0:
                next_level()

            # Colisiones con jugador
            if player is not None:
                hits_on_player = pygame.sprite.spritecollide(player, enemy_bullets_group, True)
                for _ in hits_on_player:
                    player.hp -= 10

                if player.hp <= 0:
                    state = STATE_GAME_OVER

            # Dibujo
            if boss is not None:
                SCREEN.blit(boss.image, boss.rect)
            if player is not None:
                SCREEN.blit(player.image, player.rect)

            bullets_group.draw(SCREEN)
            enemy_bullets_group.draw(SCREEN)
            special_group.draw(SCREEN)
            if player is not None:
                draw_hud(player, boss, level)

        elif state == STATE_PAUSED:
            # Dibujar escena congelada
            update_and_draw_background(SCREEN, stars)
            if boss is not None:
                SCREEN.blit(boss.image, boss.rect)
            if player is not None:
                SCREEN.blit(player.image, player.rect)
            bullets_group.draw(SCREEN)
            enemy_bullets_group.draw(SCREEN)
            special_group.draw(SCREEN)
            if player is not None:
                draw_hud(player, boss, level)
            draw_pause_overlay()

        elif state == STATE_GAME_OVER:
            draw_game_over(level, stars)

        elif state == STATE_UPGRADE:
            upgrade_cards = draw_upgrade_screen(stars, upgrade_options, mouse_pos)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
