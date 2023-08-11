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
INPUT_JUMP = 2
INPUT_DODGE = 3
INPUT_HEAVY_HIT = 4
INPUT_LIGHT_HIT = 5
INPUT_THROW = 6

TOTAL_MIDAIR_JUMPS_ALLOWED = 2

SIDE_PRECEDENCE_LEFT = 1
SIDE_PRECEDENCE_RIGHT = 2

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


def add_capsule_shape(body: pymunk.Body, offset: tuple[float,float], width: float, height: float) -> tuple[pymunk.Shape] :
	if width == height:
		return (pymunk.Circle(body, width, offset))
	if width > height:
		stretch_length = width - height
		c1 = pymunk.Circle(body, height*0.5, offset=(offset[0] - stretch_length*0.5, offset[1]))
		c2 = pymunk.Circle(body, height*0.5, offset=(offset[0] + stretch_length*0.5, offset[1]))
		box = create_pymunk_box(body, 
			(offset[0] - stretch_length*0.5, offset[1] - height*0.5), 
			(offset[0] + stretch_length*0.5, offset[1] + height*0.5))
		return (c1,c2,box)
	else:
		stretch_length = height - width
		c1 = pymunk.Circle(body, width*0.5, offset=(offset[0], offset[1] - stretch_length*0.5))
		c2 = pymunk.Circle(body, width*0.5, offset=(offset[0], offset[1] + stretch_length*0.5))
		box = create_pymunk_box(body, 
			(offset[0] - width*0.5, offset[1] - stretch_length*0.5), 
			(offset[0] + width*0.5, offset[1] + stretch_length*0.5))
		return (c1, c2, box)

class Hitbox():
	def __init__(self, left_shapes: list[pymunk.Shape], right_shapes: list[pymunk.Shape], active_frames: int, cooldown_frames: int):
		self.left_shapes = left_shapes
		self.right_shapes = right_shapes
		self.side_facing = 0
		self.active_frames = active_frames
		self.cooldown_frames = cooldown_frames
		self.cooldown_timer = 0
		self.active_timer = 0
		self.is_active = False
	def activate(self, side_facing: int, space: pymunk.Space):
		self.is_active = True
		self.active_timer = self.active_frames
		self.side_facing = side_facing
		if side_facing == consts.FIGHTER_SIDE_FACING_LEFT:
			for shape in self.left_shapes:
				space.add(shape)
		else:
			for shape in self.right_shapes:
				space.add(shape)
	def deactivate(self, space: pymunk.Space):
		self.is_active = False
		self.cooldown_timer = self.cooldown_frames
		if self.side_facing == consts.FIGHTER_SIDE_FACING_LEFT:
			for shape in self.left_shapes:
				space.remove(shape)
		else:
			for shape in self.right_shapes:
				space.remove(shape)

# to mimic brawlhalla, every attack move has a sequence of powers, and each power has a sequence of casts.
class Cast():
	#active_velocity is supposed to be used during active frames.
	#TODO: handle variable velocity. example: the last cast in unarmed side light attack, decelerates the speed of the fighter in each frame.
	def __init__(
			self, startup_frames: int, active_frames: int, base_dmg: int = 0, var_force: int = 0, fixed_force: int = 0, hitbox: Hitbox = None, 
	      	active_velocity: tuple[float, float] = (0,0), is_active_velocity_all_frames: bool = False
		):
		self.startup_frames = startup_frames
		self.active_frames = active_frames
		self.base_dmg = base_dmg
		self.var_force = var_force
		self.fixed_force = fixed_force
		self.hitbox = hitbox
		self.active_velocity = active_velocity
		self.is_active_velocity_all_frames = is_active_velocity_all_frames
		self.continuous_active_velocity = tuple[float,float]
		self.is_active = False

