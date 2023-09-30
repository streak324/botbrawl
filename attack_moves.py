import utils
import consts
import pymunk
from attack import *
from input import *

class CapsuleParams():
	def __init__(self, offset: tuple[float,float], dims: tuple[float,float]):
		self.offset = offset
		self.dims = dims

def create_hitbox_from_capsules(body, capsules_params: list[CapsuleParams]) -> Hitbox: 
	"""
		capsule_params should represent the arguments for hitbox shapes that are facing right. left facing hitboxes will be created from negating the  x (0 index) offset
	"""
	hitbox_filter = pymunk.ShapeFilter(
		categories=0b1 << (consts.HITBOX_COLLISION_TYPE-1), 
		mask=0b1 << (consts.HURTBOX_COLLISION_TYPE-1))

	left: list[pymunk.Shape] = []
	right: list[pymunk.Shape] = []
	for capsule_params in capsules_params:
		left_capsule = utils.add_capsule_shape(body, offset=(-capsule_params.offset[0], capsule_params.offset[1]), dims=capsule_params.dims)
		right_capsule = utils.add_capsule_shape(body, offset=capsule_params.offset, dims=capsule_params.dims)
		for s in left_capsule + right_capsule:
			s.collision_type = consts.HITBOX_COLLISION_TYPE	
			s.filter = hitbox_filter
			s.sensor = True
			s.color = (128, 0, 0, 255)

		left.extend(left_capsule)
		right.extend(right_capsule)
		
	return Hitbox(left, right)

