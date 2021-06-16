import melee
from melee.enums import Action, Button
from Chains.chain import Chain
from enum import Enum

class Taunt(Chain):
    def step(self, gamestate, smashbot_state, opponent_state):
        controller = self.controller
        self.interruptible = True

        controller.press_button(Button.BUTTON_D_UP)
        return
