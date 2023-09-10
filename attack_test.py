import unittest
from attack import *
import pymunk

# Assuming that consts.FIGHTER_SIDE_FACING_LEFT and consts.FIGHTER_SIDE_FACING_RIGHT are 0 and 1 respectively
DUMMY_SIDE_FACING = 0

class TestStepAttackFunction(unittest.TestCase):
	
	def setUp(self):
		self.space = pymunk.Space()

	def test_step_return_bool_count(self):
		tests = [
			{
				"name": "Test with 2 startup and 3 active frames",
				"attack": Attack(
					powers = [ Power(casts=[Cast(min_startup_frames=2, active_frames=3, hitbox=Hitbox(left_shapes=[], right_shapes=[]))])], 
					name="dummy_attack",
					is_attack_triggered_func=lambda is_fighter_grounded,input: True
					),
				"number_of_trues": 4  # expected number of times that function will return true
			},
			{
				"name": "Dummy sidelight",
				"attack": Attack([
					Power(
						casts = [
							Cast(min_startup_frames=2, active_frames=2, velocity=(50,0), is_velocity_on_active_frames_only=True), 
							Cast(min_startup_frames=3, active_frames=2, velocity=(100,10), is_velocity_on_active_frames_only=True),
							Cast(
								min_startup_frames=1, active_frames=4, velocity=(100,0), is_velocity_on_active_frames_only=False, base_dmg = 13, var_force=20, fixed_force=80,
								hitbox=Hitbox( [], [], ),
							)
						],
						cooldown_frames = 10, stun_frames = 18
					), 
					Power([Cast(min_startup_frames=0, active_frames=1, velocity=(100,0))], fixed_recovery_frames = 2, recovery_frames = 18) 
				], name="unarmed_side_light", is_attack_triggered_func=lambda is_fighter_grounded,input: True),
				"number_of_trues": 12
			},
			# Add more test cases as required
		]

		for test in tests:
			with self.subTest(test['name']):
				attack: Attack = test['attack']
				
				bool_return_count = 0
				attack.activate(side_facing=DUMMY_SIDE_FACING)

				for _ in range(1000):  
					attack_results: StepAttackResults = step_attack(attack=attack, space=self.space)
					if attack_results.is_active:
						bool_return_count += 1

				self.assertEqual(bool_return_count, test['number_of_trues'], f"unexpected number of times step() returned true: {bool_return_count}")

if __name__ == '__main__':
	unittest.main()
