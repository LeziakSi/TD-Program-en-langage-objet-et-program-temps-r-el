import pygame
from config import (
    WIDTH,
    HEIGHT,
    FONT,
    BIG_FONT,
    WHITE,
    GREEN,
    RED,
    ORANGE,
    YELLOW,
    GREY,
    CYAN,
)
from background import update_and_draw_background


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
    pygame.draw.rect(surface, GREY, (x, y, w, h), border_radius=6)
    pygame.draw.rect(surface, color, (x, y, w * ratio, h), border_radius=6)


def draw_title_screen(surface, stars):
    update_and_draw_background(surface, stars)

    # panel central con fade-in suave
    panel = pygame.Surface((int(WIDTH * 0.7), int(HEIGHT * 0.6)), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 160))
    rect = panel.get_rect(center=(WIDTH // 2, HEIGHT // 2))

    alpha = min(255, int(pygame.time.get_ticks() * 0.15))
    panel.set_alpha(alpha)
    surface.blit(panel, rect.topleft)
    pygame.draw.rect(surface, CYAN, rect, 2)

    draw_text(surface, "CHRONIQUES PIXEL", BIG_FONT, YELLOW, WIDTH // 2, rect.top + 60, center=True)
    draw_text(surface, "Assaut des Boss", FONT, WHITE, WIDTH // 2, rect.top + 110, center=True)
    draw_text(surface, "By Leziak",        FONT, CYAN,  WIDTH // 2, rect.top + 145, center=True)

    draw_text(surface, "CONTROLES",                 FONT, WHITE, WIDTH // 2, rect.top + 190, center=True)
    draw_text(surface, "Fleches : se deplacer",     FONT, WHITE, WIDTH // 2, rect.top + 220, center=True)
    draw_text(surface, "Shift : deplacement lent",  FONT, WHITE, WIDTH // 2, rect.top + 250, center=True)
    draw_text(surface, "Ctrl : deplacement rapide", FONT, WHITE, WIDTH // 2, rect.top + 280, center=True)
    draw_text(surface, "Z : tir auto vers le boss", FONT, WHITE, WIDTH // 2, rect.top + 310, center=True)
    draw_text(surface, "X : attaque speciale (laser)", FONT, WHITE, WIDTH // 2, rect.top + 340, center=True)

    # AHORA SÍ, DOS LÍNEAS SEPARADAS, SIN ENCIMARSE
    draw_text(surface, "Appuie sur ENTREE pour commencer",
              FONT, GREEN, WIDTH // 2, rect.top + 370, center=True)

    draw_text(surface, "M : mute musique | B : pause musique",
              FONT, WHITE, WIDTH // 2, rect.top + 400, center=True)


def draw_pause_overlay(surface):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))

    panel = pygame.Surface((int(WIDTH * 0.5), int(HEIGHT * 0.4)), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 200))
    rect = panel.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    surface.blit(panel, rect.topleft)
    pygame.draw.rect(surface, CYAN, rect, 2)

    draw_text(surface, "PAUSE", BIG_FONT, YELLOW, WIDTH // 2, rect.top + 40, center=True)
    draw_text(surface, "R : reprendre la partie", FONT, WHITE, WIDTH // 2, rect.top + 110, center=True)
    draw_text(surface, "T : retour a l'ecran titre", FONT, WHITE, WIDTH // 2, rect.top + 145, center=True)
    draw_text(surface, "M : mute musique | B : pause musique", FONT, WHITE, WIDTH // 2, rect.top + 180, center=True)


def draw_game_over(surface, level, stars):
    update_and_draw_background(surface, stars)

    panel = pygame.Surface((int(WIDTH * 0.5), int(HEIGHT * 0.4)), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 200))
    rect = panel.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    surface.blit(panel, rect.topleft)
    pygame.draw.rect(surface, RED, rect, 2)

    draw_text(surface, "GAME OVER", BIG_FONT, RED, WIDTH // 2, rect.top + 50, center=True)
    draw_text(surface, f"Tu es arrive au niveau {level}", FONT, WHITE, WIDTH // 2, rect.top + 120, center=True)
    draw_text(surface, "Appuie sur ENTREE pour retourner au titre", FONT, WHITE, WIDTH // 2, rect.top + 170, center=True)


def draw_hud(surface, player, boss, level, score):
    # Panel translúcido arriba
    panel = pygame.Surface((WIDTH, 80), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 140))
    surface.blit(panel, (0, 0))
    pygame.draw.line(surface, CYAN, (0, 80), (WIDTH, 80), 2)

    # HUD jugador
    draw_text(surface, "PV", FONT, WHITE, 20, 20)
    draw_health_bar(surface, 60, 22, 220, 16, player.hp, player.max_hp, GREEN)

    draw_text(surface, f"Pouvoirs (X) : {player.special_charges}", FONT, WHITE, 20, 50)
    draw_text(surface, f"Niveau : {level}", FONT, WHITE, WIDTH - 230, 20)
    draw_text(surface, f"Score : {score}", FONT, CYAN, WIDTH - 230, 50)

    # HP del boss (centrado)
    if boss is not None:
        boss_color = RED if boss.hp > boss.max_hp * 0.3 else ORANGE
        bar_w = 260
        bar_x = (WIDTH - bar_w) // 2

        draw_text(surface, "Boss", FONT, WHITE, bar_x - 60, 20)
        # sombra de la barra
        pygame.draw.rect(surface, (0, 0, 0), (bar_x - 2, 20, bar_w + 4, 20), border_radius=8)
        # base gris
        pygame.draw.rect(surface, (60, 60, 60), (bar_x, 22, bar_w, 16), border_radius=6)
        # vida real
        ratio = max(boss.hp, 0) / boss.max_hp
        pygame.draw.rect(surface, boss_color, (bar_x, 22, bar_w * ratio, 16), border_radius=6)


def draw_upgrade_screen(surface, stars, upgrade_options, mouse_pos):
    update_and_draw_background(surface, stars)
    draw_text(surface, "AMELIORATION", BIG_FONT, CYAN, WIDTH // 2, 80, center=True)
    draw_text(surface, "Choisis une amelioration avec la souris",
              FONT, WHITE, WIDTH // 2, 130, center=True)

    cards = []
    card_width = 230
    card_height = 150
    margin = 40
    total_width = 3 * card_width + 2 * margin
    start_x = (WIDTH - total_width) // 2
    y = HEIGHT // 2 - card_height // 2

    # helper para partir el texto en varias líneas que quepan en la tarjeta
    def wrap_text(text, font, max_width):
        words = text.split(" ")
        lines = []
        current = ""

        for w in words:
            test = (current + " " + w).strip()
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = w
        if current:
            lines.append(current)
        return lines

    for i, upgrade in enumerate(upgrade_options):
        x = start_x + i * (card_width + margin)
        rect = pygame.Rect(x, y, card_width, card_height)

        hovered = rect.collidepoint(mouse_pos)
        bg_color = (25, 25, 60) if not hovered else (40, 40, 90)
        border_color = CYAN if not hovered else YELLOW
        border_width = 3 if not hovered else 5

        pygame.draw.rect(surface, bg_color, rect, border_radius=10)
        pygame.draw.rect(surface, border_color, rect, border_width, border_radius=10)

        # título (casi seguro cabe en una línea)
        draw_text(surface, upgrade["name"], FONT, YELLOW, x + 10, y + 10, center=False)

        # descripción envuelta a varias líneas dentro del cuadro
        max_text_width = card_width - 20
        lines = wrap_text(upgrade["desc"], FONT, max_text_width)
        line_y = y + 55
        line_h = FONT.get_linesize()
        for line in lines:
            draw_text(surface, line, FONT, WHITE, x + 10, line_y, center=False)
            line_y += line_h

        cards.append(rect)

    draw_text(surface, "Clique sur une carte", FONT, WHITE, WIDTH // 2, HEIGHT - 60, center=True)
    return cards

