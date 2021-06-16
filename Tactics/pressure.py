import melee
import Chains
import random
from melee.enums import Action, Button
from Tactics.tactic import Tactic
from Chains.grabandthrow import THROW_DIRECTION
from Chains.shffl import SHFFL_DIRECTION
from Chains.shffl import LOW_HITBOX

# Shield pressure
class Pressure(Tactic):
    def __init__(self, logger, controller, framedata, difficulty):
        Tactic.__init__(self, logger, controller, framedata, difficulty)
        self.shffl = False
        self.dashdance = False

        # What sort of shield pressure should this be? Pick one at random
        rand = random.choice(range(9))

        # On difficulty 1 and 2, only do dash dance
        if self.difficulty <= 2:
            rand = 2

        # 10% chance of being dashdance style pressure
        if rand == 0:
            self.dashdance = True
        # 90% chance of being SHFFL style pressure
        else:
            self.shffl = True

    # We can shield pressuring if...
    def canpressure(opponent_state, gamestate):
        # Opponent must be shielding
        shieldactions = [Action.SHIELD_START, Action.SHIELD, \
            Action.SHIELD_STUN, Action.SHIELD_REFLECT]
        sheilding = opponent_state.action in shieldactions

        if opponent_state.invulnerability_left > 0:
            return False

        # We must be in close range
        # We can be 34 units away to shffl knee
        inrange = gamestate.distance < 34

        return sheilding and inrange

    def step(self, gamestate, smashbot_state, opponent_state):
        self._propagate  = (gamestate, smashbot_state, opponent_state)

        #If we can't interrupt the chain, just continue it
        if self.chain != None and not self.chain.interruptible:
            self.chain.step(gamestate, smashbot_state, opponent_state)
            return

        if self.dashdance:
            self.chain = None
            self.pickchain(Chains.DashDance, [opponent_state.position.x])
            return

        canjab = smashbot_state.action in [Action.TURNING, Action.STANDING, Action.WALK_SLOW, Action.WALK_MIDDLE, \
            Action.WALK_FAST, Action.EDGE_TEETERING_START, Action.EDGE_TEETERING, \
            Action.RUNNING]

        candash = smashbot_state.action in [Action.DASHING, Action.TURNING, Action.RUNNING, \
            Action.EDGE_TEETERING_START, Action.EDGE_TEETERING]

        # This is actually outside of jab 1's range, but we should probably only gentleman if we're quite far away
        injabrange = gamestate.distance < 23 
        # Where will opponent end up, after sliding is accounted for? (at the end of our grab)
        endposition = opponent_state.position.x + self.framedata.slide_distance(opponent_state, opponent_state.speed_ground_x_self, 7)
        ourendposition = smashbot_state.position.x + self.framedata.slide_distance(smashbot_state, smashbot_state.speed_ground_x_self, 7)
        ingrabrange = abs(endposition - ourendposition) < 14.5 

        inrange = gamestate.distance < 34

        # If we're out of range, and CAN dash, then let's just dash in no matter
        if not inrange: #and candash: #TODO IDK what it means to not be able to dash. does DD not handle being in the air? 
            # Dash dance at our opponent
            self.chain = None
            self.pickchain(Chains.DashDance, [opponent_state.position.x])
            return

        neutral = smashbot_state.action in [Action.STANDING, Action.DASHING, Action.TURNING, \
            Action.RUNNING, Action.EDGE_TEETERING_START, Action.EDGE_TEETERING]

        facingopponent = smashbot_state.facing == (smashbot_state.position.x < opponent_state.position.x)

        # TODO IDK what I'm doing here either
        if not facingopponent:
            self.pickchain(Chains.DashDance, [opponent_state.position.x])
            return
        # If we're turning, then any action will turn around, so take that into account
        if smashbot_state.action == Action.TURNING:
            facingopponent = not facingopponent

        # Check grab as it's the smallest distance
        if ingrabrange:
            self.pickchain(Chains.GrabAndThrow, [THROW_DIRECTION.DOWN])
            return

        # Gentleman if we're spaced pretty far from the opponent
        if injabrange and canjab and gamestate.distance > 18:
            self.pickchain(Chains.Gentleman)
            return

        # Really this is in areial range
        if inrange:
            # Randomly UAIR about 0.25% of the time instead of knee to throw off timing
            # Uair is +-0 on sheild so still good, and with much different hitlag and stun
            if random.randint(0, 4) == 0:
                self.pickchain(Chains.Shffl, [SHFFL_DIRECTION.UP, LOW_HITBOX.YES])
            else:
                self.pickchain(Chains.Shffl, [SHFFL_DIRECTION.FORWARD, LOW_HITBOX.YES])
            return

        # If we fall through just DD
        self.chain = None
        self.pickchain(Chains.DashDance, [opponent_state.position.x])
