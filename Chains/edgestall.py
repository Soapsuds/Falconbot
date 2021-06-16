import melee
from melee.enums import Action, Button
from Chains.chain import Chain

# Edgestall
class Edgestall(Chain):
    def __init__(self, haxdash=True, ffg=False, lgcount=0, justwavedashed=False):
        # Track if we're haxdashing or ff grabbing
        self.haxdash = haxdash
        self.ffg = ffg
        # Track how many times we've stalled
        self.lgcount = lgcount
        # Because we make inputs on falling we need a way to know if we're haxdashing off or 
        # need to jump forward
        self.justwavedashed = justwavedashed

    def step(self, gamestate, smashbot_state, opponent_state):
        controller = self.controller

        # If we just grabbed the edge, wait
        if smashbot_state.action == Action.EDGE_CATCHING:
            # Put in some variety, every stall divisible by 3
            # ffg instead
            if self.lgcount != 0 and self.lgcount % 3 == 0:
                self.haxdash = False
                self.ffg = True
            else: 
                self.haxdash = True
                self.ffg = False
            self.justwavedashed = False
            self.interruptible = True
            controller.empty_input()
            return

        # If we're stuck in landing_special, wait
        if smashbot_state.action == Action.LANDING_SPECIAL:
            controller.empty_input()
            # I guess if we've done more than one we can intterupt here
            if self.lgcount > 1:
                self.interruptible = True
            return

        # If we're jumping backwards we should grab edge unless
        # we get past frame 23
        if smashbot_state.action == Action.JUMPING_ARIAL_BACKWARD:
            if smashbot_state.action_frame < 25:
                controller.empty_input()
                return
            else:
                self.interruptible = True

        # If we are able to let go of the edge, do it
        if smashbot_state.action == Action.EDGE_HANGING:
            # If we already pressed back last frame, let go
            if controller.prev.c_stick != (0.5, 0.5):
                controller.empty_input()
                return
            x = 1
            if smashbot_state.position.x < 0:
                x = 0
            self.interruptible = False
            controller.tilt_analog(Button.BUTTON_C, x, 0.5)
            # if we're fastfall stalling, input the ff here too
            if self.ffg == True:
                controller.tilt_analog(Button.BUTTON_MAIN, 0.5, 0)
            return

        # Once we're falling either keep falling for a bit or start a haxdash
        if smashbot_state.action == Action.FALLING:
            # Failsafe, if we go too low we need to intterupt
            if smashbot_state.position.y < - 50: #TODO fake number
                self.interruptible = True
                return
            if self.ffg == True:
                # keep holding down for the first few frames of falling
                if smashbot_state.action_frame < 4:
                    controller.tilt_analog(Button.BUTTON_MAIN, 0.5, 0)
                    return
                # make sure we're not pressing anything before we have to jump
                elif smashbot_state.action_frame == 5:
                    controller.empty_input()
                    return
                # wait for frame 6, then jump
                # Do a backwards jump to swag (aka not collide with
                # doing haxdashes >.>
                elif smashbot_state.action_frame == 6:
                    x = 0.8
                    if smashbot_state.position.x < 0:
                        x = 0.2
                    controller.tilt_analog(Button.BUTTON_MAIN, x, 1)
                    return
            else:
                # We either need to jump forward right away, or let ourselves fall to the ledge
                if self.justwavedashed == False:
                    # Jump forward right away to start a hax dash
                    x = 0
                    if smashbot_state.position.x < 0:
                        x = 1
                    controller.tilt_analog(Button.BUTTON_MAIN, x, 0.5)
                    controller.press_button(Button.BUTTON_Y)
                    self.lgcount = self.lgcount + 1
                    return
                else:
                    # Fall to the ledge
                    # Was dying doing it too fast, waste a frame
                    if smashbot_state.action_frame < 3:
                        controller.empty_input()
                        return
                    if smashbot_state.action_frame < 4:
                        controller.tilt_analog(Button.BUTTON_MAIN, 0.5, 0)
                        return
                    if smashbot_state.action_frame >= 4:
                        controller.empty_input()
                        return
        
        
        # We need to jump forward for 17 frames
        if smashbot_state.action == Action.JUMPING_ARIAL_FORWARD:
            forward = 0
            backward = 1
            if smashbot_state.position.x < 0:
                forward = 1
                backward = 0
            if smashbot_state.action_frame < 17:
                controller.tilt_analog(Button.BUTTON_MAIN, forward, 0.5)
                return
            # Once we've jumped for 17 frames WD back
            if smashbot_state.action_frame >= 17:
                controller.tilt_analog(Button.BUTTON_MAIN, backward, 0) 
                controller.press_button(Button.BUTTON_L)
                self.justwavedashed = True
                self.lgcount = self.lgcount + 1
                return
