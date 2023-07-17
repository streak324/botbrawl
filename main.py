import arcade
import numpy
import pymunk

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

SIDE_PRECEDENCE_LEFT = 1
SIDE_PRECEDENCE_RIGHT = 2

#not sure how im going to do this one yet.
PIXELS_PER_WORLD_UNITS = 10

#world units
HURTBOX_CAPSULE_RADIUS = 72 / PIXELS_PER_WORLD_UNITS
#world units
HURTBOX_CAPSULE_STRETCH_LENGTH= 16 / PIXELS_PER_WORLD_UNITS

HURTBOX_COLOR = (171, 174, 105, 128)

TIMESTEP = 1/60

FIGHTER_COLLISION_TYPE = 1
PLATFORM_COLLISION_TYPE = 2

FALL_VELOCITY = 25.0

def draw_capsule_world_to_pixel(x: float, y: float, radius, stretch_h: float, color: arcade.Color):
	draw_capsule(x*PIXELS_PER_WORLD_UNITS, y*PIXELS_PER_WORLD_UNITS, radius*PIXELS_PER_WORLD_UNITS, stretch_h*PIXELS_PER_WORLD_UNITS, color)

def draw_capsule(x: float, y: float, radius: float, stretch_h: float, color: arcade.Color):
	arcade.draw_rectangle_filled(x, y, 2*radius, stretch_h, color)
	arcade.draw_arc_filled(x, y+stretch_h*0.5, 2*radius, 2*radius, color, start_angle=0, end_angle=180)
	arcade.draw_arc_filled(x, y-stretch_h*0.5, 2*radius, 2*radius, color, start_angle=180, end_angle=360)

class Platform(): 
	def __init__(self, space: pymunk.Space, min: tuple[float,float], max: tuple[float,float], physics_color: arcade.Color):
		b = pymunk.Body(body_type = pymunk.Body.STATIC)
		b._set_position((0, 0))
		shape = pymunk.Segment(b, ((min[0]+max[0])*0.5, max[1]), ((min[0]+max[0])*0.5, min[1]), max[0]-min[0])
		shape.collision_type = PLATFORM_COLLISION_TYPE
		space.add(b,shape)
		self.min = min
		self.max = max
		self.physics_color = physics_color
		shape.friction = 1.0
	def draw_physics(self, pixels_per_world_units):
		arcade.draw_lrtb_rectangle_filled(self.min[0]*pixels_per_world_units, self.max[0]*pixels_per_world_units, self.max[1]*pixels_per_world_units, self.min[1]*pixels_per_world_units, self.physics_color)

class Fighter():
	def __init__(self, space: pymunk.Space, center: tuple[float, float]):
		#hurtbox body is supposed to be the shape of a capsule: 2 circles and 1 rectangle
		self.hurtbox_body = pymunk.Body(mass=1, moment=float("inf"))
		self.hurtbox_body._set_position(center)
		self.hurtbox_c1 = pymunk.Circle(self.hurtbox_body, HURTBOX_CAPSULE_RADIUS, offset=(0, HURTBOX_CAPSULE_STRETCH_LENGTH*0.5))
		#self.hurtbox_c1.filter = pymunk.ShapeFilter(categories=0b1, mask=0b10)
		self.hurtbox_c1.collision_type = FIGHTER_COLLISION_TYPE
		self.hurtbox_c2 = pymunk.Circle(self.hurtbox_body, HURTBOX_CAPSULE_RADIUS, offset=(0, -HURTBOX_CAPSULE_STRETCH_LENGTH*0.5))
		#self.hurtbox_c2.filter = pymunk.ShapeFilter(categories=0b1, mask=0b10)
		self.hurtbox_c2.collision_type = FIGHTER_COLLISION_TYPE
		self.hurtbox_box = pymunk.Poly.create_box(self.hurtbox_body, (2*HURTBOX_CAPSULE_RADIUS, HURTBOX_CAPSULE_STRETCH_LENGTH))
		self.hurtbox_box.collision_type = FIGHTER_COLLISION_TYPE
		space.add(self.hurtbox_body, self.hurtbox_c1, self.hurtbox_c2, self.hurtbox_box)

	def draw_physics(self, pixels_per_world_units):
		bodyp = self.hurtbox_body._get_position()
		c1p = self.hurtbox_c1.center_of_gravity.__add__(bodyp)
		arcade.draw_arc_filled(c1p.x*pixels_per_world_units, c1p.y*pixels_per_world_units, 2*HURTBOX_CAPSULE_RADIUS*pixels_per_world_units, 2*HURTBOX_CAPSULE_RADIUS*pixels_per_world_units, HURTBOX_COLOR, start_angle=0, end_angle=180)
		c2p = self.hurtbox_c2.center_of_gravity.__add__(bodyp)
		arcade.draw_arc_filled(c2p.x*pixels_per_world_units, c2p.y*pixels_per_world_units, 2*HURTBOX_CAPSULE_RADIUS*pixels_per_world_units, 2*HURTBOX_CAPSULE_RADIUS*pixels_per_world_units, HURTBOX_COLOR, start_angle=180, end_angle=360)
		boxp = self.hurtbox_box.center_of_gravity.__add__(bodyp)
		arcade.draw_rectangle_filled(boxp.x*pixels_per_world_units, boxp.y*pixels_per_world_units, 2*HURTBOX_CAPSULE_RADIUS*pixels_per_world_units, HURTBOX_CAPSULE_STRETCH_LENGTH*pixels_per_world_units, HURTBOX_COLOR)
		pass

