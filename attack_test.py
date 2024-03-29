import unittest
from attack import *
import pymunk
import input

# Assuming that consts.FIGHTER_SIDE_FACING_LEFT and consts.FIGHTER_SIDE_FACING_RIGHT are 0 and 1 respectively
DUMMY_SIDE_FACING = 0

class TestAttack(unittest.TestCase):
	
	def setUp(self):
		self.space = pymunk.Space()

	def test_step_return_bool_count(self):
		test_case_3_input = input.Input()
		test_case_3_input.current[input.INPUT_LIGHT_HIT] = True
		tests = [
			{
				"name": "Test with 2 startup and 3 active frames",
				"attack": Attack(
						powers = [Power(casts=[Cast(startup_frames=2, active_frames=3, hitbox=Hitbox(left_shapes=[], right_shapes=[]))])], 
						name="dummy_attack", 
						requires_fighter_grounding=True, hit_input=AttackHitInput.LIGHT, move_type=AttackMoveType.DOWN),
				"input": input.Input(),
				"is_fighter_grounded": True,
				"number_of_steps": 1000,
				"expected_number_of_trues": 4  # expected number of times that function will return true
			},
			{
				"name": "Dummy sidelight",
				"attack": Attack(
					powers = [
						Power(
							casts = [
								Cast(startup_frames=2, active_frames=2, velocity=(50,0), is_velocity_on_active_frames_only=True), 
								Cast(startup_frames=3, active_frames=2, velocity=(100,10), is_velocity_on_active_frames_only=True),
								Cast(
									startup_frames=1, active_frames=4, velocity=(100,0), is_velocity_on_active_frames_only=False, base_dmg = 13, var_force=20, fixed_force=80,
									hitbox=Hitbox( [], [], ),
								)
							],
							cooldown_frames = 10, stun_frames = 18
						), 
						Power([Cast(startup_frames=0, active_frames=1, velocity=(100,0))], fixed_recovery_frames = 2, recovery_frames = 18) ,
					], 
					name="unarmed_side_light",
					requires_fighter_grounding=True,
					hit_input=AttackHitInput.LIGHT,
					move_type=AttackMoveType.SIDE,
				),
				"input": input.Input(),
				"is_fighter_grounded": True,
				"number_of_steps": 1000,
				"expected_number_of_trues": 12
			},
			{
				"name": "active forever",
				"attack": Attack(
						powers = [Power(casts=[
							Cast(
								startup_frames=2, active_frames=3, is_active_until_cancelled=True,
								hitbox=Hitbox(left_shapes=[], right_shapes=[])
							)
						])],
						name="dummy_attack", 
						requires_fighter_grounding=True, hit_input=AttackHitInput.LIGHT, move_type=AttackMoveType.DOWN),
				"input": test_case_3_input,
				"is_fighter_grounded": True,
				"number_of_steps": 1000,
				"expected_number_of_trues": 1000,
			},
			# Add more test cases as required
		]

		for test in tests:
			with self.subTest(test['name']):
				attack: Attack = test['attack']
				
				bool_return_count = 0
				fighter_input = test['input']

				is_fighter_grounded = test["is_fighter_grounded"]
				attack.activate(side_facing=DUMMY_SIDE_FACING)

				for _ in range(test['number_of_steps']):  
					attack_results: StepAttackResults = step_attack(attack=attack, space=self.space, fighter_input=fighter_input, is_fighter_grounded=is_fighter_grounded)
					if attack_results.is_active:
						bool_return_count += 1

				self.assertEqual(bool_return_count, test['expected_number_of_trues'], f"unexpected number of times step() returned true: {bool_return_count}")
	
	def test_is_attack_triggered(self):
		first_case_input = input.Input()
		first_case_input.current[input.INPUT_LIGHT_HIT] = True
		first_case_input.current[input.INPUT_MOVE_LEFT] = True
		second_case_input = input.Input()

		heavy_only_input = input.Input()
		heavy_only_input.current[input.INPUT_HEAVY_HIT] = True

		fourth_case_input = input.Input()
		fourth_case_input.current[input.INPUT_LIGHT_HIT] = True

		air_attack_with_jump_use = Attack(
						powers = [Power(casts=[Cast(startup_frames=0, active_frames=1, hitbox=Hitbox(left_shapes=[], right_shapes=[]))])], 
						name="dummy_attack", 
						requires_fighter_grounding=False, hit_input=AttackHitInput.HEAVY, move_type=AttackMoveType.NEUTRAL, is_jump_attack=True)
		air_attack_with_jump_use.has_jump_attack_use = True


		air_attack_without_jump_use = Attack(
						powers = [Power(casts=[Cast(startup_frames=0, active_frames=1, hitbox=Hitbox(left_shapes=[], right_shapes=[]))])], 
						name="dummy_attack", 
						requires_fighter_grounding=False, hit_input=AttackHitInput.HEAVY, move_type=AttackMoveType.NEUTRAL, is_jump_attack=True)
		air_attack_without_jump_use.has_jump_attack_use = False

		tests = [
			{
				"name": "side_light_met",
				"attack": Attack(
						powers = [Power(casts=[Cast(startup_frames=2, active_frames=3, hitbox=Hitbox(left_shapes=[], right_shapes=[]))])], 
						name="dummy_attack", 
						requires_fighter_grounding=True, hit_input=AttackHitInput.LIGHT, move_type=AttackMoveType.SIDE),
				"spare_fighter_jumps": 0,
				"is_fighter_grounded": True,
				"fighter_input": first_case_input,
				"want": AttackTriggerResults(can_activate=True, is_needing_fighter_jump=False)
			},
			{
				"name": "down_light_not_met",
				"attack": Attack(
						powers = [Power(casts=[Cast(startup_frames=2, active_frames=3, hitbox=Hitbox(left_shapes=[], right_shapes=[]))])], 
						name="dummy_attack", 
						requires_fighter_grounding=True, hit_input=AttackHitInput.LIGHT, move_type=AttackMoveType.DOWN),
				"spare_fighter_jumps": 0,
				"is_fighter_grounded": True,
				"fighter_input": second_case_input,
				"want": AttackTriggerResults(can_activate=False, is_needing_fighter_jump=False)
			},
			{
				"name": "neutral_heavy_met",
				"attack": Attack(
						powers = [Power(casts=[Cast(startup_frames=2, active_frames=3, hitbox=Hitbox(left_shapes=[], right_shapes=[]))])], 
						name="dummy_attack", 
						requires_fighter_grounding=True, hit_input=AttackHitInput.HEAVY, move_type=AttackMoveType.NEUTRAL),
				"spare_fighter_jumps": 0,
				"is_fighter_grounded": True,
				"fighter_input": heavy_only_input,
				"want": AttackTriggerResults(can_activate=True, is_needing_fighter_jump=False)
			},
			{
				"name": "side_light_not_met",
				"attack": Attack(
						powers = [Power(casts=[Cast(startup_frames=2, active_frames=3, hitbox=Hitbox(left_shapes=[], right_shapes=[]))])], 
						name="dummy_attack", 
						requires_fighter_grounding=True, hit_input=AttackHitInput.LIGHT, move_type=AttackMoveType.SIDE),
				"spare_fighter_jumps": 0,
				"is_fighter_grounded": True,
				"fighter_input": fourth_case_input,
				"want": AttackTriggerResults(can_activate=False, is_needing_fighter_jump=False)
			},
			{
				"name": "jump_not_met",
				"attack": air_attack_without_jump_use,
				"spare_fighter_jumps": 0,
				"is_fighter_grounded": False,
				"fighter_input": heavy_only_input,
				"want": AttackTriggerResults(can_activate=False, is_needing_fighter_jump=True),
			},
			{
				"name": "has_jump_use",
				"attack": air_attack_with_jump_use,
				"spare_fighter_jumps": 0,
				"is_fighter_grounded": False,
				"fighter_input": heavy_only_input,
				"want": AttackTriggerResults(can_activate=True, is_needing_fighter_jump=False),
			},
			{
				"name": "met_but_needs_fighter_jump",
				"attack": air_attack_without_jump_use,
				"spare_fighter_jumps": 1,
				"is_fighter_grounded": False,
				"fighter_input": heavy_only_input,
				"want": AttackTriggerResults(can_activate=True, is_needing_fighter_jump=True),
			},
		]
		for test in tests:
			with self.subTest(test['name']):
				attack: Attack = test['attack']
				fighter_input: input.Input = test['fighter_input']
				is_fighter_grounded: bool = test['is_fighter_grounded'] 
				spare_fighter_jumps: int = test['spare_fighter_jumps']
				want: bool = test['want']
				got = is_attack_triggered(attack, is_fighter_grounded, fighter_input, spare_fighter_jumps)
				self.assertEqual(want, got)

if __name__ == '__main__':
	unittest.main()
