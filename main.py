import math
import numpy
import pymunk
import pyglet
from pymunk import pyglet_util
from pymunk.vec2d import Vec2d
from attack import *

import consts

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "Starting Template"

# brawlhalla notes
# 2560x1440p
# sprites are 176px image
# hitbox is a capsule. dimensions are  144 width, 160 px height. 145px diameter
# hitbox above ~8-10px above sprite's feet

INPUT_MOVE_LEFT = 0
INPUT_MOVE_RIGHT = 1
INPUT_MOVE_DOWN = 2
INPUT_JUMP = 3
INPUT_DODGE = 4
INPUT_HEAVY_HIT = 5
INPUT_LIGHT_HIT = 6
INPUT_THROW = 7

TOTAL_MIDAIR_JUMPS_ALLOWED = 2

JUMP_HEIGHT = 15

#not sure how im going to do this one yet.
PIXELS_PER_WORLD_UNITS = 10

#world units
HURTBOX_WIDTH = 14.4
#world units
HURTBOX_HEIGHT = 16

FIGHTER_COLLIDER_WIDTH = 8
FIGHTER_COLLIDER_HEIGHT = 15

HURTBOX_COLOR = (171, 174, 105, 128)

FRAMES_PER_SECOND = 60
TIMESTEP = 1/FRAMES_PER_SECOND

HURTBOX_COLLISION_TYPE = 1
HITBOX_COLLISION_TYPE = 2
WALL_COLLISION_TYPE = 3
FIGHTER_WALL_COLLIDER_COLLISION_TYPE = 4

FALL_VELOCITY = 80.0

DEVICE_CONTROLLED_FIGHTER_INDEX = 0


wall_collision_filter = pymunk.ShapeFilter( \
	categories=0b1 << (WALL_COLLISION_TYPE-1), \
	mask=0b1 << (FIGHTER_WALL_COLLIDER_COLLISION_TYPE-1))

def create_pymunk_box(body: pymunk.Body, min: tuple[float,float], max: tuple[float,float], radus: float = 0):
	return pymunk.Poly(body, [min, (max[0], min[1]), max, (min[0], max[1])], radius=0)


def add_capsule_shape(body: pymunk.Body, offset: tuple[float,float], width: float, height: float) -> list[pymunk.Shape] :
	if width == height:
		return [pymunk.Circle(body, 0.5*width, offset)]
	if width > height:
		stretch_length = width - height
		c1 = pymunk.Circle(body, height*0.5, offset=(offset[0] - stretch_length*0.5, offset[1]))
		c2 = pymunk.Circle(body, height*0.5, offset=(offset[0] + stretch_length*0.5, offset[1]))
		box = create_pymunk_box(body, 
			(offset[0] - stretch_length*0.5, offset[1] - height*0.5), 
			(offset[0] + stretch_length*0.5, offset[1] + height*0.5))
		return [c1,c2,box]
	else:
		stretch_length = height - width
		c1 = pymunk.Circle(body, width*0.5, offset=(offset[0], offset[1] - stretch_length*0.5))
		c2 = pymunk.Circle(body, width*0.5, offset=(offset[0], offset[1] + stretch_length*0.5))
		box = create_pymunk_box(body, 
			(offset[0] - width*0.5, offset[1] - stretch_length*0.5), 
			(offset[0] + width*0.5, offset[1] + stretch_length*0.5))
		return [c1, c2, box]

class Fighter():
	def __init__(self, space: pymunk.Space, center: tuple[float, float], side_facing = consts.FIGHTER_SIDE_FACING_LEFT):
		#hurtbox body is supposed to be the shape of a capsule: 2 circles and 1 rectangle
		self.side_facing = side_facing
		self.input = numpy.zeros(8)
		self.prev_input = numpy.zeros(8)
		self.body = pymunk.Body(mass=5, moment=float("inf"))
		self.body._set_position(center)
		space.add(self.body)
		self.attacks: list[Attack] = []
		self.last_cast_id_hit: int = None
		self.dmg_points = 0

		hurtbox_filter = pymunk.ShapeFilter(
			categories=0b1 << (HURTBOX_COLLISION_TYPE-1),
			mask=0b1 << (HITBOX_COLLISION_TYPE-1))

		wall_collider_filter = pymunk.ShapeFilter(
			categories=0b1 << (FIGHTER_WALL_COLLIDER_COLLISION_TYPE-1),
			mask=0b1 << (WALL_COLLISION_TYPE-1))

		hitbox_filter = pymunk.ShapeFilter(
			categories=0b1 << (HITBOX_COLLISION_TYPE-1), 
			mask=0b1 << (HURTBOX_COLLISION_TYPE-1))

		hurtbox_shapes = add_capsule_shape(self.body, (0,0), HURTBOX_WIDTH, HURTBOX_HEIGHT)
		for shape in hurtbox_shapes:
			shape.collision_type = HURTBOX_COLLISION_TYPE 
			shape.filter = hurtbox_filter
			shape.sensor = True
			shape.fighter = self
			space.add(shape)

		self.wall_collider = create_pymunk_box(self.body,
			(-FIGHTER_COLLIDER_WIDTH*0.5, -FIGHTER_COLLIDER_HEIGHT*0.5-1), 
			(FIGHTER_COLLIDER_WIDTH*0.5, FIGHTER_COLLIDER_HEIGHT*0.5-1)
		)
		self.wall_collider.collision_type = FIGHTER_WALL_COLLIDER_COLLISION_TYPE
		self.wall_collider.filter = wall_collider_filter
		self.wall_collider.friction = 1
		self.wall_collider.color = (255, 233, 28, 100)

		space.add(self.wall_collider)

		left_side_light_hitbox_shapes = add_capsule_shape(self.body, (-0.5*HURTBOX_WIDTH,-1),HURTBOX_WIDTH,5)
		right_side_light_hitbox_shapes = add_capsule_shape(self.body, (0.5*HURTBOX_WIDTH,-1),HURTBOX_WIDTH,5)

		left_neutral_light_hitbox_shapes_1 = add_capsule_shape(self.body, (-6, 0), 10, 5)
		right_neutral_light_hitbox_shapes_1 = add_capsule_shape(self.body, (6, 0), 10, 5)

		left_neutral_light_hitbox_shapes_2 = add_capsule_shape(self.body, (-4, 0), 4, 4) + add_capsule_shape(self.body, (-6, 4), 8, 6)
		right_neutral_light_hitbox_shapes_2 = add_capsule_shape(self.body, (4, 0), 4, 4) + add_capsule_shape(self.body, (6, 4), 8, 6)

		left_neutral_light_hitbox_shapes_3 = add_capsule_shape(self.body, (-4, 0), 5, 10)
		right_neutral_light_hitbox_shapes_3 = add_capsule_shape(self.body, (4, 0), 5, 10)

		left_neutral_light_hitbox_shapes_4 = add_capsule_shape(self.body, (-6, 0), 10, 5)
		right_neutral_light_hitbox_shapes_4 = add_capsule_shape(self.body, (6, 0), 10, 5)

		left_down_light_hitbox_shapes = add_capsule_shape(self.body, (-8, -4), 10, 5)
		right_down_light_hitbox_shapes = add_capsule_shape(self.body, (8, -4), 10, 5)
		
		left_aerial_neutral_light_hitbox_shapes_1 = add_capsule_shape(self.body, (-7, 1), 5, 10)
		right_aerial_neutral_light_hitbox_shapes_1 = add_capsule_shape(self.body, (7, 1), 5, 10)

		left_aerial_neutral_light_hitbox_shapes_2 = add_capsule_shape(self.body, (-7, -1), 4, 3) + add_capsule_shape(self.body, (-9, 2), 8, 4)
		right_aerial_neutral_light_hitbox_shapes_2 = add_capsule_shape(self.body, (7, -1), 4, 3) + add_capsule_shape(self.body, (9, 2), 8, 4)

		left_aerial_neutral_light_hitbox_shapes_3 = add_capsule_shape(self.body, (-4, 0), 10, 5)
		right_aerial_neutral_light_hitbox_shapes_3 = add_capsule_shape(self.body, (4, 0), 10, 5)

		left_aerial_side_light_hitbox_shapes_1 = add_capsule_shape(self.body, (-8, -2), 6, 3) + add_capsule_shape(self.body, (-10, -4), 4, 3)
		right_aerial_side_light_hitbox_shapes_1 = add_capsule_shape(self.body, (8, -2), 6, 3) + add_capsule_shape(self.body, (10, -4), 4, 3)

		left_aerial_side_light_hitbox_shapes_2 = add_capsule_shape(self.body, (-9, -2), 4, 3) + add_capsule_shape(self.body, (-10, -4), 4, 3)
		right_aerial_side_light_hitbox_shapes_2 = add_capsule_shape(self.body, (9, -2), 4, 3) + add_capsule_shape(self.body, (10, -4), 4, 3)

		left_aerial_side_light_hitbox_shapes_3 = add_capsule_shape(self.body, (-12, -5), 2, 2)
		right_aerial_side_light_hitbox_shapes_3 = add_capsule_shape(self.body, (12, -5), 2, 2)

		left_aerial_down_light_hitbox_shapes = add_capsule_shape(self.body, (-5, -4), 2, 3) + add_capsule_shape(self.body, (-6, -6), 3, 4)
		right_aerial_down_light_hitbox_shapes = add_capsule_shape(self.body, (5, -4), 2, 3) + add_capsule_shape(self.body, (6, -6), 3, 4)

		#NOTE: add all hitboxes into this loop
		for shape in (left_side_light_hitbox_shapes + right_side_light_hitbox_shapes 
			+ left_neutral_light_hitbox_shapes_1 + right_neutral_light_hitbox_shapes_1 
			+ left_neutral_light_hitbox_shapes_2 + right_neutral_light_hitbox_shapes_2
			+ left_neutral_light_hitbox_shapes_3 + right_neutral_light_hitbox_shapes_3 
			+ left_neutral_light_hitbox_shapes_4 + right_neutral_light_hitbox_shapes_4 
			+ left_down_light_hitbox_shapes + right_down_light_hitbox_shapes
			+ left_aerial_neutral_light_hitbox_shapes_1 + right_aerial_neutral_light_hitbox_shapes_1
			+ left_aerial_neutral_light_hitbox_shapes_2 + right_aerial_neutral_light_hitbox_shapes_2
			+ left_aerial_neutral_light_hitbox_shapes_3 + right_aerial_neutral_light_hitbox_shapes_3
			+ left_aerial_side_light_hitbox_shapes_1 + right_aerial_side_light_hitbox_shapes_1
			+ left_aerial_side_light_hitbox_shapes_2 + right_aerial_side_light_hitbox_shapes_2
			+ left_aerial_side_light_hitbox_shapes_3 + right_aerial_side_light_hitbox_shapes_3
			+ left_aerial_down_light_hitbox_shapes + right_aerial_down_light_hitbox_shapes
			):
			shape.collision_type = HITBOX_COLLISION_TYPE	
			shape.filter = hitbox_filter
			shape.sensor = True
			shape.color = (128, 0, 0, 255)

		self.side_light_attack = Attack([
			Power(
				casts = [
					Cast(startup_frames=2, active_frames=2, active_velocity=(50,0)), 
					Cast(startup_frames=3, active_frames=2, active_velocity=(100,10)),
					Cast(
						startup_frames=1, active_frames=4, active_velocity=(100,0), is_active_velocity_all_frames=True, base_dmg = 13, var_force=20, fixed_force=80,
						hitbox=Hitbox( left_side_light_hitbox_shapes, right_side_light_hitbox_shapes, ),
					)
				],
				cooldown_frames = 10, stun_frames = 18
			), 
			Power([Cast(startup_frames=0, active_frames=1, active_velocity=(100,0))], fixed_recovery_frames = 2, recovery_frames = 18) 
		], name="unarmed_side_light")

		self.neutral_light_attack = Attack([
			Power(
				casts = [
					Cast(
						startup_frames = 5,	active_frames = 3, base_dmg=3, fixed_force=25,
						hitbox=Hitbox(left_neutral_light_hitbox_shapes_1, right_neutral_light_hitbox_shapes_1),
					),
				],
				recovery_frames = 3, cooldown_frames = 16, stun_frames = 17
			),
			Power(
				casts = [
					Cast(
						startup_frames = 6, active_frames = 6, base_dmg=3, fixed_force=20,
						hitbox=Hitbox(left_neutral_light_hitbox_shapes_2, right_neutral_light_hitbox_shapes_2),
					),
				],
				recovery_frames = 0, cooldown_frames = 0, stun_frames = 17
			),
			Power(
				casts = [
					Cast(
						startup_frames = 6, active_frames = 3, base_dmg = 3, fixed_force = 25,
						hitbox=Hitbox(left_neutral_light_hitbox_shapes_3, right_neutral_light_hitbox_shapes_3),
					),
				],
				recovery_frames = 3, stun_frames = 20, requires_hit = True
			),
			Power(
				casts = [
					Cast(startup_frames=3, active_frames = 1, active_velocity=(1,0)),
					Cast(startup_frames=3, active_frames = 1, active_velocity=(1,0), is_active_velocity_all_frames=True),
					Cast(startup_frames=3, active_frames = 1, active_velocity=(1,0), is_active_velocity_all_frames=True),
					Cast(
						startup_frames = 2, active_frames = 5, base_dmg=5, var_force=31, fixed_force=52,
						hitbox=Hitbox(left_neutral_light_hitbox_shapes_4, right_neutral_light_hitbox_shapes_4)
					),
				],
				recovery_frames = 22, stun_frames = 23, requires_hit = True
			),
			Power([Cast(startup_frames = 0, active_frames=1)], fixed_recovery_frames=2, recovery_frames=9),
		], name="unarmed_neutral_light")

		self.down_light_attack = Attack([
			Power(
				casts = [
					Cast(
						startup_frames=5, active_frames=3, active_velocity=(50,0)
					),
					Cast(
						startup_frames=0, active_frames=9, base_dmg=8, var_force=5, fixed_force=45, active_velocity=(100,0),
						hitbox=Hitbox(left_down_light_hitbox_shapes, right_down_light_hitbox_shapes)
					),
					Cast(
						startup_frames=0,active_frames=3,active_velocity=(50,0)
					),
				],
				cooldown_frames = 0, stun_frames = 31
			),
			Power(
				casts = [
					Cast(
						startup_frames=0, active_frames=4
					),
				],
				fixed_recovery_frames=1, recovery_frames=13
			)
		], name="unarmed_down_light")

		self.aerial_neutral_light_attack = Attack([
			Power(
				casts = [
					Cast(
						startup_frames=7, active_frames=5, base_dmg=3, fixed_force=40,
						hitbox=Hitbox(left_aerial_neutral_light_hitbox_shapes_1, right_aerial_neutral_light_hitbox_shapes_1),
					),
				],
				cooldown_frames=7, stun_frames=17
			),
			Power(
				casts = [
					Cast(
						startup_frames=8, active_frames=5, base_dmg=3, fixed_force=40,
						hitbox=Hitbox(left_aerial_neutral_light_hitbox_shapes_2, right_aerial_neutral_light_hitbox_shapes_2),
					),
				],
				recovery_frames=4, stun_frames=21
			),
			Power(
				casts = [
					Cast(
						startup_frames=8, active_frames=5, base_dmg=5, var_force=37, fixed_force=71,
						hitbox=Hitbox(left_aerial_neutral_light_hitbox_shapes_3, right_aerial_neutral_light_hitbox_shapes_3)
					),
				],
				recovery_frames=22, stun_frames=19, requires_hit=True,
			),
			Power(
				casts = [ Cast( startup_frames=0, active_frames=1) ],
				fixed_recovery_frames=1, recovery_frames=15, cooldown_frames=0,
			),
		], name="unarmed_aerial_neutral_light")

		self.aerial_side_light_attack = Attack([
			Power(
				casts = [
					Cast(
						startup_frames=13, active_frames=3, base_dmg=13, var_force=40, fixed_force=45, active_velocity=(50, 0),
						hitbox=Hitbox(left_aerial_side_light_hitbox_shapes_1, right_aerial_side_light_hitbox_shapes_1),
					),
					Cast(
						startup_frames=0, active_frames=2, base_dmg=13, var_force=37, fixed_force=45, active_velocity=(50, 0),
						hitbox=Hitbox(left_aerial_side_light_hitbox_shapes_2, right_aerial_side_light_hitbox_shapes_2),
					),
					Cast(
						startup_frames=0, active_frames=2, base_dmg=13, var_force=36, fixed_force=45, active_velocity=(50, 0),
						hitbox=Hitbox(left_aerial_side_light_hitbox_shapes_3, right_aerial_side_light_hitbox_shapes_3),
					)
				],
				cooldown_frames=14, stun_frames=17,
			),
			Power(
				casts = [ Cast(startup_frames=0, active_frames=1) ],
				fixed_recovery_frames=5, recovery_frames=17
			),
		], name="unarmed_aerial_side_light")

		self.aerial_down_light_attack = Attack([
			Power(
				casts = [
					Cast(startup_frames=4, active_frames=1),
					Cast(
						startup_frames=4, active_frames=16, base_dmg=16, var_force=5, fixed_force=65, active_velocity=(50,-10),
						hitbox=Hitbox(left_aerial_down_light_hitbox_shapes, right_aerial_down_light_hitbox_shapes),
					)
				],
				cooldown_frames=9, stun_frames=19
			),
			Power(
				casts = [
					Cast(startup_frames=4, active_frames=1),
				],
			),
		], name="unarmed_aerial_down_light")

		#NOTE: add all attacks in here
		self.attacks.append(self.side_light_attack)
		self.attacks.append(self.neutral_light_attack)
		self.attacks.append(self.down_light_attack)
		self.attacks.append(self.aerial_neutral_light_attack)
		self.attacks.append(self.aerial_side_light_attack)
		self.attacks.append(self.aerial_down_light_attack)

		self.midair_jumps_left = 0
		self.is_grounded = False

		#number of frames fighter must wait before attempting a new action (dodge, move, hit).
		self.recover_timer = 0
		#whether the player is currently getting hit by an action
		self.is_hit = False

	def compute_grounding(self):
		grounding = {
			"normal": Vec2d.zero(),
			"penetration": Vec2d.zero(),
			"impulse": Vec2d.zero(),
			"position": Vec2d.zero(),
			"body": None,
		}
		# find out if player is standing on ground

		def f(arbiter: pymunk.Arbiter):
			n = -arbiter.contact_point_set.normal
			if n.y > grounding["normal"].y:
				grounding["normal"] = n
				grounding["penetration"] = -arbiter.contact_point_set.points[0].distance
				grounding["body"] = arbiter.shapes[1].body
				grounding["impulse"] = arbiter.total_impulse
				grounding["position"] = arbiter.contact_point_set.points[0].point_b

		self.body.each_arbiter(f)
		self.is_grounded = False
		if grounding["body"] != None:# and abs(grounding["normal"].x / grounding["normal"].y) < feet.friction:
			self.is_grounded = True
			self.midair_jumps_left = TOTAL_MIDAIR_JUMPS_ALLOWED

	def is_input_tapped(self, input_index: int) -> bool:
		return self.input[input_index] and self.prev_input[input_index] == False

# function callback to used when a fighter hurtbox overlaps with hitbox. do stuff like knocking back fighter and applying damage points
def pre_solve_hurtbox_hitbox(arbiter: pymunk.Arbiter, space: pymunk.Space, data) -> bool:
	victim: Fighter = arbiter.shapes[0].fighter
	if victim.is_hit == False:
		victim.is_hit = True
		cast: Cast = arbiter.shapes[1].cast
		power: Power = arbiter.shapes[1].power
		attack: Attack = arbiter.shapes[1].attack
		attack.has_hit = True
		if not cast.has_hit:
			cast.has_hit = True
			victim.dmg_points += cast.base_dmg
			print("victim has {} damage points".format(victim.dmg_points))
		dir = 1
		if arbiter.shapes[1].side_facing == consts.FIGHTER_SIDE_FACING_LEFT:
			dir = -1
		impulse_scale = 1
		impulse = (cast.fixed_force + victim.dmg_points * cast.var_force * 0.01)*dir*impulse_scale, impulse_scale
		victim.body.apply_impulse_at_local_point(impulse)
		victim.recover_timer = power.stun_frames
	
	return True

class GameState():
	def __init__(self):
		self.physics_sim = pymunk.Space()
		self.physics_sim._set_gravity((0,-300))
		self.fighters = [Fighter(self.physics_sim, (30,100)), Fighter(self.physics_sim, (70, 100))]

		wall_body = pymunk.Body(body_type=pymunk.Body.STATIC)
		p1 = create_pymunk_box(wall_body, (10, 10), (120,30))
		p1.collision_type = WALL_COLLISION_TYPE
		p1.filter = wall_collision_filter
		p1.friction = 1
		p2 = create_pymunk_box(wall_body, (10, 10), (20,100))
		p2.collision_type = WALL_COLLISION_TYPE
		p2.filter = wall_collision_filter
		#p2.friction = 1
		p3 = create_pymunk_box(wall_body, (110, 30), (120,100))
		p3.collision_type = WALL_COLLISION_TYPE
		p3.filter = wall_collision_filter
		#p3.friction = 1
		self.physics_sim.add(wall_body, p1, p2, p3)

		hurtbox_hitbox_handler = self.physics_sim.add_collision_handler(HURTBOX_COLLISION_TYPE, HITBOX_COLLISION_TYPE)
		hurtbox_hitbox_handler.pre_solve = pre_solve_hurtbox_hitbox

		self.gravity_enabled = True

