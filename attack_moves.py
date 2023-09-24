import utils
import consts
import pymunk
from attack import *
from input import *

def add_unarmed_moves(body: pymunk.Body) -> list[Attack]:
	hitbox_filter = pymunk.ShapeFilter(
		categories=0b1 << (consts.HITBOX_COLLISION_TYPE-1), 
		mask=0b1 << (consts.HURTBOX_COLLISION_TYPE-1))

	left_side_light_hitbox_shapes = utils.add_capsule_shape(body, (-0.5*consts.HURTBOX_WIDTH,-1),consts.HURTBOX_WIDTH,5)
	right_side_light_hitbox_shapes = utils.add_capsule_shape(body, (0.5*consts.HURTBOX_WIDTH,-1),consts.HURTBOX_WIDTH,5)

	left_neutral_light_hitbox_shapes_1 = utils.add_capsule_shape(body, (-6, 0), 10, 5)
	right_neutral_light_hitbox_shapes_1 = utils.add_capsule_shape(body, (6, 0), 10, 5)

	left_neutral_light_hitbox_shapes_2 = utils.add_capsule_shape(body, (-4, 0), 4, 4) + utils.add_capsule_shape(body, (-6, 4), 8, 6)
	right_neutral_light_hitbox_shapes_2 = utils.add_capsule_shape(body, (4, 0), 4, 4) + utils.add_capsule_shape(body, (6, 4), 8, 6)

	left_neutral_light_hitbox_shapes_3 = utils.add_capsule_shape(body, (-4, 0), 5, 10)
	right_neutral_light_hitbox_shapes_3 = utils.add_capsule_shape(body, (4, 0), 5, 10)

	left_neutral_light_hitbox_shapes_4 = utils.add_capsule_shape(body, (-6, 0), 10, 5)
	right_neutral_light_hitbox_shapes_4 = utils.add_capsule_shape(body, (6, 0), 10, 5)

	left_down_light_hitbox_shapes = utils.add_capsule_shape(body, (-8, -4), 10, 5)
	right_down_light_hitbox_shapes = utils.add_capsule_shape(body, (8, -4), 10, 5)
	
	left_aerial_neutral_light_hitbox_shapes_1 = utils.add_capsule_shape(body, (-7, 1), 5, 10)
	right_aerial_neutral_light_hitbox_shapes_1 = utils.add_capsule_shape(body, (7, 1), 5, 10)

	left_aerial_neutral_light_hitbox_shapes_2 = utils.add_capsule_shape(body, (-7, -1), 4, 3) + utils.add_capsule_shape(body, (-9, 2), 8, 4)
	right_aerial_neutral_light_hitbox_shapes_2 = utils.add_capsule_shape(body, (7, -1), 4, 3) + utils.add_capsule_shape(body, (9, 2), 8, 4)

	left_aerial_neutral_light_hitbox_shapes_3 = utils.add_capsule_shape(body, (-4, 0), 10, 5)
	right_aerial_neutral_light_hitbox_shapes_3 = utils.add_capsule_shape(body, (4, 0), 10, 5)

	left_aerial_side_light_hitbox_shapes_1 = utils.add_capsule_shape(body, (-8, -2), 6, 3) + utils.add_capsule_shape(body, (-10, -4), 4, 3)
	right_aerial_side_light_hitbox_shapes_1 = utils.add_capsule_shape(body, (8, -2), 6, 3) + utils.add_capsule_shape(body, (10, -4), 4, 3)

	left_aerial_side_light_hitbox_shapes_2 = utils.add_capsule_shape(body, (-9, -2), 4, 3) + utils.add_capsule_shape(body, (-10, -4), 4, 3)
	right_aerial_side_light_hitbox_shapes_2 = utils.add_capsule_shape(body, (9, -2), 4, 3) + utils.add_capsule_shape(body, (10, -4), 4, 3)

	left_aerial_side_light_hitbox_shapes_3 = utils.add_capsule_shape(body, (-12, -5), 2, 2)
	right_aerial_side_light_hitbox_shapes_3 = utils.add_capsule_shape(body, (12, -5), 2, 2)

	left_aerial_down_light_hitbox_shapes = utils.add_capsule_shape(body, (-5, -4), 2, 3) + utils.add_capsule_shape(body, (-6, -6), 3, 4)
	right_aerial_down_light_hitbox_shapes = utils.add_capsule_shape(body, (5, -4), 2, 3) + utils.add_capsule_shape(body, (6, -6), 3, 4)

	#NOTE: add all hitboxes into this loop
	for shape in (left_side_light_hitbox_shapes + right_side_light_hitbox_shapes 
		+ left_neutral_light_hitbox_shapes_1 + right_neutral_light_hitbox_shapes_1 
		+ left_neutral_light_hitbox_shapes_2 + right_neutral_light_hitbox_shapes_2
		+ left_neutral_light_hitbox_shapes_3 + right_neutral_light_hitbox_shapes_3 
		+ left_neutral_light_hitbox_shapes_4 + right_neutral_light_hitbox_shapes_4 
		+ left_down_light_hitbox_shapes + right_down_light_hitbox_shapes
		+ left_aerial_neutral_light_hitbox_shapes_1 + right_aerial_neutral_light_hitbox_shapes_1
		+ left_aerial_neutral_light_hitbox_shapes_2 + right_aerial_neutral_light_hitbox_shapes_2
		+ left_aerial_neutral_light_hitbox_shapes_3 + right_aerial_neutral_light_hitbox_shapes_3
		+ left_aerial_side_light_hitbox_shapes_1 + right_aerial_side_light_hitbox_shapes_1
		+ left_aerial_side_light_hitbox_shapes_2 + right_aerial_side_light_hitbox_shapes_2
		+ left_aerial_side_light_hitbox_shapes_3 + right_aerial_side_light_hitbox_shapes_3
		+ left_aerial_down_light_hitbox_shapes + right_aerial_down_light_hitbox_shapes
		):
		shape.collision_type = consts.HITBOX_COLLISION_TYPE	
		shape.filter = hitbox_filter
		shape.sensor = True
		shape.color = (128, 0, 0, 255)

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
						hitbox=Hitbox( left_side_light_hitbox_shapes, right_side_light_hitbox_shapes, ),
					)
				],
				cooldown_frames = 10, stun_frames = 18
			), 
			Power([Cast(startup_frames=0, active_frames=1, velocity=(100,0), is_velocity_on_active_frames_only=True)], fixed_recovery_frames = 2, recovery_frames = 18) 
		], 
		name="unarmed_side_light",
		requires_fighter_grounding=True,
		hit_input=AttackHitInput.LIGHT,
		move_input=AttackMoveInput.SIDE,
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
						hitbox=Hitbox(left_down_light_hitbox_shapes, right_down_light_hitbox_shapes)
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
		move_input=AttackMoveInput.DOWN,
	))

	attacks.append(Attack(
		powers=[
			Power(
				casts = [
					Cast(
						startup_frames = 5,	active_frames = 3, base_dmg=3, fixed_force=25,
						hitbox=Hitbox(left_neutral_light_hitbox_shapes_1, right_neutral_light_hitbox_shapes_1),
					),
				],
				recovery_frames = 3, cooldown_frames = 16, stun_frames = 17
			),
			Power(
				casts = [
					Cast(
						startup_frames = 6, active_frames = 6, base_dmg=3, fixed_force=20,
						hitbox=Hitbox(left_neutral_light_hitbox_shapes_2, right_neutral_light_hitbox_shapes_2),
					),
				],
				recovery_frames = 0, cooldown_frames = 0, stun_frames = 17
			),
			Power(
				casts = [
					Cast(
						startup_frames = 6, active_frames = 3, base_dmg = 3, fixed_force = 25,
						hitbox=Hitbox(left_neutral_light_hitbox_shapes_3, right_neutral_light_hitbox_shapes_3),
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
						hitbox=Hitbox(left_neutral_light_hitbox_shapes_4, right_neutral_light_hitbox_shapes_4)
					),
				],
				recovery_frames = 22, stun_frames = 23, requires_hit = True
			),
			Power([Cast(startup_frames = 0, active_frames=1)], fixed_recovery_frames=2, recovery_frames=9), 
		],
		name="unarmed_neutral_light",
		requires_fighter_grounding=True, 
		hit_input=AttackHitInput.LIGHT,
		move_input=AttackMoveInput.NEUTRAL,
	))

	attacks.append(Attack(
		powers=[
			Power(
				casts = [
					Cast(
						startup_frames=13, active_frames=3, base_dmg=13, var_force=40, fixed_force=45, velocity=(50, 0), is_velocity_on_active_frames_only=True,
						hitbox=Hitbox(left_aerial_side_light_hitbox_shapes_1, right_aerial_side_light_hitbox_shapes_1),
					),
					Cast(
						startup_frames=0, active_frames=2, base_dmg=13, var_force=37, fixed_force=45, velocity=(50, 0), is_velocity_on_active_frames_only=True,
						hitbox=Hitbox(left_aerial_side_light_hitbox_shapes_2, right_aerial_side_light_hitbox_shapes_2),
					),
					Cast(
						startup_frames=0, active_frames=2, base_dmg=13, var_force=36, fixed_force=45, velocity=(50, 0), is_velocity_on_active_frames_only=True,
						hitbox=Hitbox(left_aerial_side_light_hitbox_shapes_3, right_aerial_side_light_hitbox_shapes_3),
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
		move_input=AttackMoveInput.SIDE,
	))

	attacks.append(Attack(
		powers=[
			Power(
				casts = [
					Cast(startup_frames=4, active_frames=1),
					Cast(
						startup_frames=4, active_frames=16, base_dmg=16, var_force=5, fixed_force=65, velocity=(50,-10), is_velocity_on_active_frames_only=True, knockback_dir=(0.71,0.71),
						hitbox=Hitbox(left_aerial_down_light_hitbox_shapes, right_aerial_down_light_hitbox_shapes),
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
		move_input=AttackMoveInput.DOWN,
	))

	attacks.append(Attack(
		powers=[
			Power(
				casts = [
					Cast(
						startup_frames=7, active_frames=5, base_dmg=3, fixed_force=40, self_velocity_on_hit=(0, 0), knockback_dir=(0,1),
						hitbox=Hitbox(left_aerial_neutral_light_hitbox_shapes_1, right_aerial_neutral_light_hitbox_shapes_1),
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
						hitbox=Hitbox(left_aerial_neutral_light_hitbox_shapes_2, right_aerial_neutral_light_hitbox_shapes_2),
					),
				],
				recovery_frames=4, stun_frames=21
			),
			Power(
				casts = [
					Cast(
						startup_frames=8, active_frames=5, base_dmg=5, var_force=37, fixed_force=71, self_velocity_on_hit=(0,0),
						hitbox=Hitbox(left_aerial_neutral_light_hitbox_shapes_3, right_aerial_neutral_light_hitbox_shapes_3)
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
		move_input=AttackMoveInput.NEUTRAL,
	))

	return attacks