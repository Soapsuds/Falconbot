import melee
from melee.enums import Action, Button
from Chains.chain import Chain
from enum import Enum

class AIR_ATTACK_DIRECTION(Enum):
    UP = 0
    DOWN = 1
    FORWARD = 2
    BACK = 3
    NEUTRAL = 4

class AirAttack(Chain):
    def __init__(self, target_x, target_y, height_level, direction=AIR_ATTACK_DIRECTION.UP):
        self.direction = direction
        self.target_x = target_x
        self.target_y = target_y
        self.height_level = height_level

    def attack_height(height_level, direction=AIR_ATTACK_DIRECTION.FORWARD):
        """For a given height level, returns the height of our attack"""
        if direction == AIR_ATTACK_DIRECTION.UP:
            if height_level == 0:
                return 0
            if height_level == 1:
                return 8.5
            if height_level == 2:
                return 16
            if height_level == 3:
                return 28   
            if height_level == 4: 
                return 39
            if height_level == 5:
                return 49
            if height_level == 6:
                return 57
        if direction == AIR_ATTACK_DIRECTION.DOWN:
            if height_level == 0:
                return 1
            if height_level == 1:
                return 12.7
            if height_level == 2: 
                return 27
            if height_level == 3:
                return 31   
            if height_level == 4: 
                return 38 
            if height_level == 5:
                return 49
            if height_level == 6:
                return 59.5
        if direction == AIR_ATTACK_DIRECTION.FORWARD:
            if height_level == 0:
                return 0
            if height_level == 1:
                return 12.9
            if height_level == 2: 
                return 26
            if height_level == 3:
                return 29   
            if height_level == 4: 
                return 37
            if height_level == 5:
                return 55
            if height_level == 6:
                return 66
        return 500

    @staticmethod
    def frame_commitment(height_level, direction=AIR_ATTACK_DIRECTION.UP):
        """Given the target height level, how many frames worth of commitment does it require?"""
        if direction == AIR_ATTACK_DIRECTION.UP:
            if height_level == 0:
                return 25       # wait 14 ff and uair same frame 
            if height_level == 1:
                return 10       # sh instant uair
            if height_level == 2:
                return 10       # fh instant uair
            if height_level == 3:
                return 16       # fh wait 6 uair
            if height_level == 4:
                return 19       # fh wait 8 dj uair
            if height_level == 5:
                return 26       # fh wait 15 dj uair
            if height_level == 6:
                return 32       # FH wait 15 dj wait 7 uair
        if direction == AIR_ATTACK_DIRECTION.DOWN:
            if height_level == 0:
                return 24       # sh wait 4 stomp
            if height_level == 1:
                return 20       # sh stomp
            if height_level == 2:
                return 21      #  fh dj stomp
            if height_level == 3: 
                return 20       # FH stomp
            if height_level == 4: 
                return 24       # fh wait 4 stomp
            if height_level == 5: 
                return 30       # fh wait 9 dj stomp
            if height_level == 6: 
                return 37       # fh wait 16 dj stomp
        if direction == AIR_ATTACK_DIRECTION.FORWARD:
            if height_level == 0:
                return 24       # sh wait 6 knee ff 
            if height_level == 1:
                return 18       # sh instant knee
            if height_level == 2:
                return 19       # DJ knee 
            if height_level == 3:
                return 18       # FH knee
            if height_level == 4:
                return 24       # FH wait 6 Fair
            if height_level == 5: 
                return 29       # FH wait 9 dj fair
            if height_level == 6: 
                return 36       # FH wait 14 dj wait 4 fair
        return 500

    def height_levels():
        """Returns a list of the possible attack height levels"""
        return [0, 1, 2, 3, 4, 5, 6]

    @staticmethod
    def uses_dj(height_level, direction):
        """Returns a bool for if the attack at the height level will use DJ"""
        if direction == AIR_ATTACK_DIRECTION.UP:
            if height_level in [4, 5, 6]:
                return True
            return False
        if direction == AIR_ATTACK_DIRECTION.DOWN:
            if height_level in [2, 5, 6]:
                return True
            return False
        if direction == AIR_ATTACK_DIRECTION.FORWARD:
            if height_level in [2, 5, 6]:
                return True
            return False

    @staticmethod
    def get_x_offset(direction, smashbot_state, target_x, dif_x):
        if direction not in [AIR_ATTACK_DIRECTION.FORWARD, AIR_ATTACK_DIRECTION.UP]:
            return 0
        facing_right = smashbot_state.facing
        target_on_right = dif_x > 0
        if direction == AIR_ATTACK_DIRECTION.FORWARD:
            if facing_right and target_on_right:
                return -5
            if not facing_right and not target_on_right:
                return 5
            # we're not facing towards them so aim well behind them
            if not facing_right and target_on_right:
                return 10
            if facing_right and not target_on_right:
                return -10

        # facing the right way, aim 10 units towards me
        if facing_right and target_on_right:
            return -10
        if not facing_right and not target_on_right:
            return 10
        # we're not facing towards them so aim well behind them
        if not facing_right and target_on_right:
            return 15
        if facing_right and not target_on_right:
            return -15

    @staticmethod
    def get_jump_direction(smashbot_state, target_x, commit, direction):
        """Figure out which direction to hold to get us closer to the target"""
        # Get the delta and the difference between our position and the target
        delta_x = abs(smashbot_state.position.x - target_x)
        dif_x = delta_x
        if smashbot_state.position.x > target_x:
            dif_x = -dif_x
        # Adjust target for knee and uair
        if direction == AIR_ATTACK_DIRECTION.FORWARD or direction == AIR_ATTACK_DIRECTION.UP:
            dif_x = dif_x + AirAttack.get_x_offset(direction, smashbot_state, target_x, dif_x)
        # If we're in the air already check with double jump values
        if smashbot_state.action in [Action.JUMPING_FORWARD, Action.JUMPING_BACKWARD] or (smashbot_state.action == Action.KNEE_BEND and smashbot_state.action_frame == 4):
           hold_right = commit * 1.1 
           hold_left = commit * -1.1
           neutral = 0
        # When we're on the ground momentum might carry into the jump
        else:
            # Going fast to the right
            if smashbot_state.speed_ground_x_self > 1.3:
                hold_right = commit * 2
                hold_left = 1.99 # Drift about this far before slowing down
                neutral = commit * 2
            # Going fast to the left
            elif smashbot_state.speed_ground_x_self < -1.3:
                hold_left = commit * -2
                hold_right = -1.99
                neutral = commit * -2
            else:
                # If we're not moving (or moving very slow) each direction will change our speed by ~1
                hold_right = commit * 0.95
                hold_left = commit * -0.95
                neutral = 0
                # If we're moving slowly subtract the traction and get the speed (if any)
                if smashbot_state.speed_ground_x_self > 0.32:
                    neutral = commit * (smashbot_state.speed_ground_x_self - 0.32)
        # Test which one gives the closer value
        x = 0.5
        if abs(hold_right - dif_x) < abs(hold_left - dif_x) and abs(hold_right - dif_x) <= abs(neutral - dif_x):
            x = 1
        if abs(hold_left - dif_x) < abs(hold_right - dif_x) and abs(hold_left - dif_x) <= abs(neutral - dif_x):
            x = 0
        print("Delta_x :", delta_x, "dif x :", dif_x, "hold_right: ", hold_right, "hold_left: ", hold_left, "neutral: ", neutral)
        print("decided to tilt X: ", x)
        return x

    @staticmethod
    def get_drift_direction(direction, height_level, smashbot_state, target_x, target_y, commit):
        # get delta and dif x
        delta_x = abs(smashbot_state.position.x - target_x)
        dif_x = delta_x
        if smashbot_state.position.x > target_x:
            dif_x = -dif_x
        # adjust the target for Uair and Fair
        if direction == AIR_ATTACK_DIRECTION.FORWARD or direction == AIR_ATTACK_DIRECTION.UP:
            dif_x = dif_x + AirAttack.get_x_offset(direction, smashbot_state, target_x, dif_x)
        # Going fast to the right, holding right or neutral will keep speed the same minus air deceleration every frame
        xspeed = smashbot_state.speed_air_x_self
        if xspeed > 1.1:
            hold_right = commit * xspeed
            hold_left = commit * (xspeed + commit * -0.06)
            neutral = commit * xspeed
        elif xspeed < -1.1:
            hold_right = commit * (xspeed + commit * 0.06)
            hold_left = commit * xspeed
            neutral = commit * xspeed
        else:
            hold_right = commit * (xspeed + 0.06)
            hold_left = commit * (xspeed - 0.06)
            neutral = commit * xspeed
        x = 0.5
        if abs(hold_right - dif_x) < abs(hold_left - dif_x) and abs(hold_right - dif_x) <= abs(neutral - dif_x):
            x = 1
        if abs(hold_left - dif_x) < abs(hold_right - dif_x) and abs(hold_left - dif_x) <= abs(neutral - dif_x):
            x = 0

        print("Dir: ", direction.value, "HL: ", height_level, "at: ", smashbot_state.position.x, ",", smashbot_state.position.y, "speed:", smashbot_state.speed_air_x_self, "Raw target: ", target_x, ",", target_y, "DeltaX = ", delta_x, "Dif X = ", dif_x, "hold_right: ", hold_right, "hold_left: ", hold_left, "neutral: ", neutral, "Holding: ", x)
        return x

    @staticmethod
    def shorthop(direction, height_level):
        if direction == AIR_ATTACK_DIRECTION.UP:
            if height_level in [0, 1]:
                return True
            else:
                return False
        if direction == AIR_ATTACK_DIRECTION.DOWN:
            if height_level in [0, 1]:
                return True
            else:
                return False
        if direction == AIR_ATTACK_DIRECTION.FORWARD:
            if height_level in [0, 1]:
                return True
            else:
                return False

    def step(self, gamestate, smashbot_state, opponent_state):
        self.interruptible = False
        controller = self.controller
        commit = self.frame_commitment(self.height_level, self.direction)
        djactions = [Action.JUMPING_ARIAL_FORWARD, Action.JUMPING_ARIAL_BACKWARD]

        # Landing. We're done
        if smashbot_state.action in [Action.LANDING, 
                Action.UAIR_LANDING, Action.DAIR_LANDING, Action.FAIR_LANDING]:
            print("marked intterupt due to Landing Action")
            self.interruptible = True
            controller.release_all()
            return

        # We've somehow fallen off stage
        if smashbot_state.position.y < 0:
            print("marked intterupt due to y < 0")
            self.interruptible = True
            controller.release_all()
            return

        # Do the first jump
        if smashbot_state.on_ground:
            controller.tilt_analog(Button.BUTTON_C, 0.5, 0.5)
            # Why would we ever still be on the ground after knee bend??
            if controller.prev.button[Button.BUTTON_Y] and smashbot_state.action != Action.KNEE_BEND:
                controller.release_button(Button.BUTTON_Y)
                print("WHY DID THIS GET CALLED?? Returned due to not leaving the ground after kneebend")
                return 
            else:
                # Either SH or fullhop
                if (not self.shorthop(self.direction, self.height_level)) or smashbot_state.action != Action.KNEE_BEND:
                    controller.press_button(Button.BUTTON_Y)
                else:
                    controller.release_button(Button.BUTTON_Y)
                # Frame 3 is where the direction matters
                if smashbot_state.action == Action.KNEE_BEND and smashbot_state.action_frame == 3:
                    x = self.get_jump_direction(smashbot_state, self.target_x, commit, self.direction)
                    controller.tilt_analog(Button.BUTTON_MAIN, x, .5)
                # Fall through to check instant functions
                if smashbot_state.action_frame != 4:
                    return

        # falling back down
        if smashbot_state.speed_y_self < 0:
            # L-Cancel
            #   Spam shoulder button
            if controller.prev.l_shoulder == 0:
                controller.press_shoulder(Button.BUTTON_L, 1.0)
            else:
                controller.press_shoulder(Button.BUTTON_L, 0)

            # Drift onto stage if we're near the edge
            if abs(smashbot_state.position.x) + 18 > melee.stages.EDGE_GROUND_POSITION[gamestate.stage]:
                controller.tilt_analog(Button.BUTTON_MAIN, int(smashbot_state.position.x < 0), 0)
                print("TOO CLOSE TO THE EDGE! PULL  BACK ")
                return
            else:
                # only FF if our attack has come out! (Stomp after DJ doesn't come out until we're falling)
                # and if we haven't fast fallen yet! otherwise we're going to keep drifting towards them until real ladning
                if self.framedata.first_hitbox_frame(smashbot_state.character, smashbot_state.action) < smashbot_state.action_frame - 3 and smashbot_state.speed_y_self > -3:
                    controller.tilt_analog(Button.BUTTON_MAIN, 0.5, 0)
                    return

        # Handle all of the instant stuff (either DJ or inputing moves)
        if smashbot_state.action == Action.KNEE_BEND and smashbot_state.action_frame == 4:
            self.interruptible = False
            # Instant Uair
            if self.direction == AIR_ATTACK_DIRECTION.UP and self.height_level in [1, 2]:
                controller.tilt_analog(Button.BUTTON_C, 0.5, 1)
                return
            # Instant DJ or Knee
            if self.direction == AIR_ATTACK_DIRECTION.FORWARD and self.height_level in [1, 2, 3]:
                if self.height_level == 2:
                    x = self.get_jump_direction(smashbot_state, self.target_x, commit, self.direction)
                    controller.tilt_analog(Button.BUTTON_MAIN, x, 0.5)
                    controller.press_button(Button.BUTTON_X)
                else:
                    controller.tilt_analog(Button.BUTTON_C, int(smashbot_state.facing), 0.5)
                return
            # Instant DJ or Stomp
            if self.direction == AIR_ATTACK_DIRECTION.DOWN and self.height_level in [1, 2, 3]:
                if self.height_level == 2:
                    x = self.get_jump_direction(smashbot_state, self.target_x, commit, self.direction)
                    controller.tilt_analog(Button.BUTTON_MAIN, x, 0.5)
                    controller.press_button(Button.BUTTON_X)
                else:
                    controller.tilt_analog(Button.BUTTON_C, 0.5, 0)
                return
            # Okay, we checked to make sure we don't need to do anything instantly, go ahead and wait for jump to start
            return


        # Okay, we're either in our first or second jump, now what?
        if smashbot_state.action in [Action.JUMPING_FORWARD, Action.JUMPING_BACKWARD, Action.JUMPING_ARIAL_FORWARD, Action.JUMPING_ARIAL_BACKWARD]:
            self.interruptible = False
            # Put in the drift
            x = self.get_drift_direction(self.direction, self.height_level, smashbot_state, self.target_x, self.target_y, commit)
            controller.tilt_analog(Button.BUTTON_MAIN, x, 0.5)
                    
            # Figure out when to double jump
            jump_on_frame = None 
            if self.uses_dj(self.height_level, self.direction):
                if self.direction == AIR_ATTACK_DIRECTION.UP:
                    if self.height_level == 4:
                        jump_on_frame = 8
                    if self.height_level in [5, 6]:
                        jump_on_frame = 15
                if self.direction == AIR_ATTACK_DIRECTION.DOWN:
                    if self.height_level == 4:
                        jump_on_frame = 4
                    if self.height_level == 5:
                        jump_on_frame = 9
                    if self.height_level == 6:
                        jump_on_frame = 16
                if self.direction == AIR_ATTACK_DIRECTION.FORWARD:
                    if self.height_level == 4:
                        jump_on_frame = 6
                    if self.height_level == 5:
                        jump_on_frame = 9
                    if self.height_level == 6:
                        jump_on_frame = 14

            # Fullhop Actions
            if smashbot_state.action in [Action.JUMPING_FORWARD, Action.JUMPING_BACKWARD]:
                # Double jump if required
                if smashbot_state.action_frame == jump_on_frame:
                    x = self.get_jump_direction(smashbot_state, self.target_x, commit, self.direction)
                    controller.tilt_analog(Button.BUTTON_MAIN, x, .5)
                    controller.press_button(Button.BUTTON_Y)
                    return
                else:
                    controller.release_button(Button.BUTTON_Y)
                    # Wait for DJ frame, otherwise fall through
                    if jump_on_frame != None:
                        return
                # Do first jump attacks if required
                if self.direction == AIR_ATTACK_DIRECTION.UP:
                    if self.height_level == 0:
                        # Note the pattern of returning outside the inner if. We wait for the right frame
                        if smashbot_state.action_frame == 14:
                            controller.tilt_analog(Button.BUTTON_C, 0.5, 1)
                        return 
                    if self.height_level == 3:
                        if smashbot_state.action_frame == 6:
                            controller.tilt_analog(Button.BUTTON_C, 0.5, 1)
                        return
                if self.direction == AIR_ATTACK_DIRECTION.DOWN:
                    if self.height_level == 0:
                        if smashbot_state.action_frame == 4:
                            controller.tilt_analog(Button.BUTTON_C, 0.5, 0)
                        return
                    if self.height_level == 4:
                        if smashbot_state.action_frame == 4:
                            controller.tilt_analog(Button.BUTTON_C, 0.5, 0)
                        return
                if self.direction == AIR_ATTACK_DIRECTION.FORWARD:
                    if self.height_level == 0:
                        if smashbot_state.action_frame == 6:
                            controller.tilt_analog(Button.BUTTON_C, int(smashbot_state.facing), 0.5)
                        return
                    if self.height_level == 4:
                        if smashbot_state.action_frame == 6:
                            controller.tilt_analog(Button.BUTTON_C, int(smashbot_state.facing), 0.5)
                        return

            # Do DJ attacks
            if smashbot_state.action in djactions:
                if self.direction == AIR_ATTACK_DIRECTION.UP: 
                    if self.height_level in [4, 5]:
                            controller.tilt_analog(Button.BUTTON_C, 0.5, 1)
                            return
                    if self.height_level == 6:
                        if smashbot_state.action_frame == 7:
                            controller.tilt_analog(Button.BUTTON_C, 0.5, 1)
                        return

                if self.direction == AIR_ATTACK_DIRECTION.DOWN:
                    if self.height_level in [2, 5, 6]:
                        controller.tilt_analog(Button.BUTTON_C, 0.5, 0)
                        return
                if self.direction == AIR_ATTACK_DIRECTION.FORWARD:
                    if self.height_level == 5 or self.height_level == 2:
                            controller.tilt_analog(Button.BUTTON_C, int(smashbot_state.facing), 0.5)
                            return
                    if self.height_level == 6:
                        if smashbot_state.action_frame == 4:
                            controller.tilt_analog(Button.BUTTON_C, int(smashbot_state.facing), 0.5)
                        return
                print("Uh oh, fell off DJ function. SOMETHING SHOULD HAVE BEEN CAUGHT")

        # Drift in during the attack
        if smashbot_state.action in [Action.UAIR, Action.BAIR, Action.DAIR, Action.FAIR, Action.NAIR]:
            x = self.get_drift_direction(self.direction, self.height_level, smashbot_state, self.target_x, self.target_y, commit)
            controller.tilt_analog(Button.BUTTON_MAIN, x, 0.5)
            controller.tilt_analog(Button.BUTTON_C, 0.5, 0.5)
            return

        print("marked intterupt due to falling off bottom")
        self.interruptible = True
        controller.empty_input()
