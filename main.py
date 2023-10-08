import math
import numpy
import pymunk
import pyglet
import utils
from pymunk import pyglet_util
from pymunk.vec2d import Vec2d
from attack import *
import attack_moves
import input

import consts

# brawlhalla notes
# 2560x1440p
# sprites are 176px image
# hitbox is a capsule. dimensions are  144 width, 160 px height. 145px diameter
# hitbox above ~8-10px above sprite's feet
# unable to reproduce exact attacks, hitboxes, hurtboxes, and knockbacks in brawlhalla.

TOTAL_MIDAIR_JUMPS_ALLOWED = 2

JUMP_HEIGHT = 15

#not sure how im going to do this one yet.
PIXELS_PER_WORLD_UNITS = 8

FIGHTER_COLLIDER_WIDTH = 8
FIGHTER_COLLIDER_HEIGHT = 15

HURTBOX_COLOR = (78, 0, 129, 255)
HURTBOX_DODGE_COLOR = (154, 0, 255, 255)

FRAMES_PER_SECOND = 60
TIMESTEP = 1/FRAMES_PER_SECOND

FALL_VELOCITY = 80.0

DEVICE_CONTROLLED_FIGHTER_INDEX = 0


wall_collision_filter = pymunk.ShapeFilter( \
	categories=0b1 << (consts.WALL_COLLISION_TYPE-1), \
	mask=0b1 << (consts.FIGHTER_WALL_COLLIDER_COLLISION_TYPE-1))

def cancel_fighter_gravity_if_allowed(body: pymunk.Body, gravity: pymunk.Vec2d, damping: float, dt: float):
	if body.is_gravity_cancelled_until_attacker_done or body.is_gravity_cancelled_due_to_attacking:
		pymunk.Body.update_velocity(body, (0,0), damping, dt)
	else:
		pymunk.Body.update_velocity(body, gravity, damping, dt)
	
class Fighter():
	def __init__(self, space: pymunk.Space, center: tuple[float, float], side_facing = consts.FIGHTER_SIDE_FACING_LEFT):
		#hurtbox body is supposed to be the shape of a capsule: 2 circles and 1 rectangle
		self.side_facing = side_facing
		self.input = input.Input()
		self.body = pymunk.Body(mass=5, moment=float("inf"))
		self.body._set_position(center)
		space.add(self.body)
		space.damping = 0.9
		self.attacks: list[Attack] = []
		self.last_cast_id_hit: int = None
		self.dmg_points = 0.0
		self.body.is_gravity_cancelled_due_to_attacking = False
		self.body.is_gravity_cancelled_until_attacker_done = False
		self.body._set_velocity_func(cancel_fighter_gravity_if_allowed)

		hurtbox_filter = pymunk.ShapeFilter(
			categories=0b1 << (consts.HURTBOX_COLLISION_TYPE-1),
			mask=0b1 << (consts.HITBOX_COLLISION_TYPE-1))

		wall_collider_filter = pymunk.ShapeFilter(
			categories=0b1 << (consts.FIGHTER_WALL_COLLIDER_COLLISION_TYPE-1),
			mask=0b1 << (consts.WALL_COLLISION_TYPE-1))

		hurtbox_shapes = utils.add_capsule_shape(self.body, (0,0), (consts.HURTBOX_WIDTH, consts.HURTBOX_HEIGHT))
		for shape in hurtbox_shapes:
			shape.collision_type = consts.HURTBOX_COLLISION_TYPE 
			shape.color = HURTBOX_COLOR
			shape.filter = hurtbox_filter
			shape.sensor = True
			shape.fighter = self
			space.add(shape)

		self.hurtbox_shapes = hurtbox_shapes

		self.wall_collider = utils.create_pymunk_box(self.body,
			(-FIGHTER_COLLIDER_WIDTH*0.5, -FIGHTER_COLLIDER_HEIGHT*0.5-1), 
			(FIGHTER_COLLIDER_WIDTH*0.5, FIGHTER_COLLIDER_HEIGHT*0.5-1)
		)
		self.wall_collider.collision_type = consts.FIGHTER_WALL_COLLIDER_COLLISION_TYPE
		self.wall_collider.filter = wall_collider_filter
		self.wall_collider.friction = 1
		self.wall_collider.color = (255, 233, 28, 100)

		space.add(self.wall_collider)

		#NOTE: add all attacks in here
		self.attacks += attack_moves.add_unarmed_moves(self.body)

		self.midair_jumps_left = 0
		self.is_grounded = False

		#number of frames fighter must wait before attempting a new action (dodge, move, hit).
		self.recover_timer = 0
		#whether the player is currently getting hit by an action
		self.is_hit = False

		self.is_dodging = False
		self.dodge_timer = 0
		self.gravity_cancel_timer = 0
		self.dodge_cooldown_timer = 0

	def compute_grounding(self):
		grounding = {
			"normal": Vec2d.zero(),
			"penetration": Vec2d.zero(),
			"impulse": Vec2d.zero(),
			"position": Vec2d.zero(),
			"body": None,
		}
		# find out if player is standing on ground

		def f(arbiter: pymunk.Arbiter):
			n = -arbiter.contact_point_set.normal
			if n.y > grounding["normal"].y:
				grounding["normal"] = n
				grounding["penetration"] = -arbiter.contact_point_set.points[0].distance
				grounding["body"] = arbiter.shapes[1].body
				grounding["impulse"] = arbiter.total_impulse
				grounding["position"] = arbiter.contact_point_set.points[0].point_b

		self.body.each_arbiter(f)
		self.is_grounded = False
		if grounding["body"] != None:# and abs(grounding["normal"].x / grounding["normal"].y) < feet.friction:
			self.is_grounded = True
			self.midair_jumps_left = TOTAL_MIDAIR_JUMPS_ALLOWED

