import melee
import Chains
from melee.enums import Action, Button, Character
from Tactics.tactic import Tactic
from Tactics.punish import Punish
from Chains.gentleman import Gentleman
from Chains.edgestall import Edgestall
from Chains.shffl import Shffl
from Chains.shffl import SHFFL_DIRECTION

class Test(Tactic):
    def step(self, gamestate, smashbot_state, opponent_state):
        self._propagate  = (gamestate, smashbot_state, opponent_state)
        #If we can't interrupt the chain, just continue it
        if self.chain != None and not self.chain.interruptible:
            self.chain.step(gamestate, smashbot_state, opponent_state)
            return

        needswavedash = smashbot_state.action in [Action.DOWN_B_GROUND, Action.DOWN_B_STUN, \
            Action.DOWN_B_GROUND_START, Action.LANDING_SPECIAL, Action.SHIELD, Action.SHIELD_START, \
            Action.SHIELD_RELEASE, Action.SHIELD_STUN, Action.SHIELD_REFLECT]
        if needswavedash:
            self.pickchain(Chains.Wavedash)
            return
        shieldactions = [Action.SHIELD_START, Action.SHIELD, Action.SHIELD_STUN, Action.SHIELD_REFLECT]

        if opponent_state.action in shieldactions:
            print("Trying to Knee")
            self.pickchain(Chains.Shffl, [SHFFL_DIRECTION.FORWARD, True])
            return

        if opponent_state.action == Action.JUMPING_FORWARD:
            print("Trying to Uair")
            self.pickchain(Chains.Shffl, [SHFFL_DIRECTION.UP])
            return

        if opponent_state.action == Action.JUMPING_BACKWARD:
            print("Trying to Bair")
            self.pickchain(Chains.Shffl, [SHFFL_DIRECTION.BACK])
            return

        if abs(opponent_state.position.x - smashbot_state.position.x) < 30:
            print("Trying to Stomp")
            self.pickchain(Chains.Shffl, [SHFFL_DIRECTION.DOWN, True])
            return

        if opponent_state.action == Action.DASHING:
            print("Trying to Nair")
            self.pickchain(Chains.Shffl, [SHFFL_DIRECTION.NEUTRAL])
            return


#        if smashbot_state.action == Action.EDGE_CATCHING or smashbot_state.action == Action.EDGE_HANGING or smashbot_state.action == Action.FALLING:
#            self.pickchain(Chains.Edgestall)
#            return
#
#        if opponent_state.action == Action.CROUCHING:
#            self.pickchain(Chains.Grabedge)
#            return
        

        self.pickchain(Chains.Nothing)
