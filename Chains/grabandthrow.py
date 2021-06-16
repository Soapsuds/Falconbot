import melee
from melee.enums import Action, Button
from Chains.chain import Chain
from enum import Enum

class THROW_DIRECTION(Enum):
    UP = 0
    DOWN = 1
    FORWARD = 2
    BACK = 3

# Grab and throw opponent
# Falcon will always pummel the opponent once because we can.
# TODO We shoulnd't always, like if we're going for a dropzone or something
class GrabAndThrow(Chain):
    def __init__(self, direction=THROW_DIRECTION.DOWN):
        self.direction = direction

    def step(self, gamestate, smashbot_state, opponent_state):
        controller = self.controller

        self.interruptible = False

        # If we already pressed Z last frame, let go
        if controller.prev.button[Button.BUTTON_Z]:
            controller.empty_input()
            return

        if smashbot_state.action == Action.GRAB and smashbot_state.action_frame > 12:
            controller.empty_input()
            self.interruptible = True
            return

        if smashbot_state.action == Action.LANDING_SPECIAL:
            controller.empty_input()
            self.interruptible = True
            return

        # If we need to jump cancel, or sheild stop do it
        jcstates = [Action.DASHING, Action.RUNNING, Action.RUN_BRAKE]
        if (smashbot_state.action in jcstates):
            if abs(smashbot_state.position.x - opponent_state.position.x) < 5 and (abs(opponent_state.speed_x_attack) < 1 or abs(opponent_state.speed_ground_x_self) < 1):
                controller.press_button(Button.BUTTON_R)
                controller.release_button(Button.BUTTON_Z)
                return
            controller.press_button(Button.BUTTON_Y)
            controller.release_button(Button.BUTTON_Z)
            return

        # Grab on knee bend or sheild
        if smashbot_state.action == Action.KNEE_BEND or smashbot_state == Action.SHIELD_REFLECT:
            controller.release_button(Button.BUTTON_Y)
            controller.release_button(Button.BUTTON_R)
            # Let go of Z if we already had it pressed
            if controller.prev.button[Button.BUTTON_Z]:
                controller.release_button(Button.BUTTON_Z)
                return
            controller.press_button(Button.BUTTON_Z)
            return

        # Do a pummel
        if smashbot_state.action == Action.GRAB_PULLING and smashbot_state.action_frame == 7:
            if controller.prev.button[Button.BUTTON_Z]:
                controller.release_button(Button.BUTTON_Z)
                controller.press_button(Button.BUTTON_A)
                return
            else:
                controller.press_button(Button.BUTTON_Z)
                return

        # Do the throw
        if smashbot_state.action == Action.GRAB_PUMMEL and smashbot_state.action_frame == 23:
            if self.direction == THROW_DIRECTION.DOWN:
                controller.tilt_analog(Button.BUTTON_MAIN, .5, 0)
            if self.direction == THROW_DIRECTION.UP:
                controller.tilt_analog(Button.BUTTON_MAIN, .5, 1)
            if self.direction == THROW_DIRECTION.FORWARD:
                controller.tilt_analog(Button.BUTTON_MAIN, int(smashbot_state.facing), .5)
            if self.direction == THROW_DIRECTION.BACK:
                controller.tilt_analog(Button.BUTTON_MAIN, int(not smashbot_state.facing), .5)
            self.interruptible = True
            return

        # Do the grab
        # Let go of Z if we already had it pressed
        if controller.prev.button[Button.BUTTON_Z]:
            controller.release_button(Button.BUTTON_Z)
            return
        controller.press_button(Button.BUTTON_Z)
