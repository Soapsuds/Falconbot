import melee
from melee.enums import Action, Button
from Chains.chain import Chain
from enum import Enum

class Gentleman(Chain):
    def __init__(self, goodrelease1=False, goodrelease2=False, goodrelease3=False):
        self.goodrelease1 = goodrelease1
        self.goodrelease2 = goodrelease2
        self.goodrelease3 = goodrelease3
        self.interruptible = False

    def step(self, gamestate, smashbot_state, opponent_state):
        controller = self.controller
        gentactions = [Action.NEUTRAL_ATTACK_1, Action.NEUTRAL_ATTACK_2, Action.NEUTRAL_ATTACK_3, Action.WALK_SLOW, Action.WALK_MIDDLE]
        firsttwo = [Action.NEUTRAL_ATTACK_1, Action.NEUTRAL_ATTACK_2]
        canjab = smashbot_state.action in [Action.STANDING, Action.TURNING]
        rapidjabs = [Action.LOOPING_ATTACK_START, Action.LOOPING_ATTACK_MIDDLE, Action.LOOPING_ATTACK_END]


        # if we messed up and rapid jabed go ahead and interrupt
        if smashbot_state.action in rapidjabs:
            self.interruptible = True
        # if we're waiting go ahead and start a jab
        if canjab:
            controller.press_button(Button.BUTTON_A)
            return

        if smashbot_state.action not in gentactions:
            controller.empty_input()

        if smashbot_state.action in gentactions:
            # Release A when in hitlag.
            if smashbot_state.hitlag_left:
                if smashbot_state.action == Action.NEUTRAL_ATTACK_1:
                    self.goodrelease1 = True
                if smashbot_state.action == Action.NEUTRAL_ATTACK_2:
                    self.goodrelease2 = True
                if smashbot_state.action == Action.NEUTRAL_ATTACK_3:
                    self.goodrelease3 = True
                controller.release_button(Button.BUTTON_A)
                return
            # Stop walking to get ready to press A again if we walked out of a hit
            if smashbot_state.action == Action.WALK_SLOW or smashbot_state == Action.WALK_MIDDLE:
                controller.release_all()
                self.interruptible = True
                return
            # Make sure we release A by now if we missed hitlag
            if smashbot_state.action == Action.NEUTRAL_ATTACK_1 and not self.goodrelease1:
                if smashbot_state.action_frame == 5:
                    controller.release_button(Button.BUTTON_A)
                    return
            # Start jab 2 a bit before we finish jab 1
            if smashbot_state.action == Action.NEUTRAL_ATTACK_1:
                if smashbot_state.action_frame == 7:
                    controller.press_button(Button.BUTTON_A)
                    return
            # Either start jab 3 right away, or walk out of it to get another good release
            if smashbot_state.action == Action.NEUTRAL_ATTACK_2:
                if self.goodrelease1 != True and self.goodrelease2 != True:
                    controller.tilt_analog(Button.BUTTON_MAIN, int(smashbot_state.facing), 0.5)
                    return
                else:
                    # Make sure to release A if we missed hitlag and had one good release already
                    if smashbot_state.action_frame == 5 and not self.goodrelease2:
                        controller.release_button(Button.BUTTON_A)
                        return
                    # Start jab 3
                    if smashbot_state.action_frame == 7:
                        controller.press_button(Button.BUTTON_A)
            if smashbot_state.action == Action.NEUTRAL_ATTACK_3:
                # Hold A until we can intterupt 
                if self.goodrelease3 and (self.goodrelease1 or self.goodrelease2):
                    if smashbot_state.action_frame == 12:
                        self.interruptible = True
                        #TODO maybe wait until the ISAI frame
                        # A should be released because of the hitlag function
                else:
                    #TODO Figure out how to end this sooner, maybe we just crouch for the ISAI frame?
                    if smashbot_state.action_frame == 32:
                        # Release A 
                        controller.release_all()
                        self.interruptible = True
