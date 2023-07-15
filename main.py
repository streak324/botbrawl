import arcade

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
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

INPUT_JUMP = 0
INPUT_MOVE_LEFT = 1
INPUT_MOVE_RIGHT = 2
INPUT_MOVE_DOWN = 3

class GameState():
	pass

class Game():
	def __init__(self, player_positions: list[tuple[float, float]] = []):
		self.fighters = [Player(p.x, p.y) for p in range(player_positions)]
	def step(self, inputs: list[tuple]) -> GameState:
		pass


class MyGameWindow(arcade.Window):
	"""
	Main application class.

	NOTE: Go ahead and delete the methods you don't need.
	If you do need a method, delete the 'pass' and replace it
	with your own code. Don't leave 'pass' in this program.
	"""

	def __init__(self, width, height, title):
		self.pos = (200, 300)
		#0, 1, -1 should be valid values
		self.move_side_dir = 0
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

	def on_update(self, delta_time):
		dx = self.move_side_dir * 10
		self.pos = (self.pos[0] + dx, self.pos[1])
		pass

	def on_key_press(self, key, key_modifiers):
		if key == arcade.key.LEFT:
			self.move_side_dir = -1
		if key == arcade.key.RIGHT:
			self.move_side_dir = 1


	def on_key_release(self, key, key_modifiers):
		if key == arcade.key.LEFT:
			self.move_side_dir += 1
		if key == arcade.key.RIGHT:
			self.move_side_dir -= 1
		pass

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