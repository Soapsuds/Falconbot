import melee
from melee.enums import Action, Button
from Chains.chain import Chain

class Stop(Chain):
    def step(self, gamestate, smashbot_state, opponent_state):
        controller = self.controller
        if abs(smashbot_state.speed_ground_x_self) < 0.70 or smashbot_state.action == Action.TURNING:
            self.interruptible = True
        else:
            self.interruptible = False
        # If we're dashing just pivot
        if smashbot_state.action == Action.DASHING:
            controller.tilt_analog(Button.BUTTON_MAIN, int(not smashbot_state.facing), 0.5)
            return
        
        # Otherwise input a shield stop
        controller.tilt_analog(Button.BUTTON_MAIN, 0.5, 0.5)
        if controller.prev.button[Button.BUTTON_L] and smashbot_state.action != Action.SHIELD_REFLECT:
            controller.press_button(Button.BUTTON_R)
        controller.press_button(Button.BUTTON_L)