def add_unarmed_moves(body: pymunk.Body) -> list[Attack]:
	attacks = []
	# order should be on priority
	attacks.append(Attack(
		powers=[
			Power(
				casts = [
					Cast(startup_frames=2, active_frames=2, velocity=(50,0), is_velocity_on_active_frames_only=True), 
					Cast(startup_frames=3, active_frames=2, velocity=(100,10), is_velocity_on_active_frames_only=True),
					Cast(
						startup_frames=1, active_frames=4, velocity=(100,0), is_velocity_on_active_frames_only=False, base_dmg = 13, var_force=20, fixed_force=80,
						hitbox=create_hitbox_from_capsules(body, [CapsuleParams(offset=(0.5*consts.HURTBOX_WIDTH,-1), dims=(consts.HURTBOX_WIDTH,5))]),
					)
				],
				cooldown_frames = 10, stun_frames = 18
			), 
			Power([Cast(startup_frames=0, active_frames=1, velocity=(100,0), is_velocity_on_active_frames_only=True)], fixed_recovery_frames = 2, recovery_frames = 18) 
		], 
		name="unarmed_side_light",
		requires_fighter_grounding=True,
		hit_input=AttackHitInput.LIGHT,
		move_type=AttackMoveType.SIDE,
	))

	attacks.append(Attack(
		powers =[
			Power(
				casts = [
					Cast(
						startup_frames=5, active_frames=3, velocity=(50,0), is_velocity_on_active_frames_only=True
					),
					Cast(
						startup_frames=0, active_frames=9, base_dmg=8, var_force=5, fixed_force=45, velocity=(100,0), is_velocity_on_active_frames_only=True, knockback_dir=(0.05,0.95),
						hitbox=create_hitbox_from_capsules(body, [CapsuleParams(offset=(8,-4), dims=(10,5))]),
					),
					Cast(
						startup_frames=0,active_frames=3, velocity=(50,0), is_velocity_on_active_frames_only=True
					),
				],
				cooldown_frames = 0, stun_frames = 31, cancel_power_on_hit=True,
			),
			Power(
				casts = [
					Cast(
						startup_frames=0, active_frames=4
					),
				],
				fixed_recovery_frames=1, recovery_frames=13, requires_no_hit=True
			),
			Power(
				casts = [
					Cast(
						startup_frames=0, active_frames=2
					),
				],
				fixed_recovery_frames=1, requires_hit=True,
			),
		], 
		name="unarmed_down_light",
		requires_fighter_grounding=True, 
		hit_input=AttackHitInput.LIGHT,
		move_type=AttackMoveType.DOWN,
	))

	attacks.append(Attack(
		powers=[
			Power(
				casts = [
					Cast(
						startup_frames = 5,	active_frames = 3, base_dmg=3, fixed_force=25,
						hitbox=create_hitbox_from_capsules(body, [CapsuleParams(offset=(6, 0), dims=(10,5))]),
					),
				],
				recovery_frames = 3, cooldown_frames = 16, stun_frames = 17
			),
			Power(
				casts = [
					Cast(
						startup_frames = 6, active_frames = 6, base_dmg=3, fixed_force=20,
						hitbox=create_hitbox_from_capsules(body, [CapsuleParams(offset=(4,0), dims=(4,4)), CapsuleParams(offset=(6,4), dims=(8,6))]),
					),
				],
				recovery_frames = 0, cooldown_frames = 0, stun_frames = 17
			),
			Power(
				casts = [
					Cast(
						startup_frames = 6, active_frames = 3, base_dmg = 3, fixed_force = 25,
						hitbox=create_hitbox_from_capsules(body, [CapsuleParams(offset=(4,0), dims=(5,10))]),
					),
				],
				recovery_frames = 3, stun_frames = 20, requires_hit = True
			),
			Power(
				casts = [
					Cast(startup_frames=3, active_frames = 1, velocity=(1,0), is_velocity_on_active_frames_only=True),
					Cast(startup_frames=3, active_frames = 1, velocity=(1,0), is_velocity_on_active_frames_only=False),
					Cast(startup_frames=3, active_frames = 1, velocity=(1,0), is_velocity_on_active_frames_only=False),
					Cast(
						startup_frames = 2, active_frames = 5, base_dmg=5, var_force=31, fixed_force=52,
						hitbox=create_hitbox_from_capsules(body, [CapsuleParams(offset=(6,0), dims=(10,5))]),
					),
				],
				recovery_frames = 22, stun_frames = 23, requires_hit = True
			),
			Power([Cast(startup_frames = 0, active_frames=1)], fixed_recovery_frames=2, recovery_frames=9), 
		],
		name="unarmed_neutral_light",
		requires_fighter_grounding=True, 
		hit_input=AttackHitInput.LIGHT,
		move_type=AttackMoveType.NEUTRAL,
	))

	attacks.append(Attack(
		powers=[
			Power(
				casts = [
					Cast(
						startup_frames=13, active_frames=3, base_dmg=13, var_force=40, fixed_force=45, velocity=(50, 0), is_velocity_on_active_frames_only=True,
						hitbox = create_hitbox_from_capsules(body, [
							CapsuleParams((8, -2), (6, 3)),
							CapsuleParams((10, -4), (4, 3))
						]),
					),
					Cast(
						startup_frames=0, active_frames=2, base_dmg=13, var_force=37, fixed_force=45, velocity=(50, 0), is_velocity_on_active_frames_only=True,
						hitbox = create_hitbox_from_capsules(body, [
							CapsuleParams((9, -2), (4, 3)),
							CapsuleParams((10, -4), (4, 3))
						]),
					),
					Cast(
						startup_frames=0, active_frames=2, base_dmg=13, var_force=36, fixed_force=45, velocity=(50, 0), is_velocity_on_active_frames_only=True,
						hitbox = create_hitbox_from_capsules(body, [
							CapsuleParams((12, -5), (2, 2))
						])
					)
				],
				cooldown_frames=14, stun_frames=17,
			),
			Power(
				casts = [ Cast(startup_frames=0, active_frames=1) ],
				fixed_recovery_frames=5, recovery_frames=17
			),
		],
		name="unarmed_aerial_side_light",
		requires_fighter_grounding=False, 
		hit_input=AttackHitInput.LIGHT,
		move_type=AttackMoveType.SIDE,
	))

	attacks.append(Attack(
		powers=[
			Power(
				casts = [
					Cast(startup_frames=4, active_frames=1),
					Cast(
						startup_frames=4, active_frames=16, base_dmg=16, var_force=5, fixed_force=65, velocity=(50,-10), is_velocity_on_active_frames_only=True, knockback_dir=(0.71,0.71),
						hitbox = create_hitbox_from_capsules(body, [
							CapsuleParams((5, -4), (2, 3)),
							CapsuleParams((6, -6), (3, 4))
						]),
					)
				],
				cooldown_frames=9, stun_frames=19
			),
			Power(
				casts = [
					Cast(startup_frames=4, active_frames=1),
				],
			),
		], 
		name="unarmed_aerial_down_light",
		requires_fighter_grounding=False, 
		hit_input=AttackHitInput.LIGHT,
		move_type=AttackMoveType.DOWN,
	))

	attacks.append(Attack(
		powers=[
			Power(
				casts = [
					Cast(
						startup_frames=7, active_frames=5, base_dmg=3, fixed_force=40, self_velocity_on_hit=(0, 0), knockback_dir=(0,1),
						hitbox=create_hitbox_from_capsules(body, [CapsuleParams(offset=(7,1), dims=(5,10))])
					),
				],
				cooldown_frames=7, stun_frames=17
			),
			Power(
				casts = [
					Cast(
						# fixed force is 40, according to brawlhalla.
						# however, unable to replicate the exact fixed force in brawlhalla, because somehow the knockback from this cast is lower than the previous cast in brawhalla, with the same force.
						startup_frames=8, active_frames=5, base_dmg=3, self_velocity_on_hit=(0, 0), knockback_dir=(0, 1), should_cancel_victim_velocity_on_hit_until_next_hit_in_attack = True,
						hitbox = create_hitbox_from_capsules(body, [
							CapsuleParams((7, -1), (4, 3)),
							CapsuleParams((9, 2), (8, 4))
						])

					),
				],
				recovery_frames=4, stun_frames=21
			),
			Power(
				casts = [
					Cast(
						startup_frames=8, active_frames=5, base_dmg=5, var_force=37, fixed_force=71, self_velocity_on_hit=(0,0),
						hitbox = create_hitbox_from_capsules(body, [
							CapsuleParams((4, 0), (10, 5))
						])

					),
				],
				recovery_frames=22, stun_frames=19, requires_hit=True,
			),
			Power(
				casts = [ Cast( startup_frames=0, active_frames=1) ],
				fixed_recovery_frames=1, recovery_frames=15, cooldown_frames=0,
			),
		], 
		name="unarmed_aerial_neutral_light",
		requires_fighter_grounding=False, 
		hit_input=AttackHitInput.LIGHT,
		move_type=AttackMoveType.NEUTRAL,
	))

	attacks.append(Attack(
		powers = [
			Power(
				casts = [
					Cast(startup_frames=0, active_frames=1),
					Cast(startup_frames=11, active_frames=1, additional_startup_frames=61, extra_dmg_per_extra_startup_frame=0.125),
				],
			),
			Power(
				casts = [
					Cast(
						startup_frames=7, active_frames=8, base_dmg=18, var_force=55, fixed_force=45, velocity=(100,0), is_velocity_on_active_frames_only=True, is_using_charged_dmg=True,
						hitbox = create_hitbox_from_capsules(body, [
							CapsuleParams((7, 4), (14, 5))
						]),
					),
					Cast(startup_frames=0, active_frames=9, velocity=(50,0), is_velocity_on_active_frames_only=True),
				],
				recovery_frames=18, stun_frames=18,
			),
		],
		name="unarmed_side_heavy",
		requires_fighter_grounding=True,
		hit_input=AttackHitInput.HEAVY,
		move_type=AttackMoveType.SIDE,
	))

	attacks.append(Attack(
		powers=[
			Power(
				casts = [
					Cast(startup_frames=0, active_frames=1),
					Cast(startup_frames=11, active_frames=1, additional_startup_frames=61, extra_dmg_per_extra_startup_frame=0.125),
				],
			),
			Power(
				casts = [
					Cast(
						startup_frames=7, active_frames=2, base_dmg=16, var_force=60, fixed_force=40, is_using_charged_dmg=True,
						hitbox = create_hitbox_from_capsules(body, [
							CapsuleParams((5, -7), (12, 5))
						]),
					),
					Cast(
						startup_frames=0, active_frames=5, base_dmg=16, var_force=60, fixed_force=40, is_using_charged_dmg=True,
						hitbox = create_hitbox_from_capsules(body, [
							CapsuleParams((3, -5.5), (8, 6)),
							CapsuleParams((6, -4.5), (6, 5))
						]),
					),
					Cast(
						startup_frames=9, active_frames=3, base_dmg=16, var_force=60, fixed_force=40, is_using_charged_dmg=True,
						hitbox = create_hitbox_from_capsules(body, [
							CapsuleParams((-2, -5.5), (14, 5)),
							CapsuleParams((-8, -4.5), (8, 6))
						]),
					),
					Cast(
						startup_frames=0, active_frames=2, base_dmg=16, var_force=60, fixed_force=40, is_using_charged_dmg=True,
						hitbox = create_hitbox_from_capsules(body, [
							CapsuleParams((-3, -5.5), (14, 5))
						]),
					),
				],
				recovery_frames=21, stun_frames=18,
			),
		],
		name="unarmed_down_heavy",
		requires_fighter_grounding=True,
		hit_input=AttackHitInput.HEAVY,
		move_type=AttackMoveType.DOWN,
	))

	attacks.append(Attack(
		powers=[
			Power(
				casts = [
					Cast(startup_frames=0, active_frames=1),
					Cast(startup_frames=10, active_frames=1, additional_startup_frames=62, extra_dmg_per_extra_startup_frame=0.125),
				],
			),
			Power(
				casts = [
					Cast(
						startup_frames=4, active_frames=6, base_dmg=20, var_force=46, fixed_force=40, is_using_charged_dmg=True,
						hitbox=create_hitbox_from_capsules(body, [
							CapsuleParams(offset=(7, 4), dims=(3, 10)),
							CapsuleParams(offset=(6, 6), dims=(3, 8)),
							CapsuleParams(offset=(5, 7.5), dims=(3.5, 6)),
						]),
					),
				],
				fixed_recovery_frames=4, recovery_frames=16,
			)
		],
		name="unarmed_neutral_heavy",
		requires_fighter_grounding=True,
		hit_input=AttackHitInput.HEAVY,
		move_type=AttackMoveType.NEUTRAL,
	))

	attacks.append(Attack(
		powers=[
			Power(
				casts=[
					Cast(
						startup_frames=15, active_frames=2, base_dmg=17, var_force=46, fixed_force=48,
					),
					Cast(
						startup_frames=0, active_frames=39, base_dmg=17, var_force=46, fixed_force=48, velocity=(0,-40), is_velocity_on_active_frames_only=True, knockback_dir=(0.1, 0.9),
						hitbox=create_hitbox_from_capsules(body, [
							CapsuleParams(offset=(-1, -8), dims=(3, 5)),
						]),
					),
					Cast(
						startup_frames=0, active_frames=1, base_dmg=17, var_force=46, fixed_force=48, velocity=(0,-40), is_active_until_cancelled=True, knockback_dir=(0.1, 0.9),
						hitbox=create_hitbox_from_capsules(body, [
							CapsuleParams(offset=(-1, -8), dims=(3, 5)),
						]),
					),
				],
				cooldown_frames=19, stun_frames=19, cancel_power_on_hit=True, cancel_power_on_ground=True,
			),
			Power(
				casts=[Cast(startup_frames=0, active_frames=1)],
				requires_no_hit=True, requires_no_grounding=True,
				recovery_frames=7, stun_frames=19,
			),
			Power(
				casts=[ Cast(startup_frames=3, active_frames=1, velocity=(10,0)) ],
				requires_hit=True,
			),
			Power(
				casts=[
					Cast(
						startup_frames=0, active_frames=2, base_dmg=17, var_force=46, fixed_force=48, knockback_dir=(0.1, 0.9),
						hitbox=create_hitbox_from_capsules(body, [
							CapsuleParams(offset=[0, -consts.HURTBOX_HEIGHT*0.5 + 3], dims=[8, 6]),
						]),
					),
					Cast(
						startup_frames=0, active_frames=7,
					),
				],
				requires_no_hit=True, requires_grounding=True,
				fixed_recovery_frames=1, recovery_frames=16, stun_frames=19,
			),
		],
		name="unarmed_aerial_down_heavy",
		requires_fighter_grounding=False,
		hit_input=AttackHitInput.HEAVY,
		move_type=AttackMoveType.DOWN,
	))

	attacks.append(Attack(
		powers=[
			Power(
				casts=[
					Cast(
						startup_frames=11, active_frames=3, base_dmg=15, var_force=40, fixed_force=55, velocity=(0,20), is_velocity_on_active_frames_only=True,
						hitbox=create_hitbox_from_capsules(body, [
							CapsuleParams(offset=(7, 4), dims=(3, 8)),
							CapsuleParams(offset=(6, 6), dims=(3, 8)),
							CapsuleParams(offset=(5, 7.5), dims=(2.5, 3)),
						]),
					),
					Cast(
						startup_frames=0, active_frames=3, base_dmg=15, var_force=40, fixed_force=55, velocity=(0,20), is_velocity_on_active_frames_only=True,
						hitbox=create_hitbox_from_capsules(body, [
							CapsuleParams(offset=(7, 4), dims=(3, 6)),
							CapsuleParams(offset=(6, 6), dims=(3, 6)),
							CapsuleParams(offset=(5, 7.5), dims=(2.5, 3)),
						]),
					),
					Cast(
						startup_frames=0, active_frames=3, base_dmg=15, var_force=40, fixed_force=55, velocity=(0,10), is_velocity_on_active_frames_only=True,
						hitbox=create_hitbox_from_capsules(body, [
							CapsuleParams(offset=(7, 4), dims=(3, 5)),
							CapsuleParams(offset=(6, 6), dims=(3, 5)),
							CapsuleParams(offset=(5, 7.5), dims=(2.5, 3)),
						]),
					),
				],
				cooldown_frames=12, stun_frames=25,
			),
		],
		name="unarmed_aerial_neutral_heavy",
		requires_fighter_grounding=False,
		hit_input=AttackHitInput.HEAVY,
		move_type=AttackMoveType.NEUTRAL,
	))

	return attacks