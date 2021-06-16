import melee
from melee.enums import Action, Button
from Chains.chain import Chain
from enum import Enum

class SHFFL_DIRECTION(Enum):
    UP = 0
    DOWN = 1
    FORWARD = 2
    BACK = 3
    NEUTRAL = 4

class LOW_HITBOX(Enum):
    YES = True
    NO = False

class Shffl(Chain):
    def __init__(self, direction=SHFFL_DIRECTION.DOWN, lowhitbox=False):
        self.direction = direction
        self.lowhitbox = lowhitbox
        self.lcanelactions = [Action.UAIR_LANDING, Action.BAIR_LANDING, Action.DAIR_LANDING, Action.UAIR_LANDING]

    def step(self, gamestate, smashbot_state, opponent_state):
        controller = self.controller

        # If we're stuck in landing lag, chill. We can wait until the last frame and then intterupt
        if smashbot_state.action in self.lcanelactions:
            if smashbot_state.action == Action.UAIR_LANDING:
                if smashbot_state.action_frame < 26:
                    controller.empty_input()
                    return
            if smashbot_state.action == Action.FAIR_LANDING:
                if smashbot_state.action_frame < 27:
                    controller.empty_input()
                    return
            if smashbot_state.action == Action.DAIR_LANDING:
                if smashbot_state.action_frame < 28:
                    controller.empty_input()
                    return
            if smashbot_state.action == Action.BAIR_LANDING:
                if smashbot_state.action_frame < 27:
                    controller.empty_input()
                    return
            # Once we've made sure we waited until the last frame go ahead and mark interruptible
            # TODO we probably don't need to do this, I'm pretty sure either the strat or tact checks
            # for landing lag :/
            self.interruptible = True
            return

        # If we're in hitlag go ahead and input an Lcancel
        if smashbot_state.hitlag_left:
            controller.press_button(Button.BUTTON_Z)
            return

        # Likewise, if we've flown offstage interrupt
        if self.framedata.is_attack(smashbot_state.character, smashbot_state.action):
            if self.framedata.iasa(smashbot_state.character, smashbot_state.action) == smashbot_state.action_frame:
                self.interruptible = True
                return

        # If we're in knee bend, let go of jump and move toward opponent
        if smashbot_state.action == Action.KNEE_BEND and smashbot_state.action_frame <= 3:
            self.interruptible = False
            controller.release_button(Button.BUTTON_Y)
            jumpdirection = 1
            if opponent_state.position.x < smashbot_state.position.x:
                jumpdirection = 0
            controller.tilt_analog(Button.BUTTON_MAIN, jumpdirection, .5)
            return
        # If we're going for an early aerial we should start it on the last frame of jump squat
        # Even if we're not though if we're doing stomp or nair we should start it ASAP
        elif smashbot_state.action == Action.KNEE_BEND and smashbot_state.action_frame == 4 and (not self.lowhitbox or self.direction == SHFFL_DIRECTION.DOWN or self.direction == SHFFL_DIRECTION.NEUTRAL): 
            if self.direction == SHFFL_DIRECTION.DOWN:
                controller.tilt_analog(Button.BUTTON_C, .5, 0)
            if self.direction == SHFFL_DIRECTION.NEUTRAL:
                controller.press_button(Button.BUTTON_A)
                controller.tilt_analog(Button.BUTTON_MAIN, .5, .5)
            if self.direction == SHFFL_DIRECTION.UP:
                controller.tilt_analog(Button.BUTTON_C, .5, 1)
            if self.direction == SHFFL_DIRECTION.FORWARD:
                controller.tilt_analog(Button.BUTTON_C, int(smashbot_state.facing), .5)
            if self.direction == SHFFL_DIRECTION.BACK:
                controller.tilt_analog(Button.BUTTON_C, int(not smashbot_state.facing), .5)
            return

        # If we're on the ground, but NOT in knee bend, then jump
        if smashbot_state.on_ground and not smashbot_state.action == Action.KNEE_BEND:
            if controller.prev.button[Button.BUTTON_Y]:
                self.interruptible = True
                controller.empty_input()
            else:
                self.interruptible = False
                controller.press_button(Button.BUTTON_Y)
            return


        # Set X to either drift towards the opponent or the stage
        x = 0.5
        edge_x = melee.stages.EDGE_GROUND_POSITION[gamestate.stage]
        if opponent_state.position.x < 0:
            edge_x = -edge_x
        edgedistance = abs(edge_x - smashbot_state.position.x)
        if edgedistance < 25:
            x = int(smashbot_state.position.x < 0)
        else:
            if smashbot_state.position.x < opponent_state.position.x:
                x = 1
            else:
                x = 0

        # If we're falling, then press down hard to do a fast fall, and press Z to L cancel
        # 0.1 because Falcon should reach 0.08 the frame before going (-)
        # we fast fall the frame before to go to -3.5 immediately
        # Nair won't come out unless we wait one additional frame to FF
        if smashbot_state.speed_y_self < 0.1:
            self.interruptible = False
            if not self.direction == SHFFL_DIRECTION.NEUTRAL:
                controller.tilt_analog(Button.BUTTON_MAIN, x, 0)
            # If we're FFing already we can set y to neutral to get better drift
            if smashbot_state.speed_y_self < -3:
                controller.tilt_analog(Button.BUTTON_MAIN, x, 0.5)
            # Upair should be input on the same frame as FF
            if self.direction == SHFFL_DIRECTION.UP:
                controller.tilt_analog(Button.BUTTON_C, 0.5, 1)
            # Only do the L cancel near the end of the animation
            if smashbot_state.action_frame >= 17:
                controller.press_button(Button.BUTTON_Z)
            return

        # If we're airborn we better be doing an attack unless lowhitbox is true
        if not self.framedata.is_attack(smashbot_state.character, smashbot_state.action):
            if not self.lowhitbox:
                raise ValueError("Falcon should have thrown out an attack by now!")
            # If the C stick wasn't set to middle, then
            if controller.prev.c_stick != (.5, .5):
                controller.tilt_analog(Button.BUTTON_C, .5, .5)
                return
            # Stomp and Nair are always done asap
            # Uair is done at the same time we FF
            # Knee should be started 6 frames into the jump
            if self.direction == SHFFL_DIRECTION.FORWARD:
                if smashbot_state.action_frame == 6:
                    controller.tilt_analog(Button.BUTTON_C, int(smashbot_state.facing), .5)
                    return
            # Bair should be done 10 frames into the jump
            if self.direction == SHFFL_DIRECTION.BACK:
                if smashbot_state.action_frame == 10:
                    controller.tilt_analog(Button.BUTTON_C, int(not smashbot_state.facing), .5)
                    return

        if self.framedata.is_attack(smashbot_state.character, smashbot_state.action):
            # While we're in the air either point towards the stage or the opponent
            # If we're close to the edge, angle back in
            controller.tilt_analog(Button.BUTTON_MAIN, x, .5)
            return

        self.interruptible = True
        controller.empty_input()