# function callback to used when a fighter hurtbox overlaps with hitbox. do stuff like knocking back fighter and applying damage points
def pre_solve_hurtbox_hitbox(arbiter: pymunk.Arbiter, space: pymunk.Space, data) -> bool:
	victim: Fighter = arbiter.shapes[0].fighter
	victim_body: pymunk.Body = arbiter.shapes[0].body
	attacker_body: pymunk.Body = arbiter.shapes[1].body
	if victim.is_hit == False:
		victim.is_hit = True
		cast: Cast = arbiter.shapes[1].cast
		power: Power = arbiter.shapes[1].power
		attack: Attack = arbiter.shapes[1].attack
		attack.has_hit = True
		victim.recover_timer = power.stun_frames
		if not power.has_hit:
			power.has_hit = True
			cast.has_hit = True
			victim.dmg_points += cast.base_dmg
			if cast.is_using_charged_dmg:
				victim.dmg_points += attack.charged_dmg 
				attack.charged_dmg = 0
			print("victim has {} damage points".format(victim.dmg_points))

			attacker_applied_velocity = cast.self_velocity_on_hit
			if cast.should_cancel_victim_velocity_on_hit_until_next_hit_in_attack:
				victim_body.is_gravity_cancelled_until_attacker_done = True
				attack.is_victim_velocity_cancelled_until_next_hit = True
				impulse = (-victim_body.mass * victim_body.velocity[0], -victim_body.mass * victim_body.velocity[1])
				victim_body.apply_impulse_at_local_point(impulse)
			elif attack.is_victim_velocity_cancelled_until_next_hit:
				victim_body.is_gravity_cancelled_until_attacker_done = False
				attack.is_victim_velocity_cancelled_until_next_hit = False

			if attacker_applied_velocity != None:
				attacker_body.is_gravity_cancelled_due_to_attacking = True
				if attack.side_facing == consts.FIGHTER_SIDE_FACING_LEFT:
					attacker_applied_velocity = -attacker_applied_velocity[0], attacker_applied_velocity[1]
				applied_vel_y = attacker_applied_velocity[1] - attacker_body.velocity.y
				impulse = (attacker_body.mass * attacker_applied_velocity[0], attacker_body.mass * applied_vel_y)
				attacker_body.apply_impulse_at_local_point(impulse)

			knockback_dir = cast.knockback_dir
			if arbiter.shapes[1].side_facing == consts.FIGHTER_SIDE_FACING_LEFT:
				knockback_dir = -knockback_dir[0], knockback_dir[1]
			fixed_impulse_scale = 5
			var_impulse_scale = 0.1
			knockback_scale = (fixed_impulse_scale * cast.fixed_force + victim.dmg_points * cast.var_force * var_impulse_scale)
			impulse = knockback_scale*knockback_dir[0], knockback_scale*knockback_dir[1]
			victim.body.apply_impulse_at_local_point(impulse)
	
	return True

