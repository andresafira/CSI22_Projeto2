WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
FULLSCREEN = True
WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT

ARENA_WIDTH = 2800
ARENA_HEIGHT = 2000
ARENA_SIZE = ARENA_WIDTH, ARENA_HEIGHT

FRAMERATE = 60

WALKING = 0
IDLE = 1
ROLLING = 2
TAKING_DAMAGE = 3

#BOSS MODES
BOSS_IDLE = 0
BOSS_FIRING_LASER = 1
BOSS_PREPARING_LASER = 2
BOSS_SWOOPING = 3
BOSS_SPAWNING = 4
BOSS_HAND_ATTACK = 5

RIGHT = 0
LEFT = 1

BREAD = 1
SHURIKEN = 3
GUN = 4
FIRE = 5
GATLING = 6
KNIFE = 2

COOLDOWNS = {BREAD: 1, GUN: 0.45, SHURIKEN: 0.9, FIRE: 5, GATLING: 0.1, KNIFE: 0.9}

VALID_MODES = (GUN,BREAD,SHURIKEN,FIRE,GATLING,KNIFE)

BACKGROUND = 0
FOREGROUND = 1