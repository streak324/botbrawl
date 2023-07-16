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

def draw_capsule(x: float, y: float, radius: float, stretch_h: float, color: arcade.Color):
	arcade.draw_rectangle_filled(x, y, 2*radius, stretch_h, color)
	arcade.draw_arc_filled(x, y+stretch_h*0.5, 2*radius, 2*radius, color, start_angle=0, end_angle=180)
	arcade.draw_arc_filled(x, y-stretch_h*0.5, 2*radius, 2*radius, color, start_angle=180, end_angle=360)

class Player():
	def __init__(self, x: int = 0, y: int = 0):
		self.x = 0
		self.y = 0

INPUT_MOVE_LEFT = 0
INPUT_MOVE_RIGHT = 1
INPUT_MOVE_SIDE_PRECEDENCE = 2
INPUT_JUMP = 3

SIDE_PRECEDENCE_LEFT = 1
SIDE_PRECEDENCE_RIGHT = 2

class MyGameWindow(arcade.Window):
	def __init__(self, width, height, title):
		self.pos = (200, 400)
		self.platform_lrtb = (100, 1100, 300, 100)
		self.input = numpy.zeros(4)
		self.prev_input = numpy.zeros(4)
		self.physics_engine = pymunk.
		super().__init__(width, height, title)
		arcade.set_background_color(arcade.color.ALMOND)

	def setup(self):
		""" Set up the game variables. Call to re-start the game. """
		# Create your sprites and sprite lists here
		pass

	def on_draw(self):
		self.clear()
		r = 72
		h = 16
		hitbox_color = (171, 174, 105, 128)
		draw_capsule(self.pos[0],self.pos[1],r,h,hitbox_color)
		arcade.draw_lrtb_rectangle_filled(self.platform_lrtb[0], self.platform_lrtb[1], self.platform_lrtb[2], self.platform_lrtb[3], arcade.color.YELLOW)

	def on_update(self, delta_time):
		dx = ((float)((self.input[INPUT_MOVE_SIDE_PRECEDENCE] != SIDE_PRECEDENCE_LEFT or self.input[INPUT_MOVE_LEFT] == False) and self.input[INPUT_MOVE_RIGHT]) \
			- \
			(float)((self.input[INPUT_MOVE_SIDE_PRECEDENCE] != SIDE_PRECEDENCE_RIGHT or self.input[INPUT_MOVE_RIGHT] == False) and self.input[INPUT_MOVE_LEFT]))
		self.pos = (self.pos[0] + dx, self.pos[1])
		self.prev_input = self.input.copy()

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