# neutral light hit actually has a series of active frames that are separated by some idle frames, but we'll worry about that later
# TODO: change back to 3
NEUTRAL_LIGHT_HIT_ACTIVE_FRAMES = 30

FIGHTER_SIDE_FACING_LEFT = 0
FIGHTER_SIDE_FACING_RIGHT = 1

HURTBOX_COLLISION_TYPE = 1
HITBOX_COLLISION_TYPE = 2
WALL_COLLISION_TYPE = 3
FIGHTER_WALL_COLLIDER_COLLISION_TYPE = 4

#world units
HURTBOX_WIDTH = 14.4
#world units
HURTBOX_HEIGHT = 16

# of frames a fighter is invulnerable after doing a neutral dodge
NEUTRAL_DODGE_INVULN_FRAMES = 16

# of frames a fighter is invulnerable after doing an air neutral dodge
AIR_NEUTRAL_DODGE_INVULN_FRAMES = 20

# of frames a fighter has after doing an air neutral dodge to initate a gravity cancel
GRAVITY_CANCEL_WINDOW_FRAMES = 16

# of frames a fighter is invulnerable after doing a move dodge. side, side air, down air, up air. no matter
MOVE_DODGE_INVULN_FRAMES = 12


