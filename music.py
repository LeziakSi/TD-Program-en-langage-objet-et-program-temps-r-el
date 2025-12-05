import os
import pygame
from config import BASE_DIR, MUSIC_VOLUME

music_muted = False
music_paused = False


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
