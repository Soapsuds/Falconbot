import melee
import math
from melee.enums import Action, Button
from Chains.chain import Chain

class GotoX(Chain):
    def __init__(self, xcord):
        self.xcord = xcord
        self.interruptible = False

    def frame_commitment(smashbot_state, xcord):
        """Given the target x position, how many frmees worth of commitment does it require?"""
        delta_x = abs(smashbot_state.position.x - xcord)
        #TODO v nieve implementation.
        return math.ceil(delta_x / 2.3)

    def step(self, gamestate, smashbot_state, opponent_state):

        # Close enough, go ahead and stop
        if abs(smashbot_state.position.x - self.xcord) < 5:
            self.controller.press_shoulder(Button.BUTTON_L, 1)
            self.interruptible = True
            return

        # if we get stuck in walk stop for one frame then dash
        if smashbot_state.action in [Action.WALK_SLOW, Action.WALK_MIDDLE, Action.WALK_FAST]:
            controller.empty_input()
            return

        #If we're starting the turn around animation, keep pressing that way or
        #   else we'll get stuck in the slow turnaround
        if smashbot_state.action == Action.TURNING and smashbot_state.action_frame == 1:
            return

        controller = self.controller

        #We need to input a jump to wavedash out of these states if dash/run gets called while in one of these states, or else we get stuck
        jcstates = [Action.TURNING_RUN]
        if (smashbot_state.action in jcstates) or (smashbot_state.action == Action.TURNING and smashbot_state.action_frame in range(2,12)):
                self.controller.press_button(Button.BUTTON_Y)
                return

        #If the past action didn't work because Smashbot tried to press Y on a bad frame and continues holding Y, he needs to let go of Y and try again
        if controller.prev.button[Button.BUTTON_Y] and smashbot_state.action in jcstates:
            self.controller.release_button(Button.BUTTON_Y)
            self.controller.press_button(Button.BUTTON_X)
            return

        #If the past action didn't work because Smashbot tried to press Y on a bad frame and continues holding Y, he should let go of X
        if controller.prev.button[Button.BUTTON_X] and smashbot_state.action in jcstates:
            self.controller.release_button(Button.BUTTON_X)
            return

        # Point towards where we need to go
        onleft = smashbot_state.position.x < self.xcord
        x = 0
        if onleft:
            x = 1 
        # Airdodge for the wavedash
        jumping = [Action.JUMPING_ARIAL_FORWARD, Action.JUMPING_ARIAL_BACKWARD]
        jumpcancel = (smashbot_state.action == Action.KNEE_BEND) and (smashbot_state.action_frame == 4)
        if jumpcancel or smashbot_state.action in jumping:
            self.controller.press_button(Button.BUTTON_L)
            self.controller.tilt_analog(Button.BUTTON_MAIN, x, 0.35)
            return

        # Likewise release L after wavedash
        if smashbot_state.action == Action.LANDING_SPECIAL:
            self.controller.empty_input()
            return

        # Otherwise, run in the specified direction
        controller.tilt_analog(Button.BUTTON_MAIN, x, .5)
