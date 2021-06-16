import melee
from melee.enums import Action, Button, Character
from Chains.chain import Chain

# Grab the edge
class Grabedge(Chain):
    def __init__(self, wavedash=False, moonwalk=False):
        self.wavedash = wavedash
        self.moonwalk = moonwalk

    def step(self, gamestate, smashbot_state, opponent_state):
        controller = self.controller

        # Moved this here from constructor.
        #   It should be fine, but let's keep an eye out for if this breaks
        edge_x = melee.stages.EDGE_GROUND_POSITION[gamestate.stage]
        if opponent_state.position.x < 0:
            edge_x = -edge_x
        edgedistance = abs(smashbot_state.position.x - edge_x)

        # Where is the edge that we're going to?
        edge_x = melee.stages.EDGE_GROUND_POSITION[gamestate.stage]
        if opponent_state.position.x < 0:
            edge_x = -edge_x

        # If we're on the edge, then we're done here, end the chain
        if smashbot_state.action in [Action.EDGE_HANGING, Action.EDGE_CATCHING]:
            self.interruptible = True
            controller.empty_input()
            return

        # If we're stuck wavedashing, just hang out and do nothing
        if smashbot_state.action == Action.LANDING_SPECIAL: 
            self.interruptible = False
            controller.empty_input()
            return

        # If we're starting a crouch keep holing down
        if smashbot_state.action == Action.CROUCH_START:
            self.interruptible = False
            x = 0.5
            y = 0
            # on frame 7 we can start the pivot
            if smashbot_state.action_frame == 7:
                x = int(not smashbot_state.facing)
                y = 0.5
            controller.tilt_analog(Button.BUTTON_MAIN, x, y)
            return

        #If we're walking, stop for a frame
        #Also, if we're shielding, don't try to dash. We will accidentally roll
        if smashbot_state.action == Action.WALK_SLOW or \
            smashbot_state.action == Action.WALK_MIDDLE or \
            smashbot_state.action == Action.WALK_FAST or \
            smashbot_state.action == Action.SHIELD_START or \
            smashbot_state.action == Action.SHIELD_REFLECT or \
            smashbot_state.action == Action.SHIELD:
                self.interruptible = True
                controller.empty_input()
                return

        facinginwards = smashbot_state.facing == (smashbot_state.position.x < 0)
        if smashbot_state.action == Action.TURNING and smashbot_state.action_frame == 1:
            print("Detected turning: facing in was: ", facinginwards)
            facinginwards = not facinginwards
            print("now facing in is: ", facinginwards)

        edgedistance = abs(smashbot_state.position.x - edge_x)
        turnspeed = abs(smashbot_state.speed_ground_x_self)
        closetoedge = edgedistance < 18

        # By default we're going to try to pivot out of crouch to grab the edge.
        # To do so we can't be in dash we have to be in Run
        # Going from running to crouching always involves one frame of runbrake before crouch starts
        if smashbot_state.action == Action.RUNNING or smashbot_state.action == Action.RUN_BRAKE:
            if closetoedge:
                # Start crouching
                controller.tilt_analog(melee.Button.BUTTON_MAIN, 0.5, 0)
                return

        # If we're standing near the ledge we shouldn't be. Either wavedash off or moonwalk off
        if smashbot_state.action == Action.STANDING and edgedistance < 30:
            if edgedistance < 15:
                controller.press_button(Button.BUTTON_Y)
                self.wavedash = True
                return
            else:
                self.moonwalk = True
                controller.tilt_analog(Button.BUTTON_MAIN, int(smashbot_state.facing), 0.5)
                return

        # Wavedash gets set under the correct conditions so we should be ready to wavedash before it's true
        # Not sure why we need this but I kept stalling on the wavedash function!
        if smashbot_state.action != Action.KNEE_BEND:
            self.wavedash = False

        if self.wavedash and not smashbot_state.off_stage:
            print("THE wavedash stall got called, hopefully it should be!")
            self.interruptible = False
            if smashbot_state.action == Action.KNEE_BEND and smashbot_state.action_frame == 4:
                controller.press_button(Button.BUTTON_L)
                controller.release_button(Button.BUTTON_Y)
                controller.tilt_analog(melee.Button.BUTTON_MAIN, int(not smashbot_state.facing), 0.35)
                self.wavedash = False
                return
            return

        # Keep the moonwalk going or start another 
        if self.moonwalk and not smashbot_state.off_stage:
            self.interruptible = False
            controller.tilt_analog(Button.BUTTON_MAIN, int(not smashbot_state.facing), 0.5)
            if smashbot_state.action_frame == 28:
                controller.tilt_analog(Button.BUTTON_MAIN, int(smashbot_state.facing), 0.5)
                return
            return

        # Fastfall, but only once
        if smashbot_state.action == Action.FALLING:
            self.wavedash = False
            self.moonwalk = False 
            self.interruptible = False

            # Fastfall speed is 3.5, but we need a little wiggle room
            if smashbot_state.speed_y_self > -3.4:
                controller.tilt_analog(melee.Button.BUTTON_MAIN, 0.5, 0)
            else:
                controller.release_all()
            return

        # Pivot slide
        if smashbot_state.action == Action.TURNING:
            # We only want to make a decision on the first frame, otherwise we need to keep sliding
            if smashbot_state.action_frame == 1:
                # speed is less than 0.5 unless we've pivoted out of crouch
                if abs(smashbot_state.speed_ground_x_self) > 0.5:
                    print("Detected pivot slide. Interruptible is false.")
                    self.interruptible = False
                    controller.empty_input()
                    return
                # If we're not sliding very fast we should wavedash off instead
                else:
                    if facinginwards:
                        self.wavedash = True
                        controller.press_button(Button.BUTTON_Y)
                        return
            else:
                # So long as we're still sliding keep waiting
                if abs(smashbot_state.speed_ground_x_self) > 0:
                    controller.empty_input()
                    return
                else:
                    self.interruptible = True
                    return

        # Do the turn
        if smashbot_state.action == Action.DASHING and closetoedge:
            self.interruptible = False
            controller.tilt_analog(melee.Button.BUTTON_MAIN, int(not smashbot_state.facing), .5)
            return

        #We can't dash IMMEDIATELY after landing. So just chill for a bit
        if smashbot_state.action == Action.LANDING and smashbot_state.action_frame < 2:
            self.interruptible = True
            controller.empty_input()
            return

        # If we get here we haven't detected any actionable states, just hold towards the ledge
        if smashbot_state.position.x > edge_x:
            self.interruptible = True
            controller.tilt_analog(melee.Button.BUTTON_MAIN, 0, .5)
            return

        if smashbot_state.position.x < edge_x:
            self.interruptible = True
            controller.tilt_analog(melee.Button.BUTTON_MAIN, 1, .5)
            return
