import pygame
import math
import random
from config import WIDTH, HEIGHT, GREEN, WHITE, BLUE, ORANGE, RED, FPS


# ============================================================
# JUGADOR
# ============================================================
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        self._draw_player_sprite()
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT - 80))

        self.base_speed = 5
        self.slow_speed = 2
        self.fast_speed = 8
        self.max_hp = 100
        self.hp = self.max_hp

        self.shoot_cooldown = 0
        self.shoot_cooldown_max = 10
        self.special_cooldown = 0
        self.special_charges = 3  # Cargas del poder especial (X)

        # Mejoras
        self.bullet_speed = 9
        self.bullet_damage = 8

        # Invencibilidad tras recibir daño (en frames)
        self.invincible = 0

        # Modo de disparo (0 = normal, 1 = triple, 2 = normal + ondas)
        self.fire_mode = 0

    def _draw_player_sprite(self):
        surf = self.image
        surf.fill((0, 0, 0, 0))

        # Glow exterior
        glow = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (80, 255, 140, 90), (-4, 4, 40, 26))
        surf.blit(glow, (0, 0))

        # contorno oscuro
        pygame.draw.rect(surf, (5, 20, 5), (0, 0, 32, 32), border_radius=6)

        # cuerpo principal
        pygame.draw.rect(surf, GREEN, (3, 6, 26, 22), border_radius=6)

        # pecho brillante
        pygame.draw.rect(surf, (160, 255, 200), (10, 10, 12, 8), border_radius=4)

        # ojos
        pygame.draw.rect(surf, (230, 255, 255), (8, 18, 5, 5), border_radius=2)
        pygame.draw.rect(surf, (230, 255, 255), (19, 18, 5, 5), border_radius=2)
        pygame.draw.rect(surf, BLUE, (9, 19, 3, 3), border_radius=2)
        pygame.draw.rect(surf, BLUE, (20, 19, 3, 3), border_radius=2)

        # sombreado inferior
        pygame.draw.rect(surf, (10, 50, 20), (3, 22, 26, 6), border_radius=3)

    def update(self, keys):
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

        self.rect.left = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, WIDTH)
        self.rect.top = max(self.rect.top, 0)
        self.rect.bottom = min(self.rect.bottom, HEIGHT)

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.special_cooldown > 0:
            self.special_cooldown -= 1
        if self.invincible > 0:
            self.invincible -= 1

    def can_shoot(self):
        return self.shoot_cooldown <= 0

    def shoot(self, boss):
        """
        Devuelve una lista de balas creadas según el modo de disparo:
        fire_mode 0: una bala normal teledirigida
        fire_mode 1: triple disparo en abanico hacia el boss
        fire_mode 2: bala normal + dos balas en onda vertical
        """
        self.shoot_cooldown = self.shoot_cooldown_max

        bullets = []
        x, y = self.rect.center

        # Determinar ángulo hacia el boss (si existe)
        if boss is not None:
            bx, by = boss.rect.center
            angle_to_boss = math.atan2(by - y, bx - x)
        else:
            angle_to_boss = -math.pi / 2  # hacia arriba

        if self.fire_mode == 0:
            # Disparo normal auto-aim
            bullets.append(Bullet(x, y, boss, self.bullet_speed, kind="normal"))

        elif self.fire_mode == 1:
            # Triple disparo en abanico
            spread = 0.28  # ~16 grados
            angles = [angle_to_boss, angle_to_boss - spread, angle_to_boss + spread]
            for ang in angles:
                bullets.append(Bullet(x, y, boss, self.bullet_speed, kind="spread", angle=ang))

        else:
            # Modo 2: una bala normal + dos ondas verticales
            bullets.append(Bullet(x, y, boss, self.bullet_speed, kind="normal"))
            bullets.append(Bullet(x - 8, y, None, self.bullet_speed - 1, kind="wave"))
            bullets.append(Bullet(x + 8, y, None, self.bullet_speed - 1, kind="wave"))

        return bullets

    def can_use_special(self):
        return self.special_charges > 0 and self.special_cooldown <= 0

    def use_special(self, special_group):
        if not self.can_use_special():
            return

        beam = SpecialAttack(self.rect.centerx)
        special_group.add(beam)

        self.special_charges -= 1
        self.special_cooldown = FPS * 2  # 2 segundos


