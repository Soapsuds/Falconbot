import melee
import Chains
from melee.enums import Action
from Tactics.tactic import Tactic
from Chains.smashattack import SMASH_DIRECTION
from Tactics.punish import Punish
from melee.enums import Character
from melee.enums import Stage

# Keeping this in for now to see where it gets called and for kill%
# OBV Falcon doesn't have an infinite

class Infinite(Tactic):
    def __init__(self, logger, controller, framedata, difficulty):
        Tactic.__init__(self, logger, controller, framedata, difficulty)

    def killpercent(stage, character):
        percent = 100
        if character == Character.CPTFALCON:
            percent = 113
        if character == Character.FALCO:
            percent = 103
        if character == Character.FOX:
            percent = 96
        if character == Character.SHEIK:
            percent = 92
        if character == Character.PIKACHU:
            percent = 73
        if character == Character.PEACH:
            percent = 80
        if character == Character.ZELDA:
            percent = 70
        if character == Character.MARTH:
            percent = 89
        if character == Character.JIGGLYPUFF:
            percent = 55
        if character == Character.SAMUS:
            percent = 89

        # Dreamland is big
        if stage == Stage.DREAMLAND:
            percent += 20
        return percent

    def caninfinite(smashbot_state, opponent_state, gamestate, framedata, difficulty):
        return False


    def step(self, gamestate, smashbot_state, opponent_state):
        self._propagate  = (gamestate, smashbot_state, opponent_state)

        print("UH OH, tried to infinite")
        return
