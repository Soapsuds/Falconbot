import melee
from melee.enums import Action, Button
from Chains.chain import Chain
from enum import Enum


class Raptorboost(Chain):

    def __init__(self, direction=0):
        self.direction = direction
    
    def step(self, gamestate, smashbot_state, opponent_state):
        controller = self.controller

        # We're done once the punching action ends or we're actionable after a miss
        if smashbot_state.action == Action.SWORD_DANCE_1 and smashbot_state.action_frame >= 79 or (smashbot_state.action == Action.SWORD_DANCE_2_HIGH and smashbot_state.action_frame >= 25):
            self.interruptible = True
            return

        # Don't input anything while we're moving or punching
        if smashbot_state.action in [Action.SWORD_DANCE_1, Action.SWORD_DANCE_2_HIGH]:
            self.interruptible = False
            controller.empty_input()
            return
        
        # Check to make sure we're ready to start
        actionable_states = smashbot_state.action in [Action.TURNING, Action.DASHING, Action.RUNNING, Action.RUN_BRAKE, Action.STANDING]
        if actionable_states:
            controller.tilt_analog(Button.BUTTON_MAIN, self.direction, 0.5)
            controller.press_button(Button.BUTTON_B)
            return
        # Otherwise we'll just empty input and see if we get called again
        else:
            controller.empty_input()
            self.interruptible = True
            return
