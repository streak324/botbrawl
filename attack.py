import pymunk
import consts
from typing import Callable
import input
from enum import Enum

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
			self, startup_frames: int, active_frames: int, base_dmg: float = 0, var_force: int = 0, fixed_force: int = 0, hitbox: Hitbox|None = None, 
		  	velocity: tuple[float, float]|None = None, is_velocity_on_active_frames_only: bool = False, knockback_dir: tuple[float,float] = (1,0), 
			self_velocity_on_hit: tuple[float,float]|None = None, should_cancel_victim_velocity_on_hit_until_next_hit_in_attack: bool = False,
			additional_startup_frames: int = 0, extra_dmg_per_extra_startup_frame: float = 0, is_using_charged_dmg: bool = False, is_active_until_cancelled=False,
		):
		"""

		### Parameters:
			additional_startup_frames : if greater than zero, than this cast is considered a charged cast. while the attack trigger is still holding
			extra_dmg_per_extra_startup_frame : how much damage is added to the cast for every additional startup frame
		"""
		self.startup_frames = startup_frames
		self.active_frames = active_frames
		self.base_dmg = base_dmg
		self.var_force = var_force
		self.fixed_force = fixed_force
		self.hitbox = hitbox
		# start velocity should be negated when attack is facing left
		self.velocity = velocity
		self.is_velocity_on_active_frames_only = is_velocity_on_active_frames_only
		# direction of force applied on hit.
		self.knockback_dir = knockback_dir
		# how much velocity needs to be applied to the fighter when hit lands. gravity is also cancelled if not none.
		self.self_velocity_on_hit = self_velocity_on_hit
		self.should_cancel_victim_velocity_on_hit_until_next_hit_in_attack = should_cancel_victim_velocity_on_hit_until_next_hit_in_attack
		self.additional_startup_frames = additional_startup_frames
		self.extra_dmg_per_extra_startup_frame = extra_dmg_per_extra_startup_frame
		self.is_using_charged_dmg = is_using_charged_dmg
		self.is_active_until_cancelled = is_active_until_cancelled


		# mutable values
		self.is_active = False
		self.has_hit = False
		self.charged_frames = 0
		self.is_cancelled = False

class Power():
	def __init__(
			self, casts: list[Cast], cooldown_frames: int = 0, fixed_recovery_frames: int = 0, recovery_frames: int = 0, min_charge_frames: int = 0, stun_frames = 0, 
			requires_hit: bool = False, requires_no_hit: bool = False, cancel_power_on_hit: bool = False, cancel_power_on_ground: bool = False, 
			requires_grounding: bool = False, requires_no_grounding: bool = False,
		):
		self.casts = casts
		self.cooldown_frames = cooldown_frames
		self.fixed_recovery_frames = fixed_recovery_frames
		self.recovery_frames = recovery_frames
		self.min_charge_frames = min_charge_frames
		self.stun_frames = stun_frames
		self.requires_hit = requires_hit
		self.requires_no_hit = requires_no_hit
		self.cancel_power_on_hit = cancel_power_on_hit
		self.cancel_power_on_ground = cancel_power_on_ground
		self.requires_grounding = requires_grounding
		self.requires_no_grounding = requires_no_grounding

		#mutable values
		self.is_active = False
		self.has_hit = False

# the value of the enum is equal to the attack type's input value
class AttackHitInput(Enum):
	LIGHT=input.INPUT_LIGHT_HIT
	HEAVY=input.INPUT_HEAVY_HIT

class AttackMoveType(Enum):
	NEUTRAL=1
	SIDE=2
	DOWN=3

class Attack():
	def __init__(self, powers: list[Power], name: str, requires_fighter_grounding: bool, hit_input: AttackHitInput, move_type: AttackMoveType):
		""" 
			### Arguments
				requires_fighter_grounding : whether the attack needs the fighter to be grounded or in the air for the attack to be activated
				hit_input : light hit or heavy hit
				move_type : does attack require side, down, or neutral (none) input to be pressed
		"""
		self.powers = powers
		self.name = name
		self.requires_fighter_grounding = requires_fighter_grounding
		self.hit_input = hit_input
		self.move_type = move_type

		# mutable values down below
		
		self.side_facing = 0
		self.is_victim_velocity_cancelled_until_next_hit = False
		# cooldown timer should not start ticking down until all powers have been looped. an attack should not be activated while cooldown timer is greater than zero
		self.cooldown_timer = 0
		# recover timer should only be used between powers, where the previous power has recovery frames. if the last power has recovery frames, it should be applied to the fighter's recover timer
		self.recover_timer = 0
		self.has_hit = False
		self.is_active = False
		self.cast_frame = 0
		self.power_idx = 0
		self.cast_idx = 0
		# whether the attack can be charging. this is only true if the attack's hit input has been pressed since the start of the attack
		self.can_do_charging = False
		# the extra damage gained from charged cast
		self.charged_dmg = 0

		# this can be true if there is an active Cast that can be cancelled.
		self.is_attack_cancelled=False
		 
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
		self.is_victim_velocity_cancelled_until_next_hit = False
		self.charged_dmg = 0
		for p in self.powers:
			p.is_active = False
			p.has_hit = False
			for c in p.casts:
				c.is_active = False
				c.has_hit = False
				c.charged_frames = 0
				c.is_cancelled = False
		current_power = self.powers[self.power_idx]
		current_cast = current_power.casts[self.cast_idx]
		self.can_do_charging = current_cast.additional_startup_frames > 0