class Power():
	def __init__(self, casts: list[Cast], cooldown_frames: int = 0, fixed_recovery_frames: int = 0, recovery_frames: int = 0, min_charge_frames: int = 0, stun_frames = 0):
		self.casts = casts
		self.cooldown_frames = cooldown_frames
		self.fixed_recovery_frames = fixed_recovery_frames
		self.recovery_frames = recovery_frames
		self.min_charge_frames = min_charge_frames
		self.stun_frames = stun_frames
		self.is_active = False

class Attack():
	def __init__(self, powers: list[Power], start_velocity: (float,float)):
		self.powers = powers
		self.is_active = False
		self.cast_frame = 0
		self.power_idx = 0
		self.cast_idx = 0
		self.start_velocity = start_velocity
		self.cooldown_timer = 0
		self.side_facing = 0
		pass

def activate_attack(attack: Attack, side_facing: int) -> (float,float):
	attack.is_active = True
	attack.cast_frame = 0
	attack.power_idx = 0
	attack.cast_idx = 0
	attack.side_facing = side_facing
	for p in attack.powers:
		p.is_active = False
		for c in p.casts:
			c.is_active = False
	return attack.start_velocity

class StepAttackResults():
	def __init__(self, is_active: bool, recover_frames: int):
		self.is_active = is_active
		self.recover_frames = recover_frames

def step_attack(attack: Attack, space: pymunk.Space) -> StepAttackResults:
	if attack.is_active == False:
		attack.cooldown_timer = max(attack.cooldown_timer - 1, 0)
		return StepAttackResults(False, 0)

	attack.cast_frame += 1
	current_power = attack.powers[attack.power_idx]
	current_cast = current_power.casts[attack.cast_idx]
	# the first active frame begins at the same frame as the last startup frame, which is why we subtract by 1, or 0 if no startup frames
	if attack.cast_frame > (max(current_cast.startup_frames-1, 0) + current_cast.active_frames):
		print(attack.cast_frame, max(current_cast.startup_frames-1, 0) + current_cast.active_frames)
		attack.cast_frame = 0
		attack.cast_idx += 1
		if current_cast.hitbox != None:
			if attack.side_facing == consts.FIGHTER_SIDE_FACING_LEFT:
				for shape in current_cast.hitbox.left_shapes:
					space.remove(shape)
			elif attack.side_facing == consts.FIGHTER_SIDE_FACING_RIGHT:
				for shape in current_cast.hitbox.right_shapes:
					space.remove(shape)
		if attack.cast_idx >= len(current_power.casts):
			attack.cast_idx = 0
			attack.power_idx += 1
			if attack.power_idx >= len(attack.powers):
				attack.power_idx = 0
				attack.is_active = False
				return StepAttackResults(False, 0)

		return step_attack(attack, space)

	recovery_frames = 0
	if current_power.is_active == False:
		current_power.is_active = True
		recovery_frames = current_power.recovery_frames
		attack.cooldown_timer = 0

	if attack.cast_frame >= current_cast.startup_frames and current_cast.is_active == False:
		current_cast.is_active = True
		if current_cast.hitbox != None:
			if attack.side_facing == consts.FIGHTER_SIDE_FACING_LEFT:
				for shape in current_cast.hitbox.left_shapes:
					space.add(shape)
			elif attack.side_facing == consts.FIGHTER_SIDE_FACING_RIGHT:
				for shape in current_cast.hitbox.right_shapes:
					space.add(shape)

	return StepAttackResults(True, recovery_frames)

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

		hurtbox_filter = pymunk.ShapeFilter(
			categories=0b1 << (HURTBOX_COLLISION_TYPE-1),
			mask=0b1 << (HITBOX_COLLISION_TYPE-1))

		wall_collider_filter = pymunk.ShapeFilter(
			categories=0b1 << (FIGHTER_WALL_COLLIDER_COLLISION_TYPE-1),
			mask=0b1 << (WALL_COLLISION_TYPE-1))

		hitbox_filter = pymunk.ShapeFilter(
			categories=0b1 << (HITBOX_COLLISION_TYPE-1), 
			mask=0b1 << (HURTBOX_COLLISION_TYPE))

		hurtbox_shapes = add_capsule_shape(self.body, (0,0), HURTBOX_WIDTH, HURTBOX_HEIGHT)
		for shape in hurtbox_shapes:
			shape.collision_type = HURTBOX_COLLISION_TYPE 
			shape.filter = hurtbox_filter
			shape.sensor = True
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

		for shape in left_side_light_hitbox_shapes + right_side_light_hitbox_shapes:
			shape.collision_type = HITBOX_COLLISION_TYPE	
			shape.filter = hitbox_filter
			shape.sensor = True
			shape.color = (128, 0, 0, 255)

		self.side_light_attack = Attack([
			Power([
				Cast(startup_frames=2, active_frames=2, active_velocity=(10,0)), 
				Cast(startup_frames=3, active_frames=2, active_velocity=(20,10)),
				Cast(
					startup_frames=1, active_frames=4, active_velocity=(20,0), is_active_velocity_all_frames=True, base_dmg = 13, var_force=20, fixed_force=80,
					hitbox=Hitbox(
						left_side_light_hitbox_shapes, right_side_light_hitbox_shapes, 
						consts.NEUTRAL_LIGHT_HIT_ACTIVE_FRAMES, consts.NEUTRAL_LIGHT_HIT_COOLDOWN_FRAMES
					),
				)
			],
			cooldown_frames = 10, stun_frames = 18), 
			Power([Cast(startup_frames=0, active_frames=1, active_velocity=(20,0))], fixed_recovery_frames = 2, recovery_frames = 18)], 
			(1,0)
		)

		self.attacks.append(self.side_light_attack)

		self.midair_jumps_left = 0
		self.is_grounded = False

		#number of frames fighter must wait before attempting a new action (dodge, move, hit).
		self.recover_timer = 0

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


