import melee
import Tactics
from melee.enums import Action, Button
from Chains.chain import Chain
from Chains.gentleman import Gentleman
from Chains.shffl import SHFFL_DIRECTION, Shffl
from enum import Enum

class SHIELD_ACTION(Enum):
    PSRB = 0    # at minimum 18 frames to hitbox
    PSFS = 1    # also 18 frames to hitbox
    PSDTILT = 2 # 10 frames to hitbox
    PSFTILT = 3 # 9 frames to hitbox
    PSFP = 4    # 52 frames to hitbox, should be good for rest punish

class ShieldAction(Chain):
    def __init__(self, action=SHIELD_ACTION.PSRB, direction=SHFFL_DIRECTION.FORWARD):
        self.action = action
        self.direction = direction

    def step(self, gamestate, smashbot_state, opponent_state):
        controller = self.controller

        self.interruptible = True

        # Let go of A if we were already pressing A
        if controller.prev.button[Button.BUTTON_A]:
            controller.empty_input()
            return

        # Let go of B if we were already pressing B
        if controller.prev.button[Button.BUTTON_B]:
            controller.empty_input()
            return

        # Use x to point towards opponent if needed
        x = 0
        if opponent_state.position.x > smashbot_state.position.x:
            x = 1
        # Consider adding redundancy to check for SHIELD_RELEASE, but this just has button inputs atm
        if self.action == SHIELD_ACTION.PSRB:
            controller.press_button(Button.BUTTON_B)
            controller.tilt_analog(Button.BUTTON_MAIN, x, .5)
            return
        if self.action == SHIELD_ACTION.PSFS:
            controller.press_button(Button.BUTTON_A)
            controller.tilt_analog(Button.BUTTON_MAIN, x, 0.5)
            return
        if self.action == SHIELD_ACTION.PSDTILT:
            controller.press_button(Button.BUTTON_A)
            controller.tilt_analog(Button.BUTTON_MAIN, .5, 0.3)
            return
        if self.action == PSFTILT:
            if x == 0:
                x = 0.3
            else:
                x = 0.7
            controller.tilt_analog(Button.BUTTON_MAIN, x, 0.5)
            controller.press_button(Button.BUTTON_A)
            return
        if self.action == PSFP:
            controller.press_button(Button.BUTTON_B)
            return
