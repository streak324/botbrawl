import math
import numpy
import pymunk
import pyglet
import pymunk.pyglet_util
from pymunk.vec2d import Vec2d

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

TOTAL_MIDAIR_JUMPS_ALLOWED = 2

SIDE_PRECEDENCE_LEFT = 1
SIDE_PRECEDENCE_RIGHT = 2

JUMP_HEIGHT = 15

#not sure how im going to do this one yet.
PIXELS_PER_WORLD_UNITS = 10

#world units
HURTBOX_CAPSULE_RADIUS = 72 / PIXELS_PER_WORLD_UNITS
#world units
HURTBOX_CAPSULE_STRETCH_LENGTH= 16 / PIXELS_PER_WORLD_UNITS

HURTBOX_COLOR = (171, 174, 105, 128)

TIMESTEP = 1/60

HURTBOX_COLLISION_TYPE = 1
HITBOX_SENSOR_COLLISION_TYPE = 2
WALL_COLLISION_TYPE = 3
FEET_COLLISION_TYPE = 4

FALL_VELOCITY = 60.0


wall_collision_filter = pymunk.ShapeFilter( \
	categories=0b1 << (WALL_COLLISION_TYPE-1), \
	mask=0b1 << (FEET_COLLISION_TYPE-1))

def create_pymunk_box(body: pymunk.Body, min: tuple[float,float], max: tuple[float,float], radus: float = 0):
	return pymunk.Poly(body, [min, (max[0], min[1]), max, (min[0], max[1])], radius=0)

class Fighter():
	def __init__(self, space: pymunk.Space, center: tuple[float, float]):
		#hurtbox body is supposed to be the shape of a capsule: 2 circles and 1 rectangle
		self.body = pymunk.Body(mass=5, moment=float("inf"))
		self.body._set_position(center)
		self.hurtbox_c1 = pymunk.Circle(self.body, HURTBOX_CAPSULE_RADIUS, offset=(0, HURTBOX_CAPSULE_STRETCH_LENGTH*0.5))
		hurtbox_filter = pymunk.ShapeFilter( \
			categories=0b1 << (HURTBOX_COLLISION_TYPE-1), \
			mask=0b1 << (HITBOX_SENSOR_COLLISION_TYPE-1))

		feet_wall_filter = pymunk.ShapeFilter( \
			categories=0b1 << (FEET_COLLISION_TYPE-1), \
			mask=0b1 << (WALL_COLLISION_TYPE-1))

		self.hurtbox_c1.collision_type = HURTBOX_COLLISION_TYPE
		self.hurtbox_c1.filter = hurtbox_filter
		self.hurtbox_c1.sensor = True
		self.hurtbox_c2 = pymunk.Circle(self.body, HURTBOX_CAPSULE_RADIUS, offset=(0, -HURTBOX_CAPSULE_STRETCH_LENGTH*0.5))
		self.hurtbox_c2.collision_type = HURTBOX_COLLISION_TYPE
		self.hurtbox_c2.filter = hurtbox_filter
		self.hurtbox_c2.sensor = True
		self.hurtbox_box = pymunk.Poly.create_box(self.body, (2*HURTBOX_CAPSULE_RADIUS, HURTBOX_CAPSULE_STRETCH_LENGTH))
		self.hurtbox_box.collision_type = HURTBOX_COLLISION_TYPE
		self.hurtbox_box.filter = hurtbox_filter
		self.hurtbox_box.sensor = True

		self.feet = create_pymunk_box(self.body,
			(-HURTBOX_CAPSULE_RADIUS, -HURTBOX_CAPSULE_RADIUS-HURTBOX_CAPSULE_STRETCH_LENGTH*0.5-0.5), 
			(HURTBOX_CAPSULE_RADIUS, HURTBOX_CAPSULE_STRETCH_LENGTH*0.5+HURTBOX_CAPSULE_RADIUS*0.5)
		)
		self.feet.collision_type = FEET_COLLISION_TYPE
		self.feet.filter = feet_wall_filter
		self.feet.friction = 1
		self.feet.color = (255, 233, 28, 100)

		space.add(self.body, self.hurtbox_c1, self.hurtbox_c2, self.hurtbox_box, self.feet)

		self.midair_jumps_left = 0
		self.is_grounded = False

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


# Set up collision handler
def post_solve_separate_fighter_from_wall(arbiter, space, data):
	impulse = arbiter.total_impulse
	print(impulse)
	return True