# ============================================================
# BALAS DEL JUGADOR
# ============================================================
class Bullet(pygame.sprite.Sprite):
    """
    Bala del jugador.
    kind:
        "normal" -> auto-dirigida al boss
        "spread" -> usa un ángulo fijo
        "wave"   -> sube y se mueve en onda senoidal
    """

    def __init__(self, x, y, target_boss, speed, kind="normal", angle=None):
        super().__init__()
        self.image = pygame.Surface((12, 12), pygame.SRCALPHA)
        self._draw_bullet_sprite(kind)
        self.rect = self.image.get_rect(center=(x, y))

        self.speed = speed
        self.kind = kind

        if kind == "wave":
            # se mueve recto hacia arriba pero oscila en X
            self.vx = 0
            self.vy = -self.speed
            self.base_x = x
            self.wave_t = 0.0
        elif kind == "spread":
            if angle is None:
                if target_boss is not None:
                    tx, ty = target_boss.rect.center
                    angle = math.atan2(ty - y, tx - x)
                else:
                    angle = -math.pi / 2
            self.vx = math.cos(angle) * self.speed
            self.vy = math.sin(angle) * self.speed
        else:  # normal auto-aim
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
                self.vx = 0
                self.vy = -self.speed

    def _draw_bullet_sprite(self, kind):
        surf = self.image
        surf.fill((0, 0, 0, 0))

        if kind == "wave":
            color_outer = (150, 240, 255, 200)
        elif kind == "spread":
            color_outer = (255, 210, 120, 200)
        else:
            color_outer = (250, 230, 120, 160)

        pygame.draw.circle(surf, color_outer, (6, 6), 6)
        pygame.draw.circle(surf, (255, 255, 255, 220), (6, 6), 3)

    def update(self):
        if self.kind == "wave":
            self.rect.y += self.vy
            self.wave_t += 0.18
            self.rect.x = self.base_x + math.sin(self.wave_t * 4) * 18
        else:
            self.rect.x += self.vx
            self.rect.y += self.vy

        if (
            self.rect.bottom < 0
            or self.rect.top > HEIGHT
            or self.rect.right < 0
            or self.rect.left > WIDTH
        ):
            self.kill()


# ============================================================
# BALAS DEL BOSS
# ============================================================
class EnemyBullet(pygame.sprite.Sprite):
    """Bala del boss."""

    def __init__(self, x, y, vx, vy, kind="normal"):
        super().__init__()
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        self._draw_enemy_bullet_sprite(kind)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = vx
        self.vy = vy
        self.kind = kind
        self.t = 0.0

    def _draw_enemy_bullet_sprite(self, kind):
        surf = self.image
        surf.fill((0, 0, 0, 0))

        if kind == "slow_orb":
            base = (200, 160, 255, 230)
        elif kind == "wave":
            base = (255, 100, 160, 230)
        else:
            base = (255, 140, 60, 220)

        pygame.draw.circle(surf, base, (5, 5), 5)
        pygame.draw.circle(surf, (255, 255, 255, 230), (5, 4), 2)

    def update(self):
        if self.kind == "wave":
            # balas que bajan haciendo onda
            self.rect.y += self.vy
            self.t += 0.15
            self.rect.x += math.sin(self.t * 4) * 2.5
        else:
            self.rect.x += self.vx
            self.rect.y += self.vy

        if (
            self.rect.bottom < 0
            or self.rect.top > HEIGHT
            or self.rect.right < 0
            or self.rect.left > WIDTH
        ):
            self.kill()