def is_attack_triggered(attack: Attack, is_fighter_grounded: bool, fighter_input: input.Input) -> bool:
	"""
		for an attack to be triggered, the fighter's grounding must be satisified, and the attack's hit and move input must be tapped
	"""
	is_side = attack.move_type == AttackMoveType.SIDE and ( fighter_input.is_pressed(input.INPUT_MOVE_LEFT) or fighter_input.is_pressed(input.INPUT_MOVE_RIGHT))
	is_down = attack.move_type == AttackMoveType.DOWN and fighter_input.is_pressed(input.INPUT_MOVE_DOWN)
	is_neutral = attack.move_type == AttackMoveType.NEUTRAL
	is_move_met = is_side or is_down or is_neutral
	return is_move_met and fighter_input.is_tapped(attack.hit_input.value) and attack.requires_fighter_grounding == is_fighter_grounded

class StepAttackResults():
	def __init__(self, is_active: bool, velocity: tuple[float, float]|None, recover_frames: int):
		self.is_active = is_active
		self.velocity = velocity
		self.recover_frames = recover_frames

def step_attack(attack: Attack, space: pymunk.Space, fighter_input: input.Input, is_fighter_grounded: bool) -> StepAttackResults:
	if attack.is_active == False:
		attack.cooldown_timer = max(attack.cooldown_timer - 1, 0)
		return StepAttackResults(is_active=False, velocity=None, recover_frames=0)
	current_power = attack.powers[attack.power_idx]
	current_cast = current_power.casts[attack.cast_idx]
	
	if attack.recover_timer > 0:
		attack.recover_timer = max(attack.recover_timer - 1, 0)
		return StepAttackResults(is_active=True, velocity=None, recover_frames=0)

	attack.cast_frame += 1

	is_hit_input_pressed =  fighter_input.is_pressed(attack.hit_input.value)
	has_extra_startup_frames = current_cast.additional_startup_frames > 0
	is_past_startup = attack.cast_frame > current_cast.startup_frames
	can_do_more_charging =  attack.cast_frame < current_cast.startup_frames + current_cast.additional_startup_frames
	attack.can_do_charging = is_hit_input_pressed and has_extra_startup_frames and can_do_more_charging
	is_charging = attack.can_do_charging and is_past_startup

	if is_charging:
		attack.charged_dmg += current_cast.extra_dmg_per_extra_startup_frame
		current_cast.charged_frames += 1
		return StepAttackResults(is_active=True, velocity=None, recover_frames=0)

	is_power_cancelled_early = (current_power.cancel_power_on_hit and attack.has_hit) or (current_power.cancel_power_on_ground and is_fighter_grounded)
	is_cast_running_forever = current_cast.is_active_until_cancelled and fighter_input.is_pressed(attack.hit_input.value)

	# the first active frame begins at the same frame as the last startup frame, which is why we subtract by 1, or 0 if no startup frames. any cast frames that were spent on charging aren't counted.
	is_cast_out_of_frames = attack.cast_frame - current_cast.charged_frames > max(current_cast.startup_frames-1, 0) + current_cast.active_frames

	is_cast_finished = is_power_cancelled_early or (is_cast_out_of_frames and not is_cast_running_forever)
	if is_cast_finished:
		if current_cast.hitbox != None:
			if attack.side_facing == consts.FIGHTER_SIDE_FACING_LEFT:
				for shape in current_cast.hitbox.left_shapes:
					space.remove(shape)
			elif attack.side_facing == consts.FIGHTER_SIDE_FACING_RIGHT:
				for shape in current_cast.hitbox.right_shapes:
					space.remove(shape)

		attack.cast_idx += 1
		if is_power_cancelled_early or attack.cast_idx >= len(current_power.casts):
			attack.cast_idx = 0
			attack.power_idx += 1
			current_power = None
			for (idx, power) in enumerate(attack.powers):
				if idx < attack.power_idx:
					continue
				if power.requires_hit and not attack.has_hit:
					continue
				if power.requires_no_hit and attack.has_hit:
					continue
				if power.requires_grounding and not is_fighter_grounded:
					continue
				if power.requires_no_grounding and is_fighter_grounded:
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
		attack.can_do_charging = current_cast.additional_startup_frames > 0

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
	if (current_cast.is_active or not current_cast.is_velocity_on_active_frames_only) and current_cast.velocity != None:
		attack_velocity = current_cast.velocity
	return StepAttackResults(is_active=True, velocity=attack_velocity, recover_frames=fighter_recover_frames)
