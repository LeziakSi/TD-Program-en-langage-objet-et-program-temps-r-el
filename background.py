import pygame
import random
from config import WIDTH, HEIGHT


def init_stars(num_far=55, num_near=35):
    """
    Crea dos capas de estrellas: lejanas (más lentas) y cercanas (más rápidas).
    Cada estrella: [x, y, speed, size, layer]
    """
    stars = []

    # Capa lejana
    for _ in range(num_far):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        speed = random.uniform(0.2, 0.7)
        size = random.randint(1, 2)
        stars.append([x, y, speed, size, 0])

    # Capa cercana
    for _ in range(num_near):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        speed = random.uniform(0.8, 2.0)
        size = random.randint(2, 3)
        stars.append([x, y, speed, size, 1])

    return stars


def update_and_draw_background(surface, stars):
    # --- Fondo degradado tipo galaxia ---
    top_color = (5, 5, 25)
    mid_color = (30, 10, 50)
    bottom_color = (5, 5, 40)

    for i in range(HEIGHT):
        t = i / HEIGHT
        if t < 0.5:
            tt = t / 0.5
            r = int(top_color[0] + (mid_color[0] - top_color[0]) * tt)
            g = int(top_color[1] + (mid_color[1] - top_color[1]) * tt)
            b = int(top_color[2] + (mid_color[2] - top_color[2]) * tt)
        else:
            tt = (t - 0.5) / 0.5
            r = int(mid_color[0] + (bottom_color[0] - mid_color[0]) * tt)
            g = int(mid_color[1] + (bottom_color[1] - mid_color[1]) * tt)
            b = int(mid_color[2] + (bottom_color[2] - mid_color[2]) * tt)
        pygame.draw.line(surface, (r, g, b), (0, i), (WIDTH, i))

    # Curvatura tipo planeta + nebulosas suaves
    planet = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
    pygame.draw.ellipse(planet, (40, 10, 60, 180), (-WIDTH // 2, HEIGHT // 3, WIDTH * 2, HEIGHT))
    pygame.draw.ellipse(planet, (20, 40, 80, 120), (-WIDTH // 4, HEIGHT // 2, WIDTH * 2, HEIGHT))
    surface.blit(planet, (0, 0))

    nebula = pygame.Surface((WIDTH * 2, HEIGHT), pygame.SRCALPHA)
    pygame.draw.ellipse(nebula, (120, 40, 180, 70), (-WIDTH // 2, -HEIGHT // 4, WIDTH * 2, HEIGHT))
    pygame.draw.ellipse(nebula, (80, 160, 220, 60), (-WIDTH // 3, HEIGHT // 4, WIDTH * 2, HEIGHT))
    surface.blit(nebula, (0, 0))

    # --- Estrellas con parallax y un poco de glow ---
    for star in stars:
        x, y, speed, size, layer = star

        y += speed
        if y > HEIGHT:
            y = 0
            x = random.randint(0, WIDTH)
            if layer == 0:
                speed = random.uniform(0.2, 0.7)
                size = random.randint(1, 2)
            else:
                speed = random.uniform(0.8, 2.0)
                size = random.randint(2, 3)

        star[0], star[1], star[2], star[3] = x, y, speed, size

        if layer == 0:
            color = (200, 200, 255)
        else:
            color = (255, 255, 255)

        # glow ligero en las estrellas cercanas
        if layer == 1:
            glow = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow, (color[0], color[1], color[2], 80), (size * 2, size * 2), size * 2)
            surface.blit(glow, (x - size * 2, y - size * 2))

        pygame.draw.rect(surface, color, (x, y, size, size))