class GameState():
	def __init__(self):
		self.physics_sim = pymunk.Space()
		self.input = numpy.zeros(4)
		self.prev_input = numpy.zeros(4)
		self.physics_sim._set_gravity((0,-100))
		self.fighter = Fighter(self.physics_sim, (30,100))

		wall_body = pymunk.Body(body_type=pymunk.Body.STATIC)
		p1 = create_pymunk_box(wall_body, (20, 10), (100,30))
		p1.collision_type = WALL_COLLISION_TYPE
		p1.filter = wall_collision_filter
		p1.friction = 1
		p2 = create_pymunk_box(wall_body, (20, 10), (10,100))
		p2.collision_type = WALL_COLLISION_TYPE
		p2.filter = wall_collision_filter
		#p2.friction = 1
		p3 = create_pymunk_box(wall_body, (90, 30), (100,100))
		p3.collision_type = WALL_COLLISION_TYPE
		p3.filter = wall_collision_filter
		#p3.friction = 1
		self.physics_sim.add(wall_body, p1, p2, p3)

		self.handler = self.physics_sim.add_collision_handler(FEET_COLLISION_TYPE, WALL_COLLISION_TYPE)
		self.handler.post_solve = post_solve_separate_fighter_from_wall
		self.gravity_enabled = True

game_state = GameState()

def step_game(_):
	dx = 50 * ((float)((game_state.input[INPUT_MOVE_SIDE_PRECEDENCE] != SIDE_PRECEDENCE_LEFT or game_state.input[INPUT_MOVE_LEFT] == False) and game_state.input[INPUT_MOVE_RIGHT]) \
		- \
		(float)((game_state.input[INPUT_MOVE_SIDE_PRECEDENCE] != SIDE_PRECEDENCE_RIGHT or game_state.input[INPUT_MOVE_RIGHT] == False) and game_state.input[INPUT_MOVE_LEFT]))
	game_state.fighter.body.velocity = min(max(-50, game_state.fighter.body.velocity.x), 50), max(game_state.fighter.body.velocity.y, -FALL_VELOCITY)
	game_state.fighter.compute_grounding()
	y_force = 0
	if (game_state.prev_input[INPUT_JUMP] == False and game_state.input[INPUT_JUMP] and
		(game_state.fighter.is_grounded or game_state.fighter.midair_jumps_left > 0)
		):
		print("JUMPING")
		#only subtract midair jumps if fighter is not grounded
		game_state.fighter.midair_jumps_left -= int(not game_state.fighter.is_grounded)
		vel = game_state.fighter.body.velocity
		game_state.fighter.body.velocity = (vel.x, 0)
		jump_v = math.sqrt(2.0 * JUMP_HEIGHT * abs(game_state.physics_sim.gravity.y))
		y_force = game_state.fighter.body.mass * jump_v

	game_state.fighter.body.apply_impulse_at_local_point((dx, y_force))

	game_state.physics_sim.step(TIMESTEP)

	game_state.prev_input = game_state.input.copy()

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
	if key == pyglet.window.key.LEFT:
		game_state.input[INPUT_MOVE_LEFT] = True
		game_state.input[INPUT_MOVE_SIDE_PRECEDENCE] = SIDE_PRECEDENCE_LEFT
	if key == pyglet.window.key.RIGHT:
		game_state.input[INPUT_MOVE_RIGHT] = True
		game_state.input[INPUT_MOVE_SIDE_PRECEDENCE] = SIDE_PRECEDENCE_RIGHT
	if key == pyglet.window.key.UP:
		game_state.input[INPUT_JUMP] = True
	if key == pyglet.window.key.O:
		game_state.gravity_enabled = not game_state.gravity_enabled
		if game_state.gravity_enabled:
			game_state.physics_sim._set_gravity((0,-100))
		else:
			game_state.physics_sim._set_gravity((0,0))
			game_state.fighter.body._set_velocity((0,0))

@game_window.event
def on_key_release(key, modifiers):
	if key == pyglet.window.key.LEFT:
		game_state.input[INPUT_MOVE_LEFT] = False
	if key == pyglet.window.key.RIGHT:
		game_state.input[INPUT_MOVE_RIGHT] = False
	if key == pyglet.window.key.UP:
		game_state.input[INPUT_JUMP] = False

if __name__ == "__main__":
	pyglet.clock.schedule_interval(step_game, TIMESTEP)
	pyglet.app.run()


