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
			self, startup_frames: int, active_frames: int, base_dmg: int = 0, var_force: int = 0, fixed_force: int = 0, hitbox: Hitbox|None = None, 
		  	active_velocity: tuple[float, float]|None = None, is_active_velocity_all_frames: bool = False
		):
		self.startup_frames = startup_frames
		self.active_frames = active_frames
		self.base_dmg = base_dmg
		self.var_force = var_force
		self.fixed_force = fixed_force
		self.hitbox = hitbox
		# start velocity should be negated when attack is facing left
		self.active_velocity = active_velocity
		self.is_active_velocity_all_frames = is_active_velocity_all_frames
		self.is_active = False
		self.has_hit = False

class Power():
	def __init__(self, casts: list[Cast], cooldown_frames: int = 0, fixed_recovery_frames: int = 0, recovery_frames: int = 0, min_charge_frames: int = 0, stun_frames = 0, requires_hit: bool = False):
		self.casts = casts
		self.cooldown_frames = cooldown_frames
		self.fixed_recovery_frames = fixed_recovery_frames
		self.recovery_frames = recovery_frames
		self.min_charge_frames = min_charge_frames
		self.stun_frames = stun_frames
		self.requires_hit = requires_hit
		self.is_active = False

class Attack():
	def __init__(self, powers: list[Power], name: str):
		self.has_hit = False
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
		for power in self.powers:
			for cast in power.casts:
				if cast.hitbox != None:
					for shape in cast.hitbox.left_shapes + cast.hitbox.right_shapes:
						shape.cast = cast
						shape.power = power
						shape.attack = self

	def activate(self, side_facing: int):
		print("activating attack {} facing {}".format(self.name, side_facing))
		self.is_active = True
		self.cast_frame = 0
		self.power_idx = 0
		self.cast_idx = 0
		self.side_facing = side_facing
		self.cooldown_timer = 0
		self.recover_timer = 0
		self.has_hit = False
		for p in self.powers:
			p.is_active = False
			for c in p.casts:
				c.is_active = False
				c.has_hit = False

class StepAttackResults():
	def __init__(self, is_active: bool, velocity: tuple[float, float]|None, recover_frames: int):
		self.is_active = is_active
		self.velocity = velocity
		self.recover_frames = recover_frames

def step_attack(attack: Attack, space: pymunk.Space) -> StepAttackResults:
	if attack.is_active == False:
		attack.cooldown_timer = max(attack.cooldown_timer - 1, 0)
		return StepAttackResults(is_active=False, velocity=None, recover_frames=0)
	current_power = attack.powers[attack.power_idx]
	current_cast = current_power.casts[attack.cast_idx]
	
	if attack.recover_timer > 0:
		attack.recover_timer = max(attack.recover_timer - 1, 0)
		print("attack on recover")
		return StepAttackResults(is_active=True, velocity=None, recover_frames=0)
	
	attack.cast_frame += 1
	# the first active frame begins at the same frame as the last startup frame, which is why we subtract by 1, or 0 if no startup frames
	is_cast_finished = attack.cast_frame > (max(current_cast.startup_frames-1, 0) + current_cast.active_frames)
	if is_cast_finished:
		if current_cast.hitbox != None:
			if attack.side_facing == consts.FIGHTER_SIDE_FACING_LEFT:
				for shape in current_cast.hitbox.left_shapes:
					space.remove(shape)
			elif attack.side_facing == consts.FIGHTER_SIDE_FACING_RIGHT:
				for shape in current_cast.hitbox.right_shapes:
					space.remove(shape)

		attack.cast_idx += 1
		if attack.cast_idx >= len(current_power.casts):
			attack.cast_idx = 0
			attack.power_idx += 1
			current_power = None
			for (idx, power) in enumerate(attack.powers):
				if idx < attack.power_idx:
					continue
				if power.requires_hit and not attack.has_hit:
					continue
				current_power = power
				attack.power_idx = idx
				break
			if current_power == None:
				attack.power_idx = 0
				attack.is_active = False
				current_power = None
				current_cast = None
				return StepAttackResults(is_active=False, velocity=None, recover_frames=0)
		
		attack.cast_frame = 1
		current_power = attack.powers[attack.power_idx]
		current_cast = current_power.casts[attack.cast_idx]

	fighter_recover_frames=0
	if current_power.is_active == False:
		current_power.is_active = True
		attack.cooldown_timer += current_power.cooldown_frames
		total_recover_frames = current_power.recovery_frames + current_power.fixed_recovery_frames
		if attack.power_idx == len(attack.powers)-1:
			fighter_recover_frames = total_recover_frames
		else:
			attack.recover_timer = total_recover_frames

	if attack.cast_frame >= current_cast.startup_frames and current_cast.is_active == False:
		current_cast.is_active = True
		if current_cast.hitbox != None:
			if attack.side_facing == consts.FIGHTER_SIDE_FACING_LEFT:
				for shape in current_cast.hitbox.left_shapes:
					space.add(shape)
			elif attack.side_facing == consts.FIGHTER_SIDE_FACING_RIGHT:
				for shape in current_cast.hitbox.right_shapes:
					space.add(shape)
	
	attack_velocity = None
	if (current_cast.is_active or current_cast.is_active_velocity_all_frames) and current_cast.active_velocity != None:
		attack_velocity = current_cast.active_velocity
	return StepAttackResults(is_active=True, velocity=attack_velocity, recover_frames=fighter_recover_frames)
