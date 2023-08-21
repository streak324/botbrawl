import math
import numpy
import pymunk
import pyglet
import pymunk.pyglet_util
from pymunk.vec2d import Vec2d

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

class Hitbox():
	def __init__(self, left_shapes: list[pymunk.Shape], right_shapes: list[pymunk.Shape]):
		self.left_shapes = left_shapes
		self.right_shapes = right_shapes
		for shape in self.left_shapes:
			shape.side_facing = consts.FIGHTER_SIDE_FACING_LEFT
		for shape in self.right_shapes:
			shape.side_facing = consts.FIGHTER_SIDE_FACING_RIGHT

# to mimic brawlhalla, every attack move has a sequence of powers, and each power has a sequence of casts.
class Cast():
	#active_velocity is supposed to be used during active frames.
	def __init__(
			self, startup_frames: int, active_frames: int, base_dmg: int = 0, var_force: int = 0, fixed_force: int = 0, hitbox: Hitbox = None, 
	      	active_velocity: tuple[float, float] = None, is_active_velocity_all_frames: bool = False
		):
		self.startup_frames = startup_frames
		self.active_frames = active_frames
		self.base_dmg = base_dmg
		self.var_force = var_force
		self.fixed_force = fixed_force
		self.hitbox = hitbox
		if hitbox != None:
			for shape in hitbox.left_shapes + hitbox.right_shapes:
				shape.cast = self
		# start velocity should be negated when attack is facing left
		self.active_velocity = active_velocity
		self.is_active_velocity_all_frames = is_active_velocity_all_frames
		self.is_active = False

class Power():
	def __init__(self, casts: list[Cast], cooldown_frames: int = 0, fixed_recovery_frames: int = 0, recovery_frames: int = 0, min_charge_frames: int = 0, stun_frames = 0):
		self.casts = casts
		for cast in self.casts:
			if cast.hitbox != None:
				for shape in cast.hitbox.left_shapes + cast.hitbox.right_shapes:
					shape.power = self
		self.cooldown_frames = cooldown_frames
		self.fixed_recovery_frames = fixed_recovery_frames
		self.recovery_frames = recovery_frames
		self.min_charge_frames = min_charge_frames
		self.stun_frames = stun_frames
		self.is_active = False

class Attack():
	def __init__(self, powers: list[Power], name: str):
		self.powers = powers
		self.name = name 
		self.is_active = False
		self.cast_frame = 0
		self.power_idx = 0
		self.cast_idx = 0
		# cooldown timer should not start ticking down until all powers have been looped. an attack should not be activated while cooldown timer is greater than zero
		self.cooldown_timer = 0
		# recover timer should only be used between powers, where the previous power has recovery frames. if the last power has recovery frames, it should be applied to the fighter's recover timer
		self.recover_timer = 0
		self.side_facing = 0
		pass

def activate_attack(attack: Attack, side_facing: int) -> (float,float):
	print("activating attack {} facing {}".format(attack.name, side_facing))
	attack.is_active = True
	attack.cast_frame = 0
	attack.power_idx = 0
	attack.cast_idx = 0
	attack.side_facing = side_facing
	attack.cooldown_timer = 0
	attack.recover_timer = 0
	for p in attack.powers:
		p.is_active = False
		for c in p.casts:
			c.is_active = False

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
		self.dmg = 0

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

		left_down_light_hitbox_shapes = add_capsule_shape(self.body, (-8, -4), 10, 5)
		right_down_light_hitbox_shapes = add_capsule_shape(self.body, (8, -4), 10, 5)
		
		left_aerial_neutral_light_hitbox_shapes_1 = add_capsule_shape(self.body, (-7, 1), 5, 10)
		right_aerial_neutral_light_hitbox_shapes_1 = add_capsule_shape(self.body, (7, 1), 5, 10)

		left_aerial_neutral_light_hitbox_shapes_2 = add_capsule_shape(self.body, (-7, -1), 4, 3) + add_capsule_shape(self.body, (-9, 2), 8, 4)
		right_aerial_neutral_light_hitbox_shapes_2 = add_capsule_shape(self.body, (7, -1), 4, 3) + add_capsule_shape(self.body, (9, 2), 8, 4)

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
			+ left_down_light_hitbox_shapes + right_down_light_hitbox_shapes
			+ left_aerial_neutral_light_hitbox_shapes_1 + right_aerial_neutral_light_hitbox_shapes_1
			+ left_aerial_neutral_light_hitbox_shapes_2 + right_aerial_neutral_light_hitbox_shapes_2
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

def pre_solve_hurtbox_hitbox(arbiter: pymunk.Arbiter, space: pymunk.Space, data) -> bool:
	victim: Fighter = arbiter.shapes[0].fighter
	if victim.is_hit == False:
		print("connected hit!")
		victim.is_hit = True
		cast: Cast = arbiter.shapes[1].cast
		power: Power = arbiter.shapes[1].power
		dir = 1
		if arbiter.shapes[1].side_facing == consts.FIGHTER_SIDE_FACING_LEFT:
			dir = -1

		impulse_scale = 1
		impulse = (impulse_scale*cast.fixed_force*dir, impulse_scale)
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
		current_cast: Cast = None
		current_power: Power = None

		is_doing_action = False
		if fighter.recover_timer == 0:
			for attack in fighter.attacks:
				if attack.is_active == False:
					attack.cooldown_timer = max(attack.cooldown_timer - 1, 0)
					continue
				
				if attack.recover_timer > 0:
					print("attack is recovering between powers")
					attack.recover_timer = max(attack.recover_timer - 1, 0)
					is_doing_action = True
					continue

				attack.cast_frame += 1
				current_power = attack.powers[attack.power_idx]
				current_cast = current_power.casts[attack.cast_idx]
				# the first active frame begins at the same frame as the last startup frame, which is why we subtract by 1, or 0 if no startup frames
				if attack.cast_frame > (max(current_cast.startup_frames-1, 0) + current_cast.active_frames):
					attack.cast_frame = 1
					attack.cast_idx += 1
					if current_cast.hitbox != None:
						if attack.side_facing == consts.FIGHTER_SIDE_FACING_LEFT:
							for shape in current_cast.hitbox.left_shapes:
								game_state.physics_sim.remove(shape)
						elif attack.side_facing == consts.FIGHTER_SIDE_FACING_RIGHT:
							for shape in current_cast.hitbox.right_shapes:
								game_state.physics_sim.remove(shape)
					if attack.cast_idx >= len(current_power.casts):
						attack.cast_idx = 0
						if attack.power_idx < len(attack.powers)-1:
							attack.recover_timer = current_power.recovery_frames + current_power.fixed_recovery_frames
						attack.power_idx += 1
						if attack.power_idx >= len(attack.powers):
							attack.power_idx = 0
							attack.is_active = False
							current_power = None
							current_cast = None
							continue
					
					current_power = attack.powers[attack.power_idx]
					current_cast = current_power.casts[attack.cast_idx]

				is_doing_action = True
				if current_power.is_active == False:
					current_power.is_active = True
					attack.cooldown_timer += current_power.cooldown_frames
					if attack.power_idx == len(attack.powers)-1:
						fighter.recover_timer = current_power.recovery_frames + current_power.fixed_recovery_frames

				if attack.cast_frame >= current_cast.startup_frames and current_cast.is_active == False:
					current_cast.is_active = True
					if current_cast.hitbox != None:
						if attack.side_facing == consts.FIGHTER_SIDE_FACING_LEFT:
							for shape in current_cast.hitbox.left_shapes:
								game_state.physics_sim.add(shape)
						elif attack.side_facing == consts.FIGHTER_SIDE_FACING_RIGHT:
							for shape in current_cast.hitbox.right_shapes:
								game_state.physics_sim.add(shape)

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
					activate_attack(fighter.down_light_attack, fighter.side_facing)
				elif dx != 0 and fighter.is_input_tapped(INPUT_LIGHT_HIT)  and fighter.side_light_attack.cooldown_timer == 0:
					activate_attack(fighter.side_light_attack, fighter.side_facing)
				elif dx == 0 and fighter.is_input_tapped(INPUT_LIGHT_HIT) and fighter.neutral_light_attack.cooldown_timer == 0:
					activate_attack(fighter.neutral_light_attack, fighter.side_facing)
			else:
				if fighter.input[INPUT_MOVE_DOWN] and fighter.is_input_tapped(INPUT_LIGHT_HIT) and fighter.aerial_down_light_attack.cooldown_timer == 0:
					activate_attack(fighter.aerial_down_light_attack, fighter.side_facing)
				elif dx != 0 and fighter.is_input_tapped(INPUT_LIGHT_HIT)  and fighter.aerial_side_light_attack.cooldown_timer == 0:
					activate_attack(fighter.aerial_side_light_attack, fighter.side_facing)
				elif dx == 0 and fighter.is_input_tapped(INPUT_LIGHT_HIT) and fighter.aerial_neutral_light_attack.cooldown_timer == 0:
					activate_attack(fighter.aerial_neutral_light_attack, fighter.side_facing)

		attack_velocity = (0,0)
		if is_doing_action and current_cast != None and current_cast.is_active and current_cast.active_velocity != None:
			attack_velocity = current_cast.active_velocity
			if fighter.side_facing == consts.FIGHTER_SIDE_FACING_LEFT:
				attack_velocity = -attack_velocity[0], attack_velocity[1]
		
		if is_doing_action or fighter.recover_timer == 0:
			fighter.body.velocity = dx + attack_velocity[0], fighter.body.velocity.y

		fighter.body.velocity = fighter.body.velocity.x, max(fighter.body.velocity.y, -FALL_VELOCITY) + attack_velocity[1]

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

	physics_draw_options = pymunk.pyglet_util.DrawOptions(batch=physics_batch)
	physics_draw_options.transform = pymunk.Transform.scaling(PIXELS_PER_WORLD_UNITS)
	game_state.physics_sim.debug_draw(physics_draw_options)
	physics_batch.draw()
	pass

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