def always_collide(arb: pymunk.Arbiter, space: pymunk.Space, data: any) -> bool:
	print("hi!!!")
	return True

class MyGameWindow(arcade.Window):
	def __init__(self, width, height, title):
		self.platform_lrtb = (100, 1100, 300, 100)
		self.input = numpy.zeros(4)
		self.prev_input = numpy.zeros(4)
		self.physics_sim = pymunk.Space()
		self.physics_sim._set_gravity((0,-100))

		self.fighter = Fighter(self.physics_sim, (20,40))

		self.platform = Platform(self.physics_sim, (10,10), (110,30), arcade.csscolor.YELLOW)

		handler = self.physics_sim.add_collision_handler(FIGHTER_COLLISION_TYPE, PLATFORM_COLLISION_TYPE)
		handler.begin = always_collide

		super().__init__(width, height, title)
		arcade.set_background_color(arcade.color.ALMOND)

	def setup(self):
		""" Set up the game variables. Call to re-start the game. """
		# Create your sprites and sprite lists here
		pass

	def on_draw(self):
		self.clear()
		self.platform.draw_physics(PIXELS_PER_WORLD_UNITS)
		self.fighter.draw_physics(PIXELS_PER_WORLD_UNITS)
		#pos = self.fighter.hurtbox_body._get_position()
		#draw_capsule_world_to_pixel(pos.x,pos.y,HURTBOX_CAPSULE_RADIUS,HURTBOX_CAPSULE_STRETCH_LENGTH,HURTBOX_COLOR)

	def on_update(self, delta_time):
		dx = 50 * ((float)((self.input[INPUT_MOVE_SIDE_PRECEDENCE] != SIDE_PRECEDENCE_LEFT or self.input[INPUT_MOVE_LEFT] == False) and self.input[INPUT_MOVE_RIGHT]) \
			- \
			(float)((self.input[INPUT_MOVE_SIDE_PRECEDENCE] != SIDE_PRECEDENCE_RIGHT or self.input[INPUT_MOVE_RIGHT] == False) and self.input[INPUT_MOVE_LEFT]))
		self.fighter.hurtbox_body.velocity = (dx, max(self.fighter.hurtbox_body.velocity.y, -FALL_VELOCITY))
		self.prev_input = self.input.copy()
		self.physics_sim.step(TIMESTEP)

	def on_key_press(self, key, key_modifiers):
		if key == arcade.key.LEFT:
			self.input[INPUT_MOVE_LEFT] = True
			self.input[INPUT_MOVE_SIDE_PRECEDENCE] = SIDE_PRECEDENCE_LEFT
		if key == arcade.key.RIGHT:
			self.input[INPUT_MOVE_RIGHT] = True
			self.input[INPUT_MOVE_SIDE_PRECEDENCE] = SIDE_PRECEDENCE_RIGHT

	def on_key_release(self, key, key_modifiers):
		if key == arcade.key.LEFT:
			self.input[INPUT_MOVE_LEFT] = False
		if key == arcade.key.RIGHT:
			self.input[INPUT_MOVE_RIGHT] = False

	def on_mouse_motion(self, x, y, delta_x, delta_y):
		"""
		Called whenever the mouse moves.
		"""
		pass

	def on_mouse_press(self, x, y, button, key_modifiers):
		"""
		Called when the user presses a mouse button.
		"""
		pass

	def on_mouse_release(self, x, y, button, key_modifiers):
		"""
		Called when a user releases a mouse button.
		"""
		pass


def main():
	game = MyGameWindow(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
	game.setup()
	arcade.run()


if __name__ == "__main__":
	main()