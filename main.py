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
INPUT_MOVE_SIDE_PRECEDENCE = 2
INPUT_JUMP = 3
INPUT_DODGE = 4
INPUT_HEAVY_HIT = 5
INPUT_LIGHT_HIT = 6
INPUT_THROW = 7

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

FALL_VELOCITY = 60.0

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
	def __init__(self, shapes: list[pymunk.Shape], active_frames: int, cooldown_frames: int):
		self.shapes = shapes
		self.active_frames = active_frames
		self.cooldown_frames = cooldown_frames
		self.cooldown_timer = 0
		self.active_timer = 0
		self.is_active = False
	def activate(self, space: pymunk.Space):
		self.is_active = True
		self.active_timer = self.active_frames
		for shape in self.shapes:
			space.add(shape)
	def deactivate(self, space: pymunk.Space):
		self.is_active = False
		self.cooldown_timer = self.cooldown_frames
		for shape in self.shapes:
			space.remove(shape)

class Fighter():
	def __init__(self, space: pymunk.Space, center: tuple[float, float], facing = consts.FIGHTER_FACING_LEFT):
		#hurtbox body is supposed to be the shape of a capsule: 2 circles and 1 rectangle
		self.facing = facing
		self.input = numpy.zeros(8)
		self.prev_input = numpy.zeros(8)
		self.body = pymunk.Body(mass=5, moment=float("inf"))
		self.body._set_position(center)
		space.add(self.body)
		self.hitboxes: list[Hitbox] = []

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

		right_neutral_light_hitbox_shapes = add_capsule_shape(self.body, (12,0), 6, 5)
		for shape in right_neutral_light_hitbox_shapes:
			shape.collision_type = HITBOX_COLLISION_TYPE	
			shape.filter = hitbox_filter
			shape.sensor = True
			shape.color = (128, 0, 0, 255)
		self.right_neutral_light_hitbox = Hitbox(right_neutral_light_hitbox_shapes, consts.NEUTRAL_LIGHT_HIT_ACTIVE_FRAMES, consts.NEUTRAL_LIGHT_HIT_COOLDOWN_FRAMES)
		self.hitboxes.append(self.right_neutral_light_hitbox)

		left_neutral_light_hitbox_shapes = add_capsule_shape(self.body, (-12,0), 6, 5)
		for shape in left_neutral_light_hitbox_shapes:
			shape.collision_type = HITBOX_COLLISION_TYPE	
			shape.filter = hitbox_filter
			shape.sensor = True
			shape.color = (128, 0, 0, 255)
		self.left_neutral_light_hitbox = Hitbox(left_neutral_light_hitbox_shapes, consts.NEUTRAL_LIGHT_HIT_ACTIVE_FRAMES, consts.NEUTRAL_LIGHT_HIT_COOLDOWN_FRAMES)
		self.hitboxes.append(self.left_neutral_light_hitbox)

		self.midair_jumps_left = 0
		self.is_grounded = False

		#number of frames fighter must wait before attempting a new action (dodge, move, hit).
		self.recover_cooldown = 0

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
		self.physics_sim._set_gravity((0,-100))
		self.fighters = [Fighter(self.physics_sim, (30,100)), Fighter(self.physics_sim, (70, 100))]

		wall_body = pymunk.Body(body_type=pymunk.Body.STATIC)
		p1 = create_pymunk_box(wall_body, (20, 10), (120,30))
		p1.collision_type = WALL_COLLISION_TYPE
		p1.filter = wall_collision_filter
		p1.friction = 1
		p2 = create_pymunk_box(wall_body, (20, 10), (10,100))
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
		dx = 50 * ((float)((fighter.input[INPUT_MOVE_SIDE_PRECEDENCE] != SIDE_PRECEDENCE_LEFT or fighter.input[INPUT_MOVE_LEFT] == False) and fighter.input[INPUT_MOVE_RIGHT]) \
			- \
			(float)((fighter.input[INPUT_MOVE_SIDE_PRECEDENCE] != SIDE_PRECEDENCE_RIGHT or fighter.input[INPUT_MOVE_RIGHT] == False) and fighter.input[INPUT_MOVE_LEFT]))
		fighter.body.velocity = min(max(-50, fighter.body.velocity.x), 50), max(fighter.body.velocity.y, -FALL_VELOCITY)
		fighter.compute_grounding()
		y_force = 0
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

		fighter.body.apply_impulse_at_local_point((dx, y_force))

		is_doing_action = False
		for hitbox in fighter.hitboxes:
			if hitbox.is_active:
				is_doing_action = True
				hitbox.active_timer = max(hitbox.active_timer - 1, 0)
				if hitbox.active_timer <= 0:
					hitbox.deactivate(game_state.physics_sim)
			else:
				hitbox.cooldown_timer = max(hitbox.cooldown_timer - 1, 0)

		fighter.recover_cooldown = max(fighter.recover_cooldown-1, 0)
		if fighter.is_input_tapped(INPUT_LIGHT_HIT) and fighter.recover_cooldown == 0 and is_doing_action == False and fighter.right_neutral_light_hitbox.cooldown_timer == 0:
			fighter.recover_cooldown = consts.NEUTRAL_LIGHT_HIT_RECOVERY_FRAMES
			fighter.right_neutral_light_hitbox.activate(game_state.physics_sim)
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
		fighter.input[INPUT_MOVE_SIDE_PRECEDENCE] = SIDE_PRECEDENCE_LEFT
	if key == pyglet.window.key.RIGHT:
		fighter.input[INPUT_MOVE_RIGHT] = True
		fighter.input[INPUT_MOVE_SIDE_PRECEDENCE] = SIDE_PRECEDENCE_RIGHT
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