class GameState():
	def __init__(self):
		self.physics_sim = pymunk.Space()
		self.physics_sim._set_gravity((0,-300))
		self.fighters = [Fighter(self.physics_sim, (30,100)), Fighter(self.physics_sim, (70, 100))]

		wall_body = pymunk.Body(body_type=pymunk.Body.STATIC)
		p1 = utils.create_pymunk_box(wall_body, (10, 10), (140,30))
		p1.collision_type = consts.WALL_COLLISION_TYPE
		p1.filter = wall_collision_filter
		p1.friction = 1
		p2 = utils.create_pymunk_box(wall_body, (10, 10), (20,100))
		p2.collision_type = consts.WALL_COLLISION_TYPE
		p2.filter = wall_collision_filter
		#p2.friction = 1
		p3 = utils.create_pymunk_box(wall_body, (130, 30), (140,100))
		p3.collision_type = consts.WALL_COLLISION_TYPE
		p3.filter = wall_collision_filter
		#p3.friction = 1
		self.physics_sim.add(wall_body, p1, p2, p3)

		hurtbox_hitbox_handler = self.physics_sim.add_collision_handler(consts.HURTBOX_COLLISION_TYPE, consts.HITBOX_COLLISION_TYPE)
		hurtbox_hitbox_handler.pre_solve = pre_solve_hurtbox_hitbox

		self.gravity_enabled = True

game_state = GameState()

