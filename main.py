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
HURTBOX_CAPSULE_LENGTH = 16 / PIXELS_PER_WORLD_UNITS

HURTBOX_COLOR = (171, 174, 105, 128)

TIMESTEP = 1/60

def draw_capsule_world_to_pixel(x: float, y: float, radius, stretch_h: float, color: arcade.Color):
	draw_capsule(x*PIXELS_PER_WORLD_UNITS, y*PIXELS_PER_WORLD_UNITS, radius*PIXELS_PER_WORLD_UNITS, stretch_h*PIXELS_PER_WORLD_UNITS, color)

def draw_capsule(x: float, y: float, radius: float, stretch_h: float, color: arcade.Color):
	arcade.draw_rectangle_filled(x, y, 2*radius, stretch_h, color)
	arcade.draw_arc_filled(x, y+stretch_h*0.5, 2*radius, 2*radius, color, start_angle=0, end_angle=180)
	arcade.draw_arc_filled(x, y-stretch_h*0.5, 2*radius, 2*radius, color, start_angle=180, end_angle=360)

def do_nothing(arb, space, data) -> bool:
	print("collision!")
	return False

class Platform(): 
	def __init__(self, space: pymunk.Space, min: tuple[float,float], max: tuple[float,float], physics_color: arcade.Color):
		b = pymunk.Body(body_type = pymunk.Body.STATIC)
		b._set_position(((min[0]+max[0])*0.5, (min[1]+max[1])*0.5))
		shape = pymunk.Segment(b, (0, max[1]), (0, min[1]), max[1]-min[0])
		space.add(b,shape)
		self.min = min
		self.max = max
		self.physics_color = physics_color
	def draw_physics(self, pixels_per_world_units):
		arcade.draw_lrtb_rectangle_filled(self.min[0]*pixels_per_world_units, self.max[0]*pixels_per_world_units, self.max[1]*pixels_per_world_units, self.min[1]*pixels_per_world_units, self.physics_color)

class MyGameWindow(arcade.Window):
	def __init__(self, width, height, title):
		self.platform_lrtb = (100, 1100, 300, 100)
		self.input = numpy.zeros(4)
		self.prev_input = numpy.zeros(4)
		self.physics_sim = pymunk.Space()
		self.physics_sim._set_gravity((0,-10))

		self.fighter_body = pymunk.Body(mass=1, moment=10)
		self.fighter_body._set_position((20, 40))
		c1 = pymunk.Circle(self.fighter_body, HURTBOX_CAPSULE_RADIUS, offset=(0, HURTBOX_CAPSULE_LENGTH*0.5))
		c1.collision_type = 1
		c1.filter = pymunk.ShapeFilter(group=1)
		c2 = pymunk.Circle(self.fighter_body, HURTBOX_CAPSULE_RADIUS, offset=(0, -HURTBOX_CAPSULE_LENGTH*0.5))
		c2.collision_type = 1
		c2.filter = pymunk.ShapeFilter(group=1)
		seg = pymunk.Segment(self.fighter_body, (0., -HURTBOX_CAPSULE_LENGTH*0.5), (0., HURTBOX_CAPSULE_LENGTH*0.5), HURTBOX_CAPSULE_RADIUS)
		seg.collision_type = 1
		seg.filter = pymunk.ShapeFilter(group=1)
		self.physics_sim.add(self.fighter_body, c1,c2,seg)
		handler = self.physics_sim.add_collision_handler(1, 1)
		handler.begin = do_nothing

		self.platform = Platform(self.physics_sim, (10,10), (110,30), arcade.csscolor.YELLOW)

		super().__init__(width, height, title)
		arcade.set_background_color(arcade.color.ALMOND)

	def setup(self):
		""" Set up the game variables. Call to re-start the game. """
		# Create your sprites and sprite lists here
		pass

	def on_draw(self):
		self.clear()
		draw_capsule_world_to_pixel(self.fighter_body._get_position().x,self.fighter_body._get_position().y,HURTBOX_CAPSULE_RADIUS,HURTBOX_CAPSULE_LENGTH,HURTBOX_COLOR)
		self.platform.draw_physics(PIXELS_PER_WORLD_UNITS)

	def on_update(self, delta_time):
		dx = ((float)((self.input[INPUT_MOVE_SIDE_PRECEDENCE] != SIDE_PRECEDENCE_LEFT or self.input[INPUT_MOVE_LEFT] == False) and self.input[INPUT_MOVE_RIGHT]) \
			- \
			(float)((self.input[INPUT_MOVE_SIDE_PRECEDENCE] != SIDE_PRECEDENCE_RIGHT or self.input[INPUT_MOVE_RIGHT] == False) and self.input[INPUT_MOVE_LEFT]))
		self.fighter_body.apply_impulse_at_local_point((dx, 0))
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