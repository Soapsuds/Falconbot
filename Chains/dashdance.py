import melee
import random
from Chains.chain import Chain
from melee.enums import Action, Button

class DashDance(Chain):
    def __init__(self, pivot, radius=0):
        self.pivotpoint = pivot
        self.radius = radius
        self.interruptible = True

    def step(self, gamestate, smashbot_state, opponent_state):
        if smashbot_state.moonwalkwarning and self.controller.prev.main_stick[0] != 0.5:
            self.controller.empty_input()
            return

        # Causes an empty_input if hitting left did not cause Smashbot to be TURNING or DASHING left, i.e. if Smashbot attempts a dashback during frames 1-3 of initial dash forward.
        if (self.controller.prev.main_stick[0] == 1) and (smashbot_state.action == Action.DASHING and not smashbot_state.facing):
            self.controller.empty_input()
            return

        # Causes an empty_input if hitting left did not cause Smashbot to be TURNING or DASHING left, i.e. if Smashbot attempts a dashback during frames 1-3 of initial dash forward.
        if (self.controller.prev.main_stick[0] == 0) and (smashbot_state.action == Action.DASHING and smashbot_state.facing):
            self.controller.empty_input()
            return


        if smashbot_state.action == Action.ON_HALO_WAIT:
            self.controller.tilt_analog(melee.Button.BUTTON_MAIN, 0.5, 0)
            return

        if smashbot_state.action in [Action.LYING_GROUND_UP, Action.LYING_GROUND_DOWN]:
            roll = random.randint(0, 3)
            if roll <= 1:
                self.controller.tilt_analog(melee.Button.BUTTON_MAIN, 0.5, 1)
                return
            elif roll == 2:
                self.controller.tilt_analog(melee.Button.BUTTON_MAIN, 1, 0.5)
                return
            else:
                self.controller.tilt_analog(melee.Button.BUTTON_MAIN, 0, 0.5)
                return

        # If we're in spotdodge or shield, do nothing
        if smashbot_state.action in [Action.SPOTDODGE, Action.SHIELD_RELEASE]:
            self.controller.empty_input()
            return

        # If we're stuck wavedashing, just hang out and do nothing
        if smashbot_state.action == Action.LANDING_SPECIAL and smashbot_state.action_frame < 28:
            self.controller.empty_input()
            return

        # Smashbot normally acts on frame 10 (stored as frame 28) of LANDING_SPECIAL. However, this can prevent him from teetering the ledge when wavedashing forward towards it.
        edgedistance = abs(smashbot_state.position.x) - melee.stages.EDGE_GROUND_POSITION[gamestate.stage]
        if smashbot_state.action == Action.LANDING_SPECIAL and smashbot_state.action_frame == 28 and edgedistance < 2:
            self.controller.empty_input()
            return

        #If we're walking, stop for a frame
        #Also, if we're shielding, don't try to dash. We will accidentally roll
        if smashbot_state.action == Action.WALK_SLOW or \
            smashbot_state.action == Action.WALK_MIDDLE or \
            smashbot_state.action == Action.WALK_FAST or \
            smashbot_state.action == Action.SHIELD_START or \
            smashbot_state.action == Action.SHIELD_REFLECT or \
            smashbot_state.action == Action.SHIELD:
                self.controller.empty_input()
                return

        #If we're starting the turn around animation, keep pressing that way or
        #   else we'll get stuck in the slow turnaround
        if smashbot_state.action == Action.TURNING and smashbot_state.action_frame == 1:
            return

        #Dash back, since we're about to start running
        # Changed for falcon
        if smashbot_state.action == Action.DASHING and smashbot_state.action_frame >= 15:
            self.controller.tilt_analog(melee.Button.BUTTON_MAIN, int(not smashbot_state.facing), .5)
            return

        # Continue holding down if you enter RUN_BRAKE or CROUCH_START. Removed Action.RUNNING from these action states because that was causing down inputs which disrupted waveshine combos.
        if smashbot_state.action in [Action.RUN_BRAKE, Action.CROUCH_START]:
            self.controller.tilt_analog(melee.Button.BUTTON_MAIN, .5, 0)
            return

        # We can't dashback while in CROUCH_END. We can, however, dash forward.
        if smashbot_state.action == Action.CROUCH_END:
            self.controller.tilt_analog(melee.Button.BUTTON_MAIN, int(smashbot_state.facing), 0)
            return

        # We need to input a jump to wavedash out of these states if dash/run gets called while in one of these states, or else we get stuck
        jcstates = smashbot_state.action in [Action.TURNING_RUN] and smashbot_state.action_frame == 3
        if jcstates or (smashbot_state.action == Action.TURNING and smashbot_state.action_frame in range(2,12)): #Also detects accidental tilt turns & decides to wavedash
            self.controller.press_button(Button.BUTTON_Y)
            return

        # Airdodge for the wavedash
        jumping = [Action.JUMPING_ARIAL_FORWARD, Action.JUMPING_ARIAL_BACKWARD, Action.JUMPING_FORWARD, Action.JUMPING_BACKWARD]
        jumpcancel = (smashbot_state.action == Action.KNEE_BEND) and (smashbot_state.action_frame == 4)
        if jumpcancel or (smashbot_state.action in jumping and abs(smashbot_state.position.x) < melee.stages.EDGE_GROUND_POSITION[gamestate.stage]):
            self.controller.press_button(Button.BUTTON_L)
            onleft = smashbot_state.position.x < opponent_state.position.x
            # Normalize distance from (0->1) to (0.5 -> 1)
            x = 1
            if onleft != False:
                x = 0
            # Don't airdodge/WD offstage
            if abs(smashbot_state.position.x) > \
                melee.stages.EDGE_GROUND_POSITION[gamestate.stage] - 25:
                    x = 0
                    if smashbot_state.position.x < 0:
                        x = 1
            self.controller.tilt_analog(Button.BUTTON_MAIN, x, 0.35)
            return

        # We can't dash IMMEDIATELY after landing. So just chill for a bit
        if (smashbot_state.action == Action.LANDING and smashbot_state.action_frame < 4):
            self.controller.empty_input()
            return

        if not smashbot_state.on_ground:
            # Do a fastfall if we're not already
            if smashbot_state.speed_y_self > -2.8:
                self.controller.tilt_analog(Button.BUTTON_MAIN, 0.5, 0)
            else:
                self.controller.tilt_analog(Button.BUTTON_MAIN, int(smashbot_state.position.x < opponent_state.position.x), 0.5)
            return

        # Don't run off the stage
        if abs(smashbot_state.position.x) > \
            melee.stages.EDGE_GROUND_POSITION[gamestate.stage] - 6.9:#(3 * Falon_dash_speed):
                x = 0
                if smashbot_state.position.x < 0:
                    x = 1
                self.controller.tilt_analog(melee.Button.BUTTON_MAIN, x, .5)
                return

        # Are we inside the given radius of dash dancing?
        if (smashbot_state.position.x > self.pivotpoint - self.radius) and (smashbot_state.position.x < self.pivotpoint + self.radius):
            # Dash the direction we're facing to keep going through to the end of the radius
            self.controller.tilt_analog(melee.Button.BUTTON_MAIN, int(smashbot_state.facing), .5)
            return

        # Dash towards the pivot point
        self.controller.tilt_analog(melee.Button.BUTTON_MAIN, int(smashbot_state.position.x < self.pivotpoint), .5)
        return