def step_game(_):
	for fighter in game_state.fighters:
		dx = 0

		attack_results: StepAttackResults
		is_doing_action = False
		if fighter.recover_timer == 0:
			for attack in fighter.attacks:
				attack_results = step_attack(attack, game_state.physics_sim, fighter.input, fighter.is_grounded)
				if attack_results.is_active and not is_doing_action:
					is_doing_action = True
					break

		# on input, move fighter to right
		if is_doing_action == False and fighter.recover_timer == 0 and (fighter.side_facing != consts.FIGHTER_SIDE_FACING_LEFT or fighter.input.is_pressed(input.INPUT_MOVE_LEFT) == False) and fighter.input.is_pressed(input.INPUT_MOVE_RIGHT):
			fighter.side_facing = consts.FIGHTER_SIDE_FACING_RIGHT
			dx = 50
		
		#on input, move fighter to the left
		if is_doing_action == False and fighter.recover_timer == 0 and (fighter.side_facing != consts.FIGHTER_SIDE_FACING_RIGHT or fighter.input.is_pressed(input.INPUT_MOVE_RIGHT) == False) and fighter.input.is_pressed(input.INPUT_MOVE_LEFT):
			fighter.side_facing = consts.FIGHTER_SIDE_FACING_LEFT
			dx = -50

		fighter.compute_grounding()
		if (fighter.input.is_tapped(input.INPUT_JUMP) and
			(fighter.is_grounded or fighter.midair_jumps_left > 0)
			):
			print("JUMPING")
			#only subtract midair jumps if fighter is not grounded
			fighter.midair_jumps_left -= int(not fighter.is_grounded)
			vel = fighter.body.velocity
			fighter.body.velocity = (vel.x, 0)
			jump_v = math.sqrt(2.0 * JUMP_HEIGHT * abs(game_state.physics_sim.gravity.y))
			y_force = fighter.body.mass * jump_v
			fighter.body.apply_impulse_at_local_point((0, y_force))
			is_doing_action = True

		if fighter.recover_timer == 0 and is_doing_action == False:
			for attack in fighter.attacks:
				trigger_results = is_attack_triggered(attack, fighter.is_grounded, fighter.input, fighter.midair_jumps_left)
				if trigger_results.can_activate:
					if trigger_results.is_needing_fighter_jump:
						fighter.midair_jumps_left = fighter.midair_jumps_left - 1

					attack.activate(fighter.side_facing)
					is_doing_action=True
					break	

		attack_velocity = (0,0)
		if is_doing_action and attack_results.is_active and attack_results.velocity != None:
			attack_velocity = attack_results.velocity
			if fighter.side_facing == consts.FIGHTER_SIDE_FACING_LEFT:
				attack_velocity = -attack_velocity[0], attack_velocity[1]
		
		if is_doing_action or fighter.recover_timer == 0:
			fighter.body.velocity = dx + attack_velocity[0], fighter.body._get_velocity().y

		if fighter.dodge_cooldown_timer == 0 and is_doing_action == False and fighter.input.is_tapped(input.INPUT_DODGE):
			fighter.is_dodging = True
			fighter.dodge_cooldown_timer = consts.DODGE_COOLDOWN_FRAMES
			any_moves_pressed = fighter.input.is_one_pressed([input.INPUT_JUMP, input.INPUT_MOVE_LEFT, input.INPUT_MOVE_RIGHT, input.INPUT_MOVE_DOWN])
			are_left_right_pressed = fighter.input.is_one_pressed([input.INPUT_MOVE_LEFT, input.INPUT_MOVE_RIGHT])
			if fighter.is_grounded:
				if are_left_right_pressed:
					fighter.dodge_timer = consts.MOVE_DODGE_INVULN_FRAMES
				else:
					fighter.dodge_timer = consts.NEUTRAL_DODGE_INVULN_FRAMES
			else:
				if any_moves_pressed:
					fighter.dodge_timer = consts.MOVE_DODGE_INVULN_FRAMES
				else:
					fighter.dodge_timer = consts.AIR_NEUTRAL_DODGE_INVULN_FRAMES
					fighter.gravity_cancel_timer = consts.GRAVITY_CANCEL_WINDOW_FRAMES

		is_doing_action = fighter.is_dodging
		for shape in fighter.hurtbox_shapes:
			shape.color = HURTBOX_COLOR
			if fighter.is_dodging:
				shape.color = HURTBOX_DODGE_COLOR

		fighter.body.velocity = fighter.body._get_velocity().x, max(fighter.body._get_velocity().y, -FALL_VELOCITY) + attack_velocity[1]

		if fighter.is_hit == False:
			fighter.recover_timer = max(fighter.recover_timer-1, 0)
		fighter.is_hit = False

		fighter.is_dodging = fighter.dodge_timer > 0
		if fighter.is_dodging == False:
			fighter.dodge_cooldown_timer = max(fighter.dodge_cooldown_timer-1, 0)
		fighter.dodge_timer = min(fighter.dodge_timer - 1, 0)

		fighter.body.is_gravity_cancelled_due_to_attacking = fighter.body.is_gravity_cancelled_due_to_attacking and attack_results.is_active
		#current input should be copied into previous input AFTER all logic needing input has been processed
		fighter.input.copy_current_to_previous()

	game_state.physics_sim.step(TIMESTEP)