# ============================================================
# ATAQUE ESPECIAL DEL JUGADOR
# ============================================================
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
        pygame.draw.rect(surf, (130, 0, 200, 140), (10, 0, 40, HEIGHT))
        pygame.draw.rect(surf, (255, 255, 255, 220), (26, 0, 8, HEIGHT))

    def update(self):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()


# ============================================================
# ENEMIGOS PEQUEÑOS (MINIONS)
# ============================================================
class Minion(pygame.sprite.Sprite):
    """Enemigo pequeño con poca vida, baja desde el boss."""

    def __init__(self, x, y, level):
        super().__init__()
        self.image = pygame.Surface((26, 26), pygame.SRCALPHA)
        self._draw_minion_sprite()
        self.rect = self.image.get_rect(center=(x, y))

        self.max_hp = 20 + level * 5
        self.hp = self.max_hp
        self.speed_y = 2.0 + level * 0.2
        self.phase = random.uniform(0, math.pi * 2)

    def _draw_minion_sprite(self):
        surf = self.image
        surf.fill((0, 0, 0, 0))
        pygame.draw.rect(surf, (10, 10, 40), (0, 0, 26, 26), border_radius=6)
        pygame.draw.rect(surf, (80, 80, 220), (3, 5, 20, 16), border_radius=4)
        pygame.draw.rect(surf, (255, 255, 255), (6, 8, 4, 4), border_radius=2)
        pygame.draw.rect(surf, (255, 255, 255), (16, 8, 4, 4), border_radius=2)

    def update(self):
        self.rect.y += self.speed_y
        self.phase += 0.06
        self.rect.x += math.sin(self.phase * 2) * 1.8

        if self.rect.top > HEIGHT + 40:
            self.kill()


