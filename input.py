INPUT_MOVE_LEFT = 0
INPUT_MOVE_RIGHT = 1
INPUT_MOVE_DOWN = 2
INPUT_JUMP = 3
INPUT_DODGE = 4
INPUT_HEAVY_HIT = 5
INPUT_LIGHT_HIT = 6
INPUT_THROW = 7

class Input():
	def __init__(self):	
		self.current = [False] * 8
		self.prev = [False] * 8
	def is_tapped(self, input_index) -> bool:
		return self.current[input_index] and self.prev[input_index] == False
	def is_pressed(self, input_index) -> bool:
		return self.current[input_index]
	def is_one_pressed(self, input_indices) -> bool:
		b = True
		for idx in input_indices:
			b = b or self.current[idx]
		return b
	def are_pressed(self, input_indices) -> bool:
		b = True
		for idx in input_indices:
			b = b and self.current[idx]
		return b
	def copy_current_to_previous(self):
		for i, v in enumerate(self.current):
			self.prev[i] = v