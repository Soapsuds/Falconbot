import melee
import Chains
import math
from melee.enums import Action, Button, Character
from Tactics.tactic import Tactic
from Chains.smashattack import SMASH_DIRECTION
from Chains.shffl import SHFFL_DIRECTION
from Chains.shieldaction import SHIELD_ACTION
from Chains.grabandthrow import THROW_DIRECTION

class Punish(Tactic):
    # How many frames do we have to work with for the punish
    def framesleft(opponent_state, framedata, smashbot_state):
        # For some dumb reason, the game shows the standing animation as having a large hitstun
        #   manually account for this
        if opponent_state.action == Action.STANDING:
            return 1

        # Opponent's shield is broken, opponent is resting Puff.
        restingpuff = opponent_state.character == Character.JIGGLYPUFF and opponent_state.action == Action.MARTH_COUNTER
        if restingpuff or opponent_state.action in [Action.SHIELD_BREAK_STAND_U, Action.SHIELD_BREAK_TEETER]:
            return 249 - opponent_state.action_frame

        # Don't try to punish Samus knee_bend, because they will go into UP_B and it has invulnerability
        if opponent_state.action == Action.KNEE_BEND and opponent_state.character == Character.SAMUS:
            return 0

        # It's unsafe to shine an opponent lying on a platform. Just wait for them to act instead
        if opponent_state.position.y > 5 and opponent_state.action in [Action.LYING_GROUND_UP, Action.LYING_GROUND_DOWN]:
            return 0

        # Samus UP_B invulnerability
        if opponent_state.action in [Action.SWORD_DANCE_3_MID, Action.SWORD_DANCE_3_LOW] and \
                opponent_state.character == Character.SAMUS and opponent_state.action_frame <= 5:
            return 0

        # Samus morph ball
        if opponent_state.character == Character.SAMUS and opponent_state.action in [Action.SWORD_DANCE_4_MID, Action.SWORD_DANCE_4_HIGH, Action.NEUTRAL_B_CHARGING]:
            return 1

        # Pikachu skull bash, thunder
        if opponent_state.action in [Action.NEUTRAL_B_FULL_CHARGE, Action.NEUTRAL_B_ATTACKING, Action.SWORD_DANCE_2_MID_AIR, Action.SWORD_DANCE_2_HIGH_AIR] and \
                opponent_state.character == Character.PIKACHU:
            return 1

        # Jigglypuff jumps
        if opponent_state.character == Character.JIGGLYPUFF and opponent_state.action in \
                [Action.LASER_GUN_PULL, Action.NEUTRAL_B_CHARGING, Action.NEUTRAL_B_ATTACKING, Action.NEUTRAL_B_FULL_CHARGE, Action.WAIT_ITEM]:
            return 1

        if opponent_state.character == Character.SHEIK:
            if opponent_state.action in [Action.SWORD_DANCE_4_HIGH, Action.SWORD_DANCE_1_AIR]:
                return 17 - opponent_state.action_frame
            if opponent_state.action in [Action.SWORD_DANCE_4_LOW, Action.SWORD_DANCE_2_HIGH_AIR] and opponent_state.action_frame <= 21:
                return 0

        # Shine wait
        if opponent_state.character in [Character.FOX, Character.FALCO]:
            if opponent_state.action in [Action.SWORD_DANCE_2_MID_AIR, Action.SWORD_DANCE_3_HIGH_AIR, Action.SWORD_DANCE_3_LOW_AIR]:
                return 3

        if opponent_state.action == Action.LOOPING_ATTACK_MIDDLE:
            return 1

        if opponent_state.character == Character.SHEIK and opponent_state.action == Action.SWORD_DANCE_2_HIGH:
            return 1

        # Is opponent attacking?
        if framedata.is_attack(opponent_state.character, opponent_state.action):
            # What state of the attack is the opponent in?
            # Windup / Attacking / Cooldown
            attackstate = framedata.attack_state(opponent_state.character, opponent_state.action, opponent_state.action_frame)
            if attackstate == melee.enums.AttackState.WINDUP:
                # Don't try to punish opponent in windup when they're invulnerable
                if opponent_state.invulnerability_left > 0:
                    return 0
                # Don't try to punish standup attack windup
                if opponent_state.action in [Action.GROUND_ATTACK_UP, Action.GETUP_ATTACK]:
                    return 0
                frame = framedata.first_hitbox_frame(opponent_state.character, opponent_state.action)
                # Account for boost grab. Dash attack can cancel into a grab
                if opponent_state.action == Action.DASH_ATTACK:
                    return min(6, frame - opponent_state.action_frame - 1)
                return max(0, frame - opponent_state.action_frame - 1)
            if attackstate == melee.enums.AttackState.ATTACKING and smashbot_state.action == Action.SHIELD_RELEASE:
                if opponent_state.action in [Action.NAIR, Action.FAIR, Action.UAIR, Action.BAIR, Action.DAIR]:
                    return 7
                elif opponent_state.character == Character.PEACH and opponent_state.action in [Action.NEUTRAL_B_FULL_CHARGE, Action.WAIT_ITEM, Action.NEUTRAL_B_ATTACKING, Action.NEUTRAL_B_CHARGING, Action.NEUTRAL_B_FULL_CHARGE_AIR]:
                    return 6
                else:
                    return framedata.frame_count(opponent_state.character, opponent_state.action) - opponent_state.action_frame
            if attackstate == melee.enums.AttackState.ATTACKING and smashbot_state.action != Action.SHIELD_RELEASE:
                return 0
            if attackstate == melee.enums.AttackState.COOLDOWN:
                frame = framedata.iasa(opponent_state.character, opponent_state.action)
                return max(0, frame - opponent_state.action_frame)
        if framedata.is_roll(opponent_state.character, opponent_state.action):
            frame = framedata.last_roll_frame(opponent_state.character, opponent_state.action)
            return max(0, frame - opponent_state.action_frame)

        # Opponent is in hitstun
        if opponent_state.hitstun_frames_left > 0:
            # Special case here for lying on the ground.
            #   For some reason, the hitstun count is totally wrong for these actions
            if opponent_state.action in [Action.LYING_GROUND_UP, Action.LYING_GROUND_DOWN]:
                return 1

            # If opponent is in the air, we need to cap the return at when they will hit the ground
            if opponent_state.position.y > .02 or not opponent_state.on_ground:
                # When will they land?
                speed = opponent_state.speed_y_attack + opponent_state.speed_y_self
                height = opponent_state.position.y
                gravity = framedata.characterdata[opponent_state.character]["Gravity"]
                termvelocity = framedata.characterdata[opponent_state.character]["TerminalVelocity"]
                count = 0
                while height > 0:
                    height += speed
                    speed -= gravity
                    speed = max(speed, -termvelocity)
                    count += 1
                    # Shortcut if we get too far
                    if count > 120:
                        break
                return min(count, opponent_state.hitstun_frames_left)

            return opponent_state.hitstun_frames_left

        # Opponent is in a lag state
        if opponent_state.action in [Action.UAIR_LANDING, Action.FAIR_LANDING, \
                Action.DAIR_LANDING, Action.BAIR_LANDING, Action.NAIR_LANDING]:
            # TODO: DO an actual lookup to see how many frames this is
            return 8 - (opponent_state.action_frame // 3)

        # Exception for Jigglypuff rollout
        #   The action frames are weird for this action, and Jiggs is actionable during it in 1 frame
        if opponent_state.character == Character.JIGGLYPUFF and \
                opponent_state.action in [Action.SWORD_DANCE_1, Action.NEUTRAL_B_FULL_CHARGE_AIR, Action.SWORD_DANCE_4_LOW, \
                Action.SWORD_DANCE_4_MID, Action.SWORD_DANCE_3_LOW]:
            return 1

        # Opponent is in a B move
        if framedata.is_bmove(opponent_state.character, opponent_state.action):
            return framedata.frame_count(opponent_state.character, opponent_state.action) - opponent_state.action_frame

        return 1

    # Static function that returns whether we have enough time to run in and punish,
    # given the current gamestate. 
    def canpunish(smashbot_state, opponent_state, gamestate, framedata):

        restingpuff = opponent_state.character == Character.JIGGLYPUFF and opponent_state.action == Action.MARTH_COUNTER
        if restingpuff or opponent_state.action in [Action.SHIELD_BREAK_TEETER, Action.SHIELD_BREAK_STAND_U]:
            return True

        # Wait until the later shieldbreak animations to punish, sometimes Smashbot usmashes too early
        if opponent_state.action in [Action.SHIELD_BREAK_FLY, Action.SHIELD_BREAK_DOWN_U]:
            return False

        # Can't punish opponent in shield
        shieldactions = [Action.SHIELD_START, Action.SHIELD, Action.SHIELD_RELEASE, \
            Action.SHIELD_STUN, Action.SHIELD_REFLECT]
        if opponent_state.action in shieldactions:
            return False

        if smashbot_state.off_stage or opponent_state.off_stage:
            return False

        firefox = opponent_state.action == Action.SWORD_DANCE_3_LOW and opponent_state.character in [Character.FOX, Character.FALCO]
        if firefox and opponent_state.position.y > 15:
            return False

        left = Punish.framesleft(opponent_state, framedata, smashbot_state)
        # Will our opponent be invulnerable for the entire punishable window?
        if left <= opponent_state.invulnerability_left:
            return False

        if framedata.is_roll(opponent_state.character, opponent_state.action):
            return True

        # We might be able to jab, we'll check next
        if left < 3:
            return False

        # Can we jab right now without any movement?
        jabablestates = [Action.TURNING, Action.STANDING, Action.WALK_SLOW, Action.WALK_MIDDLE, \
            Action.WALK_FAST, Action.EDGE_TEETERING_START, Action.EDGE_TEETERING, Action.CROUCHING]
        falconjabrange = 14.13 
        if gamestate.distance < falconjabrange and smashbot_state in jabablestates and opponent_state.on_ground:
            return True

        # Standing grab was covered above, check if we're in range to jc grab
        if left < 9:
            return False

        dashablestates = [Action.TURNING, Action.STANDING, Action.EDGE_TEETERING_START, \
                Action.EDGE_TEETERING, Action.CROUCHING, Action.DASHING]
        dashoneframegrabrange = 23.21 # 9-10 frames (grab active for 2 frames, max distance)
        if gamestate.distance < dashoneframegrabrange and smashbot_state in dashablestates:
            return True

        falconrunspeed = 2.3
        fullspeedgrabslide=26.84    # runnning at 2.3 and jc grabbing will put the grab box 
                                    # this many units away from bot's x position on the 8th grab frame

        #TODO: Subtract from this time spent turning or transitioning
        # Assume that we can run at max speed toward our opponent
        potentialgrabdistance = (left-8) * falconrunspeed + fullspeedgrabslide

        if gamestate.distance < potentialgrabdistance:
            return True
        return False

    def step(self, gamestate, smashbot_state, opponent_state):
        self._propagate  = (gamestate, smashbot_state, opponent_state)

        framesleft = Punish.framesleft(opponent_state, self.framedata, smashbot_state)
        endposition = opponent_state.position.x + self.framedata.slide_distance(opponent_state, opponent_state.speed_x_attack, framesleft)
        slidedistance = self.framedata.slide_distance(smashbot_state, smashbot_state.speed_ground_x_self, framesleft)
        smashbot_endposition = slidedistance + smashbot_state.position.x

        if self.logger:
            self.logger.log("Notes", "framesleft: " + str(framesleft) + " ", concat=True)

        #If we can't interrupt the chain, just continue it
        if self.chain != None and not self.chain.interruptible:
            self.chain.step(gamestate, smashbot_state, opponent_state)
            return

        # TODO: May be missing some relevant inactionable states
        inactionablestates = [Action.THROW_DOWN, Action.THROW_UP, Action.THROW_FORWARD, Action.THROW_BACK, Action.UAIR_LANDING, Action.FAIR_LANDING, \
                Action.DAIR_LANDING, Action.BAIR_LANDING, Action.NAIR_LANDING, Action.UPTILT, Action.DOWNTILT, Action.UPSMASH, \
                Action.DOWNSMASH, Action.FSMASH_MID, Action.FTILT_MID, Action.FTILT_LOW, Action.FTILT_HIGH]
        if smashbot_state.action in inactionablestates:
            self.pickchain(Chains.Nothing)
            return

        # Attempt powershield action, note, we don't have a way of knowing for sure if we hit a physical PS
        # I mean, checking that shield_strength is MAXED is a pretty good way to know :/
        powershieldrelease = (smashbot_state.action == Action.SHIELD_RELEASE and smashbot_state.shield_strength >= 59.9)
        opponentxvelocity = (opponent_state.speed_air_x_self + opponent_state.speed_ground_x_self + opponent_state.speed_x_attack)
        opponentyvelocity = (opponent_state.speed_y_attack + opponent_state.speed_y_self)
        opponentonright = opponent_state.position.x > smashbot_state.position.x

        if powershieldrelease:
            # Sometimes shine OOS will miss because the oppponent is still rising with an aerial. Peach's float can be hard to shine OOS.
            if opponent_state.position.y >= 10:
                # If the opponent is above a certain height and still rising, or outside of a small x range, don't jab, just WD.
                if opponentyvelocity >= 0 or abs(opponent_state.position.x - smashbot_state.position.x) > 10:
                    self.pickchain(Chains.Wavedash)
                    return
                # Maybe we can RB or at least jab
                else:
                    if framesleft >= 18:
                        self.pickchain(Chains.ShieldAction, [SHIELD_ACTION.PSRB])
                    else:
                        self.pickchain(Chains.ShieldAction, [SHIELD_ACTION.PSJAB])
                    return
            # If the opponent is closer to the ground
            else:
                if framesleft >= 60:
                    self.pickchain(Chains.ShieldAction, [SHIELD_ACTION.PSFP])
                    return
                # Do a bunch of different things depending on the amount of frames left
                if gamestate.distance <= 30 and framesleft >= 22 and opponent_state.percent < 62: 
                    self.pickchain(Chains.ShieldAction, [SHIELD_ACTION.PSRB])
                    return
                if gamestate.distance <= 20 and framesleft >= 20 and opponent_state.percent < 66: 
                    self.pickchain(Chains.Shffl, [SHFFL_DIRECTION.DOWN])
                    return
                if gamestate.distance <= 20 and framesleft >= 20: 
                    self.pickchain(Chains.ShieldAction, [SHIELD_ACTION.PSFS])
                    return
                if gamestate.distance <= 16 and framesleft >= 10: 
                    self.pickchain(Chains.ShieldAction, [SHIELD_ACTION.PSDTILT])
                    return
                if gamestate.distance <= 15 and framesleft >= 9: 
                    self.pickchain(Chains.ShieldAction, [SHIELD_ACTION.PSFTILT])
                    return
                if gamestate.distance <= 13 and framesleft >= 3: 
                    self.pickchain(Chains.ShieldAction, [SHIELD_ACTION.PSJAB])
                    return

                self.pickchain(Chains.Wavedash)
                return

        shieldactions = [Action.SHIELD_START, Action.SHIELD, Action.SHIELD_RELEASE, \
            Action.SHIELD_STUN, Action.SHIELD_REFLECT]

        # Shffl OOS if possible
        if smashbot_state.action in shieldactions and abs(opponent_state.position.x - smashbot_state.position.x) < 18:
            if framesleft >= 20:
                self.pickchain(Chains.Shffl, [SHFFL_DIRECTION.DOWN])
                return
            if framesleft >= 18:
                self.pickchain(Chains.Shffl, [SHFFL_DIRECTION.FORWARD])
                return
            if framesleft >= 10:
                self.pickchain(Chains.Shffl, [SHFFL_DIRECTION.UP])
                return
        elif smashbot_state.action in shieldactions:
            self.pickchain(Chains.Wavedash)
            return

        # THE REST IS FUCKING INSAINE
        # Okay, let's try to modify this to just grab
        # How many frames do we need for a grab
        # It's 7 frames normally, plus some transition frames
        # 1 if in shield or dash/running
        framesneeded = 7
        runningactions = [Action.DASHING, Action.RUNNING]
        if smashbot_state.action in shieldactions:
            framesneeded += 1
        if smashbot_state.action in runningactions:
            framesneeded += 1

        endposition = opponent_state.position.x
        isroll = self.framedata.is_roll(opponent_state.character, opponent_state.action)
        slideoff = False

        # If we have the time....
        if framesneeded <= framesleft:
            # Calculate where the opponent will end up
            if opponent_state.hitstun_frames_left > 0:
                endposition = opponent_state.position.x + self.framedata.slide_distance(opponent_state, opponent_state.speed_x_attack, framesleft)

            if isroll:
                endposition = self.framedata.roll_end_position(opponent_state, gamestate.stage)

                initialrollmovement = 0
                facingchanged = False
                try:
                    initialrollmovement = self.framedata.framedata[opponent_state.character][opponent_state.action][opponent_state.action_frame]["locomotion_x"]
                    facingchanged = self.framedata.framedata[opponent_state.character][opponent_state.action][opponent_state.action_frame]["facing_changed"]
                except KeyError:
                    pass
                backroll = opponent_state.action in [Action.ROLL_BACKWARD, Action.GROUND_ROLL_BACKWARD_UP, \
                    Action.GROUND_ROLL_BACKWARD_DOWN, Action.BACKWARD_TECH]
                if not (opponent_state.facing ^ facingchanged ^ backroll):
                    initialrollmovement = -initialrollmovement

                speed = opponent_state.speed_x_attack + opponent_state.speed_ground_x_self - initialrollmovement
                endposition += self.framedata.slide_distance(opponent_state, speed, framesleft)

                # But don't go off the end of the stage
                if opponent_state.action in [Action.TECH_MISS_DOWN, Action.TECH_MISS_UP, Action.NEUTRAL_TECH]:
                    if abs(endposition) > melee.stages.EDGE_GROUND_POSITION[gamestate.stage]:
                        slideoff = True
                endposition = max(endposition, -melee.stages.EDGE_GROUND_POSITION[gamestate.stage])
                endposition = min(endposition, melee.stages.EDGE_GROUND_POSITION[gamestate.stage])


            # And if we're in range...
            # Take our sliding into account
            slidedistance = self.framedata.slide_distance(smashbot_state, smashbot_state.speed_ground_x_self, framesleft)
            smashbot_endposition = slidedistance + smashbot_state.position.x

            # Do we have to consider character pushing?
            # Are we between the character's current and predicted position?
            if opponent_state.position.x < smashbot_endposition < endposition or \
                    opponent_state.position.x > smashbot_endposition > endposition:
                # Add a little bit of push distance along that path
                # 0.3 pushing for max of 16 frames
                #TODO Needs work here
                onleft = smashbot_state.position.x < opponent_state.position.x
                if onleft:
                    smashbot_endposition -= 4.8
                else:
                    smashbot_endposition += 4.8

            if self.logger:
                self.logger.log("Notes", "endposition: " + str(endposition) + " ", concat=True)
                self.logger.log("Notes", "smashbot_endposition: " + str(smashbot_endposition) + " ", concat=True)

            facing = smashbot_state.facing == (smashbot_endposition < endposition)
            # Remember that if we're turning, the attack will come out the opposite way
            # On f1 of smashturn, smashbot hasn't changed directions yet. On/after frame 2, it has. Tilt turn may be a problem.
            if smashbot_state.action == Action.TURNING and smashbot_state.action_frame == 1:
                facing = not facing

            # Get height of opponent at the targeted frame
            height = opponent_state.position.y
            firefox = opponent_state.action == Action.SWORD_DANCE_3_LOW and opponent_state.character in [Character.FOX, Character.FALCO]
            speed = opponent_state.speed_y_attack
            gravity = self.framedata.characterdata[opponent_state.character]["Gravity"]
            termvelocity = self.framedata.characterdata[opponent_state.character]["TerminalVelocity"]
            if not opponent_state.on_ground and not firefox:
                # Loop through each frame and count the distances
                for i in range(framesleft):
                    speed -= gravity
                    # We can't go faster than termvelocity downwards
                    speed = max(speed, -termvelocity)
                    height += speed

            distance = abs(endposition - smashbot_endposition)
            x = 1
            # If we are really close to the edge, wavedash straight down
            if melee.stages.EDGE_GROUND_POSITION[gamestate.stage] - abs(smashbot_state.position.x) < 3:
                x = 0
            if not slideoff and distance < 10.7 and opponent_state.on_ground or (-5 < height < 8 and opponent_state.speed_y_self < 0) :
                if facing:
                    self.chain = None
                    # Do the grab
                    # NOTE: If we get here, we want to delete the chain and start over
                    #   Since the amount we need to charge may have changed
                    self.pickchain(Chains.GrabAndThrow, [THROW_DIRECTION.DOWN])
                    return
#                else:
#                    # Do the bair if there's not enough time to wavedash, but we're facing away and out of shine range
#                    #   This shouldn't happen often, but can if we're pushed away after powershield
#                    offedge = melee.stages.EDGE_GROUND_POSITION[gamestate.stage] < abs(endposition)
#                    if framesleft < 11 and not offedge:
#                        if gamestate.distance <= 9.5 and opponent_state.percent < 89:
#                            self.pickchain(Chains.Waveshine, [x])
#                        else:
#                            self.pickchain(Chains.Shffl, [SHFFL_DIRECTION.BACK])
#                        return
            # If we're not in attack range, and can't run, then maybe we can wavedash in
            #   Now we need more time for the wavedash. 10 frames of lag, and 3 jumping
            framesneeded = 13
            if framesneeded <= framesleft:
                if smashbot_state.action in shieldactions:
                    self.pickchain(Chains.Wavedash)
                    return

        # We can't smash our opponent, so let's just shine instead. Do we have time for that?
        #TODO: Wrap the shine range into a helper
#        framesneeded = 1
#        if smashbot_state.action == Action.DASHING:
#            framesneeded = 2
#        if smashbot_state.action in [Action.SHIELD_RELEASE, Action.SHIELD]:
#            framesneeded = 4
#        if smashbot_state.action in [Action.DOWN_B_STUN, Action.DOWN_B_GROUND_START, Action.DOWN_B_GROUND]:
#            framesneeded = 4
#
#        foxshinerange = 9.9
#        if smashbot_state.action == Action.RUNNING:
#            shinerange = 12.8
#        if smashbot_state.action == Action.DASHING:
#            foxshinerange = 9.5

#        # If we're teetering, and opponent is off stage, hit'm
#        opponent_pushing = (gamestate.distance < 8) and abs(smashbot_state.position.x) > abs(opponent_state.position.x)
#        if smashbot_state.action == Action.EDGE_TEETERING_START and not opponent_pushing:
#            # Little baby wavedash
#            self.pickchain(Chains.Waveshine, [0.2])
#            return
#
#        edgetooclose = (smashbot_state.action == Action.EDGE_TEETERING_START or melee.stages.EDGE_GROUND_POSITION[gamestate.stage] - abs(smashbot_state.position.x) < 5) or (smashbot_state.action in [Action.RUNNING, Action.RUN_BRAKE, Action.CROUCH_START] and melee.stages.EDGE_GROUND_POSITION[gamestate.stage] - abs(smashbot_state.position.x) < 10.5)
#        if gamestate.distance < foxshinerange and not edgetooclose:
#            if framesneeded <= framesleft:
#                # Also, don't shine someone in the middle of a roll
#                if (not isroll) or (opponent_state.action_frame < 3):
#                    self.chain = None
#                    # If we are facing towards the edge, don't wavedash off of it
#                    #   Reduce the wavedash length
#                    x = 1
#                    # If we are really close to the edge, wavedash straight down
#                    if melee.stages.EDGE_GROUND_POSITION[gamestate.stage] - abs(smashbot_state.position.x) < 3:
#                        x = 0
#                    # Additionally, if the opponent is going to get sent offstage by the shine, wavedash down
#                    # This makes Smashbot wavedash down if he shines the opponent outwards near the ledge. The gamestate.distance condition is there to ignore RUNNING situations where Smashbot/opponent are within 0.8 units where an extra frame causes them to switch sides.
#                    if abs(opponent_state.position.x) + 41 > melee.stages.EDGE_GROUND_POSITION[gamestate.stage] and abs(opponent_state.position.x) > abs(smashbot_state.position.x) and gamestate.distance > 0.8 and smashbot_state.action in [Action.RUNNING, Action.RUN_BRAKE, Action.CROUCH_START]:
#                        x = 0
#                    # RUNNING and DASHING are very different. Even if Smashbot/opponent are within 0.1 units of each other during DASHING, they will not cross each other up if Smashbot does a pivot shine.
#                    if abs(opponent_state.position.x) + 41 > melee.stages.EDGE_GROUND_POSITION[gamestate.stage] and abs(opponent_state.position.x) > abs(smashbot_state.position.x) and smashbot_state.action in [Action.DASHING, Action.TURNING, Action.STANDING]:
#                        x = 0
#                    # If we are running away from our opponent, just shine now
#                    onright = opponent_state.position.x < smashbot_state.position.x
#                    if (smashbot_state.speed_ground_x_self > 0) == onright and abs(gamestate.distance) <= 9.5:
#                        self.pickchain(Chains.Waveshine, [x])
#                        return
#                    if framesleft <= 6:
#                        self.pickchain(Chains.Waveshine, [x])
#                        return
#            # We're in range, but don't have enough time. Let's try turning around to do a pivot.
#            else:
#                self.chain = None
#                # Pick a point right behind us
#                pivotpoint = smashbot_state.position.x
#                dashbuffer = 5
#                if smashbot_state.facing:
#                    dashbuffer = -dashbuffer
#                pivotpoint += dashbuffer
#                self.pickchain(Chains.DashDance, [pivotpoint])
#                return

        # Kill the existing chain and start a new one
        self.chain = None
        self.pickchain(Chains.DashDance, [endposition])