# Set up collision handler
def post_solve_separate_fighter_from_wall(arbiter, space, data):
	impulse = arbiter.total_impulse
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

		self.handler = self.physics_sim.add_collision_handler(FIGHTER_WALL_COLLIDER_COLLISION_TYPE, WALL_COLLISION_TYPE)
		self.handler.post_solve = post_solve_separate_fighter_from_wall
		self.gravity_enabled = True

game_state = GameState()

def step_game(_):
	for fighter in game_state.fighters:
		dx = 0

		is_doing_action = False
		for attack in fighter.attacks:
			results: StepAttackResults = step_attack(attack, game_state.physics_sim)
			is_doing_action = is_doing_action or results.is_active
			fighter.recover_timer = results.recover_frames

		if is_doing_action == False and fighter.recover_timer == 0 and (fighter.side_facing != consts.FIGHTER_SIDE_FACING_LEFT or fighter.input[INPUT_MOVE_LEFT] == False) and fighter.input[INPUT_MOVE_RIGHT]:
			fighter.side_facing = consts.FIGHTER_SIDE_FACING_RIGHT
			dx = 50
		
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

		if dx != 0 and fighter.is_input_tapped(INPUT_LIGHT_HIT) and fighter.recover_timer == 0 and is_doing_action == False and fighter.side_light_attack.cooldown_timer == 0:
			fighter.recover_timer = consts.NEUTRAL_LIGHT_HIT_RECOVERY_FRAMES
			activate_attack(fighter.side_light_attack, fighter.side_facing)
			dx = 0

		fighter.body.velocity = dx, max(fighter.body.velocity.y, -FALL_VELOCITY)
		#input should be copied into previous input AFTER all logic needing input has been processed
		fighter.prev_input = fighter.input.copy()


	fighter.recover_timer = max(fighter.recover_timer-1, 0)
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
		fighter.side_facing = consts.FIGHTER_SIDE_FACING_LEFT
	if key == pyglet.window.key.RIGHT:
		fighter.input[INPUT_MOVE_RIGHT] = True
		fighter.side_facing = consts.FIGHTER_SIDE_FACING_RIGHT
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


