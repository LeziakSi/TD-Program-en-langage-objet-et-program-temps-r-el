import pygame
import os

# Mixer antes para evitar problemas de sonido
try:
    pygame.mixer.pre_init(44100, -16, 2, 512)
except Exception:
    pass

pygame.init()

# Tamaño ventana y FPS
WIDTH, HEIGHT = 800, 600
FPS = 60

# Fuente estilo gótica (si no está, cae a la de sistema)
GOTHIC_FONT_NAME = "Old English Text MT"
FONT = pygame.font.SysFont(GOTHIC_FONT_NAME, 24)
BIG_FONT = pygame.font.SysFont(GOTHIC_FONT_NAME, 48)

# Colores
BLACK  = (0, 0, 0)
WHITE  = (255, 255, 255)
RED    = (200, 60, 60)
GREEN  = (60, 200, 60)
BLUE   = (60, 60, 200)
YELLOW = (230, 230, 40)
GREY   = (40, 40, 40)
PURPLE = (160, 80, 200)
CYAN   = (80, 200, 200)
ORANGE = (255, 160, 60)

# Estados del juego
STATE_TITLE    = "TITLE"
STATE_PLAYING  = "PLAYING"
STATE_PAUSED   = "PAUSED"
STATE_GAME_OVER = "GAME_OVER"
STATE_UPGRADE  = "UPGRADE"

# Carpeta base (para música)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Música
MUSIC_VOLUME = 0.6
