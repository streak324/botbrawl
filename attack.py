import pymunk
import consts

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
	def activate(self, side_facing: int):
		print("activating attack {} facing {}".format(self.name, side_facing))
		self.is_active = True
		self.cast_frame = 0
		self.power_idx = 0
		self.cast_idx = 0
		self.side_facing = side_facing
		self.cooldown_timer = 0
		self.recover_timer = 0
		for p in self.powers:
			p.is_active = False
			for c in p.casts:
				c.is_active = False

	def step(self, space: pymunk.Space) -> (Cast, bool):
		if self.is_active == False:
			self.cooldown_timer = max(self.cooldown_timer - 1, 0)
			return (None, False)
		current_power = self.powers[self.power_idx]
		current_cast = current_power.casts[self.cast_idx]
		
		if self.recover_timer > 0:
			self.recover_timer = max(self.recover_timer - 1, 0)
			return (current_cast, True)
		
		self.cast_frame += 1
		# the first active frame begins at the same frame as the last startup frame, which is why we subtract by 1, or 0 if no startup frames
		if self.cast_frame > (max(current_cast.startup_frames-1, 0) + current_cast.active_frames):
			self.cast_frame = 1
			self.cast_idx += 1
			if current_cast.hitbox != None:
				if self.side_facing == consts.FIGHTER_SIDE_FACING_LEFT:
					for shape in current_cast.hitbox.left_shapes:
						space.remove(shape)
				elif self.side_facing == consts.FIGHTER_SIDE_FACING_RIGHT:
					for shape in current_cast.hitbox.right_shapes:
						space.remove(shape)
			if self.cast_idx >= len(current_power.casts):
				self.cast_idx = 0
				if self.power_idx < len(self.powers)-1:
					self.recover_timer = current_power.recovery_frames + current_power.fixed_recovery_frames
				self.power_idx += 1
				if self.power_idx >= len(self.powers):
					self.power_idx = 0
					self.is_active = False
					current_power = None
					current_cast = None
					return (None, False)
			
			current_power = self.powers[self.power_idx]
			current_cast = current_power.casts[self.cast_idx]

		if current_power.is_active == False:
			current_power.is_active = True
			self.cooldown_timer += current_power.cooldown_frames
			if self.power_idx == len(self.powers)-1:
				self.recover_timer = current_power.recovery_frames + current_power.fixed_recovery_frames

		if self.cast_frame >= current_cast.startup_frames and current_cast.is_active == False:
			current_cast.is_active = True
			if current_cast.hitbox != None:
				if self.side_facing == consts.FIGHTER_SIDE_FACING_LEFT:
					for shape in current_cast.hitbox.left_shapes:
						space.add(shape)
				elif self.side_facing == consts.FIGHTER_SIDE_FACING_RIGHT:
					for shape in current_cast.hitbox.right_shapes:
						space.add(shape)
		return (current_cast, True)