import random


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
