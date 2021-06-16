import melee
import Chains
import random
import math
from melee.enums import Action
from Tactics.punish import Punish
from Tactics.tactic import Tactic
from Chains.falcondive import Falcondive

class Recover(Tactic):
    # Do we need to recover?
    def needsrecovery(smashbot_state, opponent_state, gamestate):
        onedge = smashbot_state.action in [Action.EDGE_HANGING, Action.EDGE_CATCHING]
        opponentonedge = opponent_state.action in [Action.EDGE_HANGING, Action.EDGE_CATCHING, Action.EDGE_GETUP_SLOW, \
        Action.EDGE_GETUP_QUICK, Action.EDGE_ATTACK_SLOW, Action.EDGE_ATTACK_QUICK, Action.EDGE_ROLL_SLOW, Action.EDGE_ROLL_QUICK]

        # If the opponent is on-stage, and Smashbot is on-edge, Smashbot needs to ledgedash
        if not opponent_state.off_stage and onedge:
            return True

        # If we're on stage, then we don't need to recover
        if not smashbot_state.off_stage:
            return False

        if smashbot_state.on_ground:
            return False

        # We can now assume that we're off the stage...

        # If opponent is dead
        if opponent_state.action in [Action.DEAD_DOWN, Action.DEAD_RIGHT, Action.DEAD_LEFT, \
                Action.DEAD_FLY, Action.DEAD_FLY_STAR, Action.DEAD_FLY_SPLATTER]:
            return True

        # If opponent is on stage
        if not opponent_state.off_stage:
            return True

        # If opponent is in hitstun, then recover, unless we're on the edge.
        if opponent_state.off_stage and opponent_state.hitstun_frames_left > 0 and not onedge:
            return True

        if opponent_state.action == Action.DEAD_FALL and opponent_state.position.y < -30:
            return True

        # If opponent is closer to the edge, recover
        diff_x_opponent = abs(melee.stages.EDGE_POSITION[gamestate.stage] - abs(opponent_state.position.x))
        diff_x = abs(melee.stages.EDGE_POSITION[gamestate.stage] - abs(smashbot_state.position.x))

        # Using (opponent_state.position.y + 15)**2 was causing a keepdistance/dashdance bug.
        opponent_dist = math.sqrt( (opponent_state.position.y)**2 + (diff_x_opponent)**2 )
        smashbot_dist = math.sqrt( (smashbot_state.position.y)**2 + (diff_x)**2 )

        if opponent_dist < smashbot_dist and not onedge:
            return True

        if smashbot_dist >= 125:
            return True

        # If opponent is ON the edge, recover
        if opponentonedge and not onedge:
            return True

        return False

    def __init__(self, logger, controller, framedata, difficulty):
        Tactic.__init__(self, logger, controller, framedata, difficulty)
        self.logger = logger

    def step(self, gamestate, smashbot_state, opponent_state):
        self._propagate  = (gamestate, smashbot_state, opponent_state)

        opponentonedge = opponent_state.action in [Action.EDGE_HANGING, Action.EDGE_CATCHING, Action.EDGE_GETUP_SLOW, \
        Action.EDGE_GETUP_QUICK, Action.EDGE_ATTACK_SLOW, Action.EDGE_ATTACK_QUICK, Action.EDGE_ROLL_SLOW, Action.EDGE_ROLL_QUICK]

        # If we can't interrupt the chain, just continue it
        if self.chain != None and not self.chain.interruptible:
            self.chain.step(gamestate, smashbot_state, opponent_state)
            return

        frames_left = Punish.framesleft(opponent_state, self.framedata, smashbot_state)
        refresh = False
        if smashbot_state.action in [Action.EDGE_HANGING, Action.EDGE_CATCHING]:
            self.pickchain(Chains.Edgedash, [refresh])
            return

        diff_x = abs(melee.stages.EDGE_POSITION[gamestate.stage] - abs(smashbot_state.position.x))

        facinginwards = smashbot_state.facing == (smashbot_state.position.x < 0)
        if smashbot_state.action == Action.DEAD_FALL:
            self.chain = None
            self.pickchain(Chains.DI, [int(smashbot_state.position.x < 0), 0.5])
            return

        # If we can just do nothing and grab the edge, do that
        if -12 < smashbot_state.position.y and (diff_x < 7) and facinginwards and smashbot_state.speed_y_self < 0:
            # Do a Fastfall if we're not already
            if smashbot_state.action == Action.DEAD_FALL and smashbot_state.speed_y_self > -3:
                self.chain = None
                self.pickchain(Chains.DI, [0.5, 0])
                return

            # If we are currently moving away from the stage, DI in
            if (smashbot_state.speed_air_x_self > 0) == (smashbot_state.position.x > 0):
                x = 0
                if smashbot_state.position.x < 0:
                    x = 1
                self.chain = None
                self.pickchain(Chains.DI, [x, 0.5])
                return
            else:
                self.pickchain(Chains.Nothing)
                return

        # Is the opponent going offstage to edgeguard us?
        opponent_edgedistance = abs(opponent_state.position.x) - abs(melee.stages.EDGE_GROUND_POSITION[gamestate.stage])
        opponentxvelocity = opponent_state.speed_air_x_self + opponent_state.speed_ground_x_self
        opponentmovingtoedge = not opponent_state.off_stage and (opponent_edgedistance < 20) and (opponentxvelocity > 0 == opponent_state.position.x > 0)
        opponentgoingoffstage = opponent_state.action in [Action.FALLING, Action.JUMPING_FORWARD, Action.JUMPING_BACKWARD, Action.LANDING_SPECIAL,\
            Action.DASHING, Action.WALK_MIDDLE, Action.WALK_FAST, Action.NAIR, Action.FAIR, Action.UAIR, Action.BAIR, Action.DAIR]

        # First jump back to the stage if we're low
        # Falcon can at least DJ from y = -50.39 and still sweetspot grab the ledge.
        jump_randomizer = random.randint(0, 5) == 1
        if smashbot_state.jumps_left > 0 and (smashbot_state.position.y > -49 or opponentgoingoffstage or opponentmovingtoedge or jump_randomizer):
            self.pickchain(Chains.Jump)
            return

        # Don't airdodge recovery if we still have attack velocity. It just causes an SD
        hit_movement = abs(smashbot_state.speed_x_attack) > 0.2

        x_canairdodge = abs(smashbot_state.position.x) - 18 <= abs(melee.stages.EDGE_GROUND_POSITION[gamestate.stage])
        y_canairdodge = smashbot_state.position.y >= -24

        if x_canairdodge and y_canairdodge and (opponentgoingoffstage or opponentmovingtoedge) and not hit_movement:
            self.pickchain(Chains.Airdodge, [int(smashbot_state.position.x < 0), int(smashbot_state.position.y + smashbot_state.ecb.bottom.y < 5)])
            return

        # Don't up-b if we're super high up, wait a little to come down
        if smashbot_state.speed_y_self < 0 and smashbot_state.position.y < -55:
            self.pickchain(Chains.Falcondive)
            return

        randomhighrecovery = smashbot_state.speed_y_self < 0 and random.randint(0, 10) == 1
        if randomhighrecovery:
            print("Started random high recovery")
            self.pickchain(Chains.Falcondive)
            return

        # DI into the stage
        x = 0
        if smashbot_state.position.x < 0:
            x = 1
        self.chain = None
        self.pickchain(Chains.DI, [x, 0.5])