game_window = pyglet.window.Window(fullscreen=True, style=pyglet.window.Window.WINDOW_STYLE_BORDERLESS)
physics_batch = pyglet.graphics.Batch()
@game_window.event
def on_draw():
	# draw things here
	game_window.clear()

	physics_draw_options = pyglet_util.DrawOptions(batch=physics_batch)
	physics_draw_options.transform = pymunk.Transform.scaling(PIXELS_PER_WORLD_UNITS)
	game_state.physics_sim.debug_draw(physics_draw_options)
	physics_batch.draw()
	for fighter in game_state.fighters:
		body = fighter.body
		label = pyglet.text.Label('DP: {}'.format(fighter.dmg_points),
                          font_name='Times New Roman',
                          font_size=24,
                          x=body.position.x * PIXELS_PER_WORLD_UNITS, y=(body.position.y + 10) * PIXELS_PER_WORLD_UNITS,
                          anchor_x='center', anchor_y='center')
		label.draw()

		facing_triangle_size = 6

		xoffset = facing_triangle_size * (1 - 2*int(fighter.side_facing == consts.FIGHTER_SIDE_FACING_LEFT))
		x12 = (body.position.x - 0.5*xoffset) * PIXELS_PER_WORLD_UNITS
		y1 = (body.position.y - 0.5*facing_triangle_size) * PIXELS_PER_WORLD_UNITS
		y2 = (body.position.y + 0.5*facing_triangle_size) * PIXELS_PER_WORLD_UNITS
		x3 = (body.position.x + 0.5*xoffset) * PIXELS_PER_WORLD_UNITS
		y3 = body.position.y * PIXELS_PER_WORLD_UNITS
		facing_triangle = pyglet.shapes.Triangle(x12, y1, x12, y2, x3, y3)
		facing_triangle.draw()

@game_window.event
def on_key_press(key, modifiers):
	fighter: Fighter = game_state.fighters[DEVICE_CONTROLLED_FIGHTER_INDEX]
	if key == pyglet.window.key.LEFT:
		fighter.input.current[input.INPUT_MOVE_LEFT] = True
	if key == pyglet.window.key.RIGHT:
		fighter.input.current[input.INPUT_MOVE_RIGHT] = True
	if key == pyglet.window.key.DOWN:
		fighter.input.current[input.INPUT_MOVE_DOWN] = True
	if key == pyglet.window.key.UP:
		fighter.input.current[input.INPUT_JUMP] = True
	if key == pyglet.window.key.Z:
		fighter.input.current[input.INPUT_DODGE] = True
	if key == pyglet.window.key.X: 
		fighter.input.current[input.INPUT_HEAVY_HIT] = True
	if key == pyglet.window.key.C:
		fighter.input.current[input.INPUT_LIGHT_HIT] = True
	if key == pyglet.window.key.V:
		fighter.input.current[input.INPUT_THROW] = True
	if key == pyglet.window.key.O:
		game_state.gravity_enabled = not game_state.gravity_enabled
		if game_state.gravity_enabled:
			game_state.physics_sim._set_gravity((0,-100))
		else:
			game_state.physics_sim._set_gravity((0,0))
			fighter.body._set_velocity((0,0))

@game_window.event
def on_key_release(key, modifiers):
	fighter: Fighter = game_state.fighters[DEVICE_CONTROLLED_FIGHTER_INDEX]
	if key == pyglet.window.key.LEFT:
		fighter.input.current[input.INPUT_MOVE_LEFT] = False
	if key == pyglet.window.key.RIGHT:
		fighter.input.current[input.INPUT_MOVE_RIGHT] = False
	if key == pyglet.window.key.DOWN:
		fighter.input.current[input.INPUT_MOVE_DOWN] = False
	if key == pyglet.window.key.UP:
		fighter.input.current[input.INPUT_JUMP] = False
	if key == pyglet.window.key.Z:
		fighter.input.current[input.INPUT_DODGE] = False
	if key == pyglet.window.key.X: 
		fighter.input.current[input.INPUT_HEAVY_HIT] = False
	if key == pyglet.window.key.C:
		fighter.input.current[input.INPUT_LIGHT_HIT] = False
	if key == pyglet.window.key.V:
		fighter.input.current[input.INPUT_THROW] = False

if __name__ == "__main__":
	pyglet.clock.schedule_interval(step_game, TIMESTEP)
	pyglet.app.run()