# ============================================================
# BOSS PRINCIPAL
# ============================================================
class Boss(pygame.sprite.Sprite):
    def __init__(self, level):
        super().__init__()
        self.image = pygame.Surface((160, 90), pygame.SRCALPHA)
        self.level = level
        self._draw_boss_sprite()
        self.rect = self.image.get_rect(center=(WIDTH // 2, 100))

        self.max_hp = 120 + level * 50
        self.hp = self.max_hp
        self.speed_x = 2 + level
        self.shoot_timer = 0
        self.shoot_interval = max(25 - level * 2, 8)

        self.pattern_time = 0
        self.pattern_duration = FPS * 3
        self.current_pattern = 0  # 0,1,2,3
        self.enraged = False
        self.spin_angle = 0.0  # para patrón radial

    def _draw_boss_sprite(self):
        surf = self.image
        surf.fill((0, 0, 0, 0))

        # glow
        glow = pygame.Surface((160, 90), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (255, 80, 80, 90), (-20, 0, 200, 90))
        surf.blit(glow, (0, 0))

        # cuerpo
        pygame.draw.rect(surf, (40, 0, 0), (0, 10, 160, 70), border_radius=18)
        pygame.draw.rect(surf, (130, 0, 0), (6, 16, 148, 58), border_radius=16)

        # cascos laterales
        pygame.draw.rect(surf, (90, 0, 0), (0, 26, 12, 40), border_radius=6)
        pygame.draw.rect(surf, (90, 0, 0), (148, 26, 12, 40), border_radius=6)

        # ojos
        pygame.draw.rect(surf, (250, 250, 250), (40, 32, 22, 14), border_radius=4)
        pygame.draw.rect(surf, (250, 250, 250), (98, 32, 22, 14), border_radius=4)
        pygame.draw.rect(surf, (255, 60, 60), (44, 36, 14, 6), border_radius=3)
        pygame.draw.rect(surf, (255, 60, 60), (102, 36, 14, 6), border_radius=3)

        # boca
        pygame.draw.rect(surf, (30, 0, 0), (50, 54, 60, 10), border_radius=3)
        for i in range(6):
            pygame.draw.rect(surf, (220, 220, 220), (52 + i * 9, 56, 5, 6), border_radius=2)

    def _draw_enraged_sprite(self):
        surf = self.image
        surf.fill((0, 0, 0, 0))
        pygame.draw.rect(surf, (80, 0, 0), (0, 10, 160, 70), border_radius=18)
        pygame.draw.rect(surf, (220, 20, 20), (6, 16, 148, 58), border_radius=16)
        pygame.draw.rect(surf, (120, 0, 0), (0, 26, 12, 40), border_radius=6)
        pygame.draw.rect(surf, (120, 0, 0), (148, 26, 12, 40), border_radius=6)
        pygame.draw.rect(surf, (255, 255, 255), (38, 28, 26, 16), border_radius=4)
        pygame.draw.rect(surf, (255, 255, 255), (96, 28, 26, 16), border_radius=4)
        pygame.draw.rect(surf, (255, 0, 0), (42, 32, 18, 6), border_radius=3)
        pygame.draw.rect(surf, (255, 0, 0), (100, 32, 18, 6), border_radius=3)
        pygame.draw.rect(surf, (40, 0, 0), (50, 54, 60, 10), border_radius=3)
        for i in range(6):
            pygame.draw.rect(surf, (255, 230, 230), (52 + i * 9, 56, 5, 6), border_radius=2)

    def update(self):
        # movimiento horizontal
        self.rect.x += self.speed_x
        if self.rect.left <= 0 or self.rect.right >= WIDTH:
            self.speed_x *= -1

        # flotando un poquito
        self.rect.y = 100 + int(10 * math.sin(pygame.time.get_ticks() * 0.002))

        # enrage: segunda fase cuando baja al 50%
        if not self.enraged and self.hp <= self.max_hp * 0.5:
            self.enraged = True
            self.speed_x *= 1.5
            self.shoot_interval = max(int(self.shoot_interval * 0.6), 5)
            self.pattern_duration = int(self.pattern_duration * 0.7)
            self._draw_enraged_sprite()

        self.pattern_time += 1
        if self.pattern_time >= self.pattern_duration:
            self.pattern_time = 0
            patterns = [0, 1, 2, 3]
            patterns.remove(self.current_pattern)
            self.current_pattern = random.choice(patterns)

        if self.shoot_timer > 0:
            self.shoot_timer -= 1

    def maybe_shoot(self, player, enemy_bullets_group, minions_group):
        """Dispara según el patrón actual o invoca minions."""
        if self.shoot_timer > 0:
            return

        self.shoot_timer = self.shoot_interval

        # Patrón 0: ráfaga dirigida (triple shot)
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
                bullet = EnemyBullet(sx, sy, vx, vy, kind="normal")
                enemy_bullets_group.add(bullet)

        # Patrón 1: pared de orbes lentos que bajan recto
        elif self.current_pattern == 1:
            num = 9
            margin = 80
            span = WIDTH - margin * 2
            for i in range(num):
                x = margin + int(span * (i / (num - 1)))
                y = self.rect.bottom
                bullet = EnemyBullet(x, y, 0, 3.0, kind="slow_orb")
                enemy_bullets_group.add(bullet)

        # Patrón 2: círculo radial giratorio
        elif self.current_pattern == 2:
            num_bullets = 14
            speed = 4.0
            self.spin_angle += 0.3  # gira un poco cada ráfaga
            for i in range(num_bullets):
                angle = self.spin_angle + (2 * math.pi / num_bullets) * i
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                bullet = EnemyBullet(self.rect.centerx, self.rect.centery, vx, vy, kind="wave")
                enemy_bullets_group.add(bullet)

        # Patrón 3: invoca minions pequeños
        elif self.current_pattern == 3:
            offsets = [-80, 0, 80]
            for off in offsets:
                mx = self.rect.centerx + off
                my = self.rect.bottom + 10
                if 20 < mx < WIDTH - 20:
                    minion = Minion(mx, my, self.level)
                    minions_group.add(minion)
