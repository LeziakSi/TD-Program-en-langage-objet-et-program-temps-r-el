import sys
import random
import pygame

from config import (
    WIDTH,
    HEIGHT,
    FPS,
    STATE_TITLE,
    STATE_PLAYING,
    STATE_PAUSED,
    STATE_GAME_OVER,
    STATE_UPGRADE,
)
from music import start_music, toggle_mute_music, toggle_pause_music
from background import init_stars, update_and_draw_background
from entities import Player, Boss
from ui import (
    draw_title_screen,
    draw_pause_overlay,
    draw_game_over,
    draw_hud,
    draw_upgrade_screen,
)
from upgrades import get_upgrade_options


def main():
    pygame.init()
    SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chroniques Pixel - Assaut des Boss")
    CLOCK = pygame.time.Clock()

    # Superficie donde se dibuja el mundo (para aplicar screen shake)
    WORLD = pygame.Surface((WIDTH, HEIGHT))

    start_music()

    state = STATE_TITLE
    level = 1
    score = 0

    # Intensidad actual de temblor de cámara
    shake = 0

    player = None
    boss = None
    bullets_group = pygame.sprite.Group()
    enemy_bullets_group = pygame.sprite.Group()
    special_group = pygame.sprite.Group()
    minions_group = pygame.sprite.Group()

    stars = init_stars()

    # Sistema de mejoras
    upgrade_options = []
    upgrade_cards = []

    # -------------------------------------------------
    # FUNCIONES INTERNAS
    # -------------------------------------------------
    def start_new_game():
        nonlocal player, boss, bullets_group, enemy_bullets_group, special_group, minions_group
        nonlocal level, score, shake
        level = 1
        score = 0
        shake = 0

        player = Player()
        boss = Boss(level)

        bullets_group = pygame.sprite.Group()
        enemy_bullets_group = pygame.sprite.Group()
        special_group = pygame.sprite.Group()
        minions_group = pygame.sprite.Group()

    def next_level():
        nonlocal player, boss, bullets_group, enemy_bullets_group, special_group, minions_group
        nonlocal level, state, upgrade_options, shake

        level += 1
        shake = 0

        # Mejorar el modo de disparo del jugador según el nivel
        if player is not None:
            # 1 -> triple; 2 -> ondas + normal
            player.fire_mode = min(2, level - 1)

        upgrade_options = get_upgrade_options(player)
        state = STATE_UPGRADE

        bullets_group.empty()
        enemy_bullets_group.empty()
        special_group.empty()
        minions_group.empty()

    def apply_upgrade_and_spawn_boss(chosen_upgrade):
        nonlocal player, boss, level, state
        chosen_upgrade["apply"](player)
        boss = Boss(level)
        state = STATE_PLAYING

    # -------------------------------------------------
    # BUCLE PRINCIPAL
    # -------------------------------------------------
    running = True
    while running:
        CLOCK.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        # ----------------------------------
        # EVENTOS
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
                    if event.key in (pygame.K_p, pygame.K_ESCAPE):
                        state = STATE_PAUSED
                    # Poder especial
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
        # LÓGICA Y DIBUJO SEGÚN ESTADO
        # ----------------------------------
        if state == STATE_TITLE:
            draw_title_screen(SCREEN, stars)

        elif state == STATE_PLAYING:
            keys = pygame.key.get_pressed()

            # Dibujamos TODO el mundo en la superficie WORLD
            update_and_draw_background(WORLD, stars)

            # Screen shake: calcular offset de la cámara
            if shake > 0:
                offset_x = random.randint(-shake, shake)
                offset_y = random.randint(-shake, shake)
                # el temblor se va reduciendo
                shake = max(0, shake - 1)
            else:
                offset_x = offset_y = 0

            # --- Player ---
            if player is not None:
                player.update(keys)
                if keys[pygame.K_z] and player.can_shoot():
                    new_bullets = player.shoot(boss)
                    # añadimos trail a las nuevas balas
                    for b in new_bullets:
                        b.trail = []
                    bullets_group.add(*new_bullets)

            # --- Boss y disparos ---
            if boss is not None:
                boss.update()
                boss.maybe_shoot(player, enemy_bullets_group, minions_group)

            bullets_group.update()
            enemy_bullets_group.update()
            special_group.update()
            minions_group.update()

            # Actualizamos trail de balas del jugador
            for bullet in bullets_group:
                if not hasattr(bullet, "trail"):
                    bullet.trail = []
                bullet.trail.append(bullet.rect.center)
                if len(bullet.trail) > 6:
                    bullet.trail.pop(0)

            # --- Colisiones con boss ---
            if boss is not None:
                hits_on_boss = pygame.sprite.spritecollide(boss, bullets_group, True)
                if hits_on_boss:
                    boss.hp -= player.bullet_damage * len(hits_on_boss)
                    score += 10 * len(hits_on_boss)
                    setattr(boss, "flash_timer", 6)
                    shake = min(shake + 3, 14)

                hits_special_on_boss = pygame.sprite.spritecollide(boss, special_group, False)
                if hits_special_on_boss:
                    boss.hp -= 4 * len(hits_special_on_boss)
                    score += 4 * len(hits_special_on_boss)
                    setattr(boss, "flash_timer", 4)
                    shake = min(shake + 2, 14)

            # Láser limpia balas enemigas
            for beam in special_group:
                pygame.sprite.spritecollide(beam, enemy_bullets_group, True)

            # --- Balas del jugador contra minions ---
            for minion in list(minions_group):
                hits = pygame.sprite.spritecollide(minion, bullets_group, True)
                if hits:
                    minion.hp -= player.bullet_damage * len(hits)
                    setattr(minion, "flash_timer", 6)
                    shake = min(shake + 2, 12)
                    if minion.hp <= 0:
                        minion.kill()
                        score += 50  # recompensa por minion

            # --- Boss muerto, pasar de nivel ---
            if boss is not None and boss.hp <= 0:
                score += 200 * level  # bonus por matar al boss
                next_level()

            # --- Daño al jugador ---
            if player is not None:
                # Balas del boss
                if player.invincible <= 0:
                    hits_on_player = pygame.sprite.spritecollide(
                        player, enemy_bullets_group, True
                    )
                    if hits_on_player:
                        player.hp -= 10 * len(hits_on_player)
                        player.invincible = FPS  # ~1 segundo invencible
                        setattr(player, "flash_timer", 10)
                        shake = min(shake + 6, 18)
                else:
                    pygame.sprite.spritecollide(player, enemy_bullets_group, True)

                # Choque con minions
                hits_minions_player = pygame.sprite.spritecollide(
                    player, minions_group, False
                )
                if hits_minions_player and player.invincible <= 0:
                    player.hp -= 20
                    player.invincible = FPS
                    setattr(player, "flash_timer", 12)
                    shake = min(shake + 8, 20)
                    for m in hits_minions_player:
                        m.kill()

                if player.hp <= 0:
                    state = STATE_GAME_OVER

            # --- Reducir timers de flash ---
            for obj in [boss, player, *list(minions_group)]:
                if obj is None:
                    continue
                if hasattr(obj, "flash_timer") and obj.flash_timer > 0:
                    obj.flash_timer -= 1

            # -------------------------------------------------
            # DIBUJO DE ENTIDADES EN WORLD (SIN OFFSET)
            # -------------------------------------------------
            # Boss
            if boss is not None:
                WORLD.blit(boss.image, boss.rect)
                if getattr(boss, "flash_timer", 0) > 0:
                    flash = pygame.Surface(boss.image.get_size(), pygame.SRCALPHA)
                    flash.fill((255, 255, 255, 150))
                    WORLD.blit(flash, boss.rect)

            # Minions
            for m in minions_group:
                WORLD.blit(m.image, m.rect)
                if getattr(m, "flash_timer", 0) > 0:
                    flash = pygame.Surface(m.image.get_size(), pygame.SRCALPHA)
                    flash.fill((255, 255, 255, 150))
                    WORLD.blit(flash, m.rect)

            # Player
            if player is not None:
                # sombra
                shadow = pygame.Surface((40, 12), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow, (0, 0, 0, 130), (0, 0, 40, 12))
                WORLD.blit(
                    shadow,
                    (player.rect.centerx - 20, player.rect.bottom - 6),
                )

                # parpadeo cuando es invencible
                if player.invincible > 0 and (pygame.time.get_ticks() // 80) % 2 == 0:
                    pass
                else:
                    WORLD.blit(player.image, player.rect)
                    if getattr(player, "flash_timer", 0) > 0:
                        flash = pygame.Surface(player.image.get_size(), pygame.SRCALPHA)
                        flash.fill((255, 255, 255, 150))
                        WORLD.blit(flash, player.rect)

            # Balas del jugador con trail
            for b in bullets_group:
                # trail
                if hasattr(b, "trail"):
                    for i, pos in enumerate(b.trail):
                        alpha = 40 + i * 20
                        s = pygame.Surface((8, 8), pygame.SRCALPHA)
                        pygame.draw.circle(s, (255, 255, 200, alpha), (4, 4), 3)
                        WORLD.blit(s, (pos[0] - 4, pos[1] - 4))

                WORLD.blit(b.image, b.rect)

            # Balas del boss
            for eb in enemy_bullets_group:
                WORLD.blit(eb.image, eb.rect)

            # Láser especial
            for s in special_group:
                WORLD.blit(s.image, s.rect)

            # -------------------------------------------------
            # APLICAR SCREEN SHAKE: blitear WORLD a SCREEN con offset
            # -------------------------------------------------
            SCREEN.fill((0, 0, 0))
            SCREEN.blit(WORLD, (offset_x, offset_y))

            # HUD (se dibuja encima, sin sacudida)
            if player is not None:
                draw_hud(SCREEN, player, boss, level, score)

        elif state == STATE_PAUSED:
            # En pausa, dibujamos escena "congelada" sin sacudida
            update_and_draw_background(SCREEN, stars)
            if boss is not None:
                SCREEN.blit(boss.image, boss.rect)
            minions_group.draw(SCREEN)
            if player is not None:
                SCREEN.blit(player.image, player.rect)
            bullets_group.draw(SCREEN)
            enemy_bullets_group.draw(SCREEN)
            special_group.draw(SCREEN)
            if player is not None:
                draw_hud(SCREEN, player, boss, level, score)
            draw_pause_overlay(SCREEN)

        elif state == STATE_GAME_OVER:
            draw_game_over(SCREEN, level, stars)

        elif state == STATE_UPGRADE:
            upgrade_cards = draw_upgrade_screen(SCREEN, stars, upgrade_options, mouse_pos)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