game_state = GameState()

def step_game(_):
	for fighter in game_state.fighters:
		dx = 0

		attack_results: StepAttackResults
		is_doing_action = False
		if fighter.recover_timer == 0:
			for attack in fighter.attacks:
				attack_results = step_attack(attack, game_state.physics_sim)
				if attack_results.is_active and not is_doing_action:
					print("attack {} is active".format(attack.name))
					is_doing_action = True
					break

		# on input, move fighter to right
		if is_doing_action == False and fighter.recover_timer == 0 and (fighter.side_facing != consts.FIGHTER_SIDE_FACING_LEFT or fighter.input[INPUT_MOVE_LEFT] == False) and fighter.input[INPUT_MOVE_RIGHT]:
			fighter.side_facing = consts.FIGHTER_SIDE_FACING_RIGHT
			dx = 50
		
		#on input, move fighter to the left
		if is_doing_action == False and fighter.recover_timer == 0 and (fighter.side_facing != consts.FIGHTER_SIDE_FACING_RIGHT or fighter.input[INPUT_MOVE_RIGHT] == False) and fighter.input[INPUT_MOVE_LEFT]:
			fighter.side_facing = consts.FIGHTER_SIDE_FACING_LEFT
			dx = -50

		fighter.compute_grounding()
		if (fighter.prev_input[INPUT_JUMP] == False and fighter.input[INPUT_JUMP] and
			(fighter.is_grounded or fighter.midair_jumps_left > 0)
			):
			print("JUMPING")
			#only subtract midair jumps if fighter is not grounded
			fighter.midair_jumps_left -= int(not fighter.is_grounded)
			vel = fighter.body.velocity
			fighter.body.velocity = (vel.x, 0)
			jump_v = math.sqrt(2.0 * JUMP_HEIGHT * abs(game_state.physics_sim.gravity.y))
			y_force = fighter.body.mass * jump_v
			fighter.body.apply_impulse_at_local_point((0, y_force))

		if fighter.recover_timer == 0 and is_doing_action == False:
			if fighter.is_grounded:
				if fighter.input[INPUT_MOVE_DOWN] and fighter.is_input_tapped(INPUT_LIGHT_HIT) and fighter.down_light_attack.cooldown_timer == 0:
					fighter.down_light_attack.activate(fighter.side_facing)
				elif dx != 0 and fighter.is_input_tapped(INPUT_LIGHT_HIT)  and fighter.side_light_attack.cooldown_timer == 0:
					fighter.side_light_attack.activate(fighter.side_facing)
				elif dx == 0 and fighter.is_input_tapped(INPUT_LIGHT_HIT) and fighter.neutral_light_attack.cooldown_timer == 0:
					fighter.neutral_light_attack.activate(fighter.side_facing)
			else:
				if fighter.input[INPUT_MOVE_DOWN] and fighter.is_input_tapped(INPUT_LIGHT_HIT) and fighter.aerial_down_light_attack.cooldown_timer == 0:
					fighter.aerial_down_light_attack.activate(fighter.side_facing)
				elif dx != 0 and fighter.is_input_tapped(INPUT_LIGHT_HIT)  and fighter.aerial_side_light_attack.cooldown_timer == 0:
					fighter.aerial_side_light_attack.activate(fighter.side_facing)
				elif dx == 0 and fighter.is_input_tapped(INPUT_LIGHT_HIT) and fighter.aerial_neutral_light_attack.cooldown_timer == 0:
					fighter.aerial_neutral_light_attack.activate(fighter.side_facing)

		attack_velocity = (0,0)
		if is_doing_action and attack_results.is_active and attack_results.velocity != None:
			print("attack velocity being applied")
			attack_velocity = attack_results.velocity
			if fighter.side_facing == consts.FIGHTER_SIDE_FACING_LEFT:
				attack_velocity = -attack_velocity[0], attack_velocity[1]
		
		if is_doing_action or fighter.recover_timer == 0:
			fighter.body.velocity = dx + attack_velocity[0], fighter.body._get_velocity().y

		fighter.body.velocity = fighter.body._get_velocity().x, max(fighter.body._get_velocity().y, -FALL_VELOCITY) + attack_velocity[1]

		if fighter.is_hit == False:
			fighter.recover_timer = max(fighter.recover_timer-1, 0)
		fighter.is_hit = False
		#input should be copied into previous input AFTER all logic needing input has been processed
		fighter.prev_input = fighter.input.copy()

	game_state.physics_sim.step(TIMESTEP)


game_window = pyglet.window.Window(fullscreen=True, style=pyglet.window.Window.WINDOW_STYLE_BORDERLESS)
physics_batch = pyglet.graphics.Batch()
@game_window.event
def on_draw():
	# draw things here
	game_window.clear()

	physics_draw_options = pyglet_util.DrawOptions(batch=physics_batch)
	physics_draw_options.transform = pymunk.Transform.scaling(PIXELS_PER_WORLD_UNITS)
	game_state.physics_sim.debug_draw(physics_draw_options)
	physics_batch.draw()
	for fighter in game_state.fighters:
		body = fighter.body
		label = pyglet.text.Label('DP: {}'.format(fighter.dmg_points),
                          font_name='Times New Roman',
                          font_size=24,
                          x=body.position.x * PIXELS_PER_WORLD_UNITS, y=(body.position.y + 10) * PIXELS_PER_WORLD_UNITS,
                          anchor_x='center', anchor_y='center')
		label.draw()

@game_window.event
def on_key_press(key, modifiers):
	fighter: Fighter = game_state.fighters[DEVICE_CONTROLLED_FIGHTER_INDEX]
	if key == pyglet.window.key.LEFT:
		fighter.input[INPUT_MOVE_LEFT] = True
	if key == pyglet.window.key.RIGHT:
		fighter.input[INPUT_MOVE_RIGHT] = True
	if key == pyglet.window.key.DOWN:
		fighter.input[INPUT_MOVE_DOWN] = True
	if key == pyglet.window.key.UP:
		fighter.input[INPUT_JUMP] = True
	if key == pyglet.window.key.Z:
		fighter.input[INPUT_DODGE] = True
	if key == pyglet.window.key.X: 
		fighter.input[INPUT_HEAVY_HIT] = True
	if key == pyglet.window.key.C:
		fighter.input[INPUT_LIGHT_HIT] = True
	if key == pyglet.window.key.V:
		fighter.input[INPUT_THROW] = True
	if key == pyglet.window.key.O:
		game_state.gravity_enabled = not game_state.gravity_enabled
		if game_state.gravity_enabled:
			game_state.physics_sim._set_gravity((0,-100))
		else:
			game_state.physics_sim._set_gravity((0,0))
			fighter.body._set_velocity((0,0))

@game_window.event
def on_key_release(key, modifiers):
	fighter: Fighter = game_state.fighters[DEVICE_CONTROLLED_FIGHTER_INDEX]
	if key == pyglet.window.key.LEFT:
		fighter.input[INPUT_MOVE_LEFT] = False
	if key == pyglet.window.key.RIGHT:
		fighter.input[INPUT_MOVE_RIGHT] = False
	if key == pyglet.window.key.DOWN:
		fighter.input[INPUT_MOVE_DOWN] = False
	if key == pyglet.window.key.UP:
		fighter.input[INPUT_JUMP] = False
	if key == pyglet.window.key.Z:
		fighter.input[INPUT_DODGE] = False
	if key == pyglet.window.key.X: 
		fighter.input[INPUT_HEAVY_HIT] = False
	if key == pyglet.window.key.C:
		fighter.input[INPUT_LIGHT_HIT] = False
	if key == pyglet.window.key.V:
		fighter.input[INPUT_THROW] = False

if __name__ == "__main__":
	pyglet.clock.schedule_interval(step_game, TIMESTEP)
	pyglet.app.run()


