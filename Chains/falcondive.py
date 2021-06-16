import melee
import random
from melee.enums import Action, Button
from Chains.chain import Chain
from enum import Enum

class FALCONDIVE(Enum):
    SWEETSPOT = 0
    IN = 1
    OUT = 2

class Falcondive(Chain):
    def __init__(self, direction=FALCONDIVE.SWEETSPOT):
        self.direction = direction

    def step(self, gamestate, smashbot_state, opponent_state):
        controller = self.controller

        # We're done here if...
        if smashbot_state.on_ground or smashbot_state.action in [Action.EDGE_CATCHING, Action.EDGE_HANGING]:
            self.interruptible = True
            controller.empty_input()
            return

        x = int(smashbot_state.position.x < 0)

        diff_x = abs(melee.stages.EDGE_POSITION[gamestate.stage] - abs(smashbot_state.position.x))
        # If we're traveling in the air try to drift towards the ledge
        if (smashbot_state.action == Action.SWORD_DANCE_3_LOW and smashbot_state.action_frame > 13) or smashbot_state.action == Action.DEAD_FALL:
            controller.tilt_analog(Button.BUTTON_MAIN, x, 0.5)
            return

        # Which way should we point? We have until frame 13 to turn around
        if smashbot_state.action == Action.SWORD_DANCE_3_LOW and smashbot_state.action_frame <= 13:
            self.interruptible = False

            #if self.direction == SWEETSPOT:
            if diff_x < 7 and smashbot_state.position.y < -45:
                controller.tilt_analog(Button.BUTTON_MAIN, int(not x), 1)
            else:
                controller.tilt_analog(Button.BUTTON_MAIN, x, 1)
            return

        # If we already pressed B last frame, let go
        if controller.prev.button[Button.BUTTON_B]:
            self.interruptible = True
            controller.empty_input()
            return
        controller.press_button(Button.BUTTON_B)
        controller.tilt_analog(Button.BUTTON_MAIN, .5, 1)
        self.interruptible = False
