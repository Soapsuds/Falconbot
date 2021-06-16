import melee
import Tactics
import random
from melee.enums import Action, Button
from Strategies.strategy import Strategy
from Tactics.punish import Punish
from Tactics.pressure import Pressure
from Tactics.defend import Defend
from Tactics.recover import Recover
from Tactics.mitigate import Mitigate
from Tactics.edgeguard import Edgeguard
from Tactics.juggle import Juggle
from Tactics.celebrate import Celebrate
from Tactics.wait import Wait
from Tactics.retreat import Retreat
from Tactics.selfdestruct import SelfDestruct
from Tactics.approach import Approach
from Tactics.test import Test

class Test(Strategy):
    def __init__(self, logger, controller, framedata, difficulty):
        self.approach = False
        self.approach_frame = -123
        self.logger = logger
        self.controller = controller
        self.framedata = framedata
        self.set_difficulty = difficulty
        self.difficulty = 4

    def __str__(self):
        string = "Test"

        if not self.tactic:
            return string
        string += str(type(self.tactic))

        if not self.tactic.chain:
            return string
        string += str(type(self.tactic.chain))
        return string

    def step(self, gamestate, smashbot_state, opponent_state):
        self._propagate  = (gamestate, smashbot_state, opponent_state)

        # -1 means auto-adjust difficulty based on stocks remaining
        if self.set_difficulty == -1:
            self.difficulty = smashbot_state.stock
        else:
            self.difficulty = self.set_difficulty

        if SelfDestruct.shouldsd(gamestate, smashbot_state, opponent_state):
            self.picktactic(Tactics.SelfDestruct)
            return

        # Reset the approach state after 1 second
        #   Or if opponent becomes invulnerable
        if self.approach and ((abs(self.approach_frame - gamestate.frame) > 60) or (opponent_state.invulnerability_left > 0)):
            self.approach_frame = -123
            self.approach = False

        # Randomly approach sometimes rather than keeping distance
        # Should happen on average once per 2 seconds
        # The effect will last for about 1 second
        # On the first two difficulties, just always approach
        if (random.randint(0, 120) == 0 or self.difficulty >= 4) and (opponent_state.invulnerability_left == 0):
            self.approach = True
            self.approach_frame = gamestate.frame

        if self.logger:
            self.logger.log("Notes", " approach: " + str(self.approach) + " ", concat=True)

        if Mitigate.needsmitigation(smashbot_state):
            self.picktactic(Tactics.Mitigate)
            return

        if self.tactic and not self.tactic.isinteruptible():
            self.tactic.step(gamestate, smashbot_state, opponent_state)
            return

        # If we're stuck in a lag state, just do nothing. Trying an action might just
        #   buffer an input we don't want
        if Wait.shouldwait(gamestate, smashbot_state, opponent_state, self.framedata):
            self.picktactic(Tactics.Wait)
            return

        if Recover.needsrecovery(smashbot_state, opponent_state, gamestate):
            self.picktactic(Tactics.Recover)
            return

        self.picktactic(Tactics.KeepDistance)
        return

