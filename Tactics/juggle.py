import melee
import Chains
from melee.enums import Action, Character
from Tactics.tactic import Tactic
from Chains.tilt import TILT_DIRECTION
from Chains.shffl import SHFFL_DIRECTION
from Chains.grabandthrow import GrabAndThrow
from Chains.grabandthrow import THROW_DIRECTION
from Chains.airattack import AirAttack, AIR_ATTACK_DIRECTION
from Chains.goto_x import GotoX
from Tactics.punish import Punish
from Tactics.infinite import Infinite
from melee.enums import Character
from melee.enums import Stage

class Juggle(Tactic):
    def __init__(self, logger, controller, framedata, difficulty):
        Tactic.__init__(self, logger, controller, framedata, difficulty)

    def canjuggle(smashbot_state, opponent_state, gamestate, framedata, difficulty):
        if opponent_state.invulnerability_left > 0:
            return False

        # If the opponent is in hitstun, in the air
        if (not opponent_state.on_ground) and (opponent_state.hitstun_frames_left > 0):
            if not framedata.is_attack(opponent_state.character, opponent_state.action):
                end_x, end_y, frames_left = framedata.project_hit_location(opponent_state, gamestate.stage)
                edge_x = melee.stages.EDGE_POSITION[gamestate.stage]
                if end_y > -5 and end_y < 75 and abs(end_x) < edge_x + 20:
                    return True 

        # If opponent is rolling and we can start a juggle combo from it
        if framedata.is_roll(opponent_state.character, opponent_state.action):
            return True

        return False

    def step(self, gamestate, smashbot_state, opponent_state):
        self._propagate  = (gamestate, smashbot_state, opponent_state)

        # If we can't interrupt the chain, just continue it
        if self.chain != None and not self.chain.interruptible:
            self.chain.step(gamestate, smashbot_state, opponent_state)
            return

        # figure out where they will be at the end of hitstun
        end_x, end_y, frames_left = self.framedata.project_hit_location(opponent_state, gamestate.stage)

        if self.framedata.is_roll(opponent_state.character, opponent_state.action):
            end_x = self.framedata.roll_end_position(opponent_state, gamestate.stage)
            frames_left = self.framedata.last_roll_frame(opponent_state.character, opponent_state.action) - opponent_state.action_frame

        facing_away = (smashbot_state.position.x < end_x) != smashbot_state.facing
        if smashbot_state.action == Action.TURNING and smashbot_state.action_frame == 1:
            facing_away = not facing_away

        on_ground = opponent_state.on_ground or opponent_state.position.y < 1 or opponent_state.action in [Action.TECH_MISS_UP, Action.TECH_MISS_DOWN]

        if self.logger:
            self.logger.log("Notes", " Predicted End Position: " + str(end_x) + " " + str(end_y) + " ", concat=True)
            self.logger.log("Notes", " on_ground: " + str(on_ground), concat=True)
            self.logger.log("Notes", " frames left: " + str(frames_left) + " ", concat=True)

        if not on_ground:
            # First off a couple of fail safe's if we get really close to the end of hitstun
            # Check if we can gentleman
            if not facing_away and frames_left < 6 and frames_left > 2 and end_y > 0 and end_y < 10 and abs(smashbot_state.position.x - opponent_state.position.x) < 10:
                if smashbot_state.action in [Action.STANDING, Action.TURNING]:
                    print("Thought jab was a good idea")
                    self.chain = None
                    self.pickchain(Chains.Gentleman)
                    return

            # Check if we can grab them
            if not facing_away and frames_left < 8 and frames_left > 6 and end_y > 3 and end_y < 10 and abs(smashbot_state.position.x - opponent_state.position.x) < 8:
                self.chain = None
                print("Thought grab was a good idea")
                if opponent_state.percent > 20 and opponent_state.percent < 73:
                    self.pickchain(Chains.GrabAndThrow, [THROW_DIRECTION.UP])
                else:
                    self.pickchain(Chains.GrabAndThrow, [THROW_DIRECTION.DOWN])
                return

            # First we'll see if we can get right under them.
            # This will increase the success rate of our aerials and make the logic easier, but we need to have a lot of time so we don't
            # miss the opportunity to get a big hit 
            if abs(melee.stages.EDGE_POSITION[gamestate.stage]) > abs(end_x):
                if abs(smashbot_state.position.x - end_x) > 10:
                    if end_y > 50 and frames_left > 42:
                        if Chains.GotoX.frame_commitment(smashbot_state, end_x) < 8:
                            if self.logger:
                                self.logger.log("Notes", "HIGH frame_commitment: " + str(Chains.GotoX.frame_commitment(smashbot_state, end_x)) + "end pos: " + str(end_x))
                            self.chain = None
                            self.pickchain(Chains.GotoX, [end_x])
                            return
                    if end_y > 10 and frames_left > 30:
                        if GotoX.frame_commitment(smashbot_state, end_x) < 8:
                            if self.logger:
                                self.logger.log("Notes", "LOW frame_commitment: " + str(Chains.GotoX.frame_commitment(smashbot_state, end_x)) + "end pos: " + str(end_x))
                            self.chain = None
                            self.pickchain(Chains.GotoX, [end_x])
                            return

            # If we're far away from the opponent and couldn't get right under just start dashing towards them
            if abs(smashbot_state.position.x - end_x) > 10 and abs(smashbot_state.speed_ground_x_self) < 1.7 and abs(end_x) < melee.stages.EDGE_GROUND_POSITION[gamestate.stage]:
                print("Started running!")
                x = 1
                if smashbot_state.position.x > end_x:
                    x = 0
                self.chain = None
                self.pickchain(Chains.Run, [x])
                return

            # Check if we can possibly get to where they'll end up laterally
            delta_x = abs(smashbot_state.position.x - end_x)
            max_dist = 2.1 * (frames_left + 2) + 10 # Uair hits well in front of us
            if max_dist > delta_x:
                # Let's see what the biggest move we can get off is
                # UP = 0
                # DOWN = 1
                # FORWARD = 2
                direction = None
                height_level = None
                attk_commitment = None
                prefer_knee = opponent_state.percent > 55
                tried_early = False
                early_x = None
                early_y = None
                early_frames_left = None
                # Figure out an attack to do
                while direction == None and tried_early == False:
                    for i in [AIR_ATTACK_DIRECTION.UP, AIR_ATTACK_DIRECTION.FORWARD, AIR_ATTACK_DIRECTION.DOWN]:
                        if i == AIR_ATTACK_DIRECTION.UP:
                            bottom_offset = 11
                            top_offset = 26
                        if i == AIR_ATTACK_DIRECTION.FORWARD:
                            bottom_offset = 2
                            top_offset = 14
                        if i == AIR_ATTACK_DIRECTION.DOWN:
                            bottom_offset = -10
                            top_offset = 14
                        print("Considering Aerial ", i)
                        if early_x != None and early_y != None and early_frames_left != None:
                            end_x = early_x
                            end_y = early_y
                            frames_left = early_frames_left
                            tried_early = True
                        viableheightlevels = []
                        for hl in AirAttack.height_levels():
                            attk_y = AirAttack.attack_height(hl)
                            top_hb = attk_y + top_offset
                            bot_hb = attk_y + bottom_offset
                            print("Calculated top_hb: ", top_hb, "bot_hb: ", bot_hb, "end_y: ", end_y)
                            if end_y < top_hb and end_y > bot_hb:
                                print("added ", hl, "to viable height levels")
                                viableheightlevels.append(hl)

                        for hl in viableheightlevels:
                            attk_commitment = AirAttack.frame_commitment(hl, i)
                            # Check if the height level still makes sense
                            # Using our double jump will lower our max speed to 1.1. Check if we'll still catch the target
                            uses_dj = AirAttack.uses_dj(height_level, i)
                            if uses_dj:
                                max_dist = 1.1 * frames_left
                            if max_dist < delta_x:
                                continue # skip to next check
                            # Prefer harder hitting moves
                            print("Uses DJ: ", uses_dj, "attk_commit: ", attk_commitment, "Height_level: ", hl, "Current direction: ", direction)
                            # Usually we have some wiggle room since marth can't do anything for the first couple frames
                            # However, if he's going to be able to tech we do not
                            extraframes = 2
                            if end_y < 0:
                                extraframes = 0
                            if attk_commitment <= frames_left + extraframes:
                                if direction == None:
                                    print("Picked new direction. Old direction was: ", direction, "new: ", i, "HL: ", hl)
                                    direction = i
                                    height_level = hl
                                if direction == AIR_ATTACK_DIRECTION.UP and i == AIR_ATTACK_DIRECTION.FORWARD:
                                    print("Picked new direction. Old direction was: ", direction, "new: ", i, "HL: ", hl)
                                    direction = i
                                    height_level = hl
                                if direction == AIR_ATTACK_DIRECTION.FORWARD and i == AIR_ATTACK_DIRECTION.DOWN and not prefer_knee: 
                                    print("Picked new direction. Old direction was: ", direction, "new: ", i, "HL: ", hl)
                                    direction = i
                                    height_level = hl
                    # Now that we've exhausted all of the end_x,y possibilities if we haven't found a direction try early areials
                    # TODO we would need 18 frames to knee. This just checks for early uairs rn
                    if direction == None and tried_early == False:
                        print("NO DIRECTION FOUND,  CHECKING EARLY AERIALS NOW")
                        early_x, early_y, early_frames_left = self.framedata.project_hit_location(opponent_state, gamestate.stage, 12)
                        print("Early end_x:", early_x, "Early end_y:", early_y, "frames:", early_frames_left)
                    

                # we found an attack to do
                if attk_commitment and direction:
                    print("OUTSIDE OF LOOP", "knee=", prefer_knee, "attk direction", direction, "Commit: ", attk_commitment, "Frames Left: ", frames_left, "End y: ", end_y, "Picked height level: ", height_level)
                    # we might not have to do it yet though
                    # calculate at frameoffset
                    if end_y < 2:
                        print("used offset of 1 per y < 2")
                        offset = 1
                    elif end_y > 20 and direction == AIR_ATTACK_DIRECTION.FORWARD:
                        offset = 1
                    else:
                        offset = 3 
                    if frames_left > attk_commitment + offset:
                        print("WAITING")
                        # if we're close and they're not moving quickly just stop 
                        if abs(smashbot_state.position.x - end_x) < 10:
                            if smashbot_state == Action.DASHING:
                                self.chain = None
                                self.pickchain(Chains.Stop)
                                return
                            elif frames_left - attk_commitment >= 15:
                                self.chain = None
                                self.pickchain(Chains.Wavedash, [0])
                                return
                        # if we're far dash/run towards it
                        else:
                            self.chain = None
                            if smashbot_state.position.x > end_x:
                                x = 0
                            else:
                                x = 1
                            self.pickchain(Chains.DashDance, [end_x])
                            return
                    # Okay time to call airattack
                    else:
                        print("passed it off to airattack")
                        self.chain = None
                        self.pickchain(Chains.AirAttack, [end_x, end_y, height_level, direction])
                        return
            # opponent speed is > 1.8 or end_y < 3 
            else:
                self.chain = None
                edge_x = melee.stages.EDGE_POSITION[gamestate.stage]
                if abs(end_x) > edge_x:
                    self.pickchain(Chains.Grabedge)
                else:
                    print("failed check for grab edge for some reason, dd instead")
                    self.pickchain(Chains.DashDance, [end_x])
                return
        else: # (opponent is on_ground)
            if self.framedata.is_roll(opponent_state.character, opponent_state.action):
                print("Detected opponent on ground")
                # Raptorboost is a fun option, but we don't want to do it if they're too low %
                if frames_left > 25 and abs(smashbot_state.position.x - end_x) < 20 and opponent_state.percent > 60:
                    self.chain = None
                    self.pickchain(Chains.Raptorboost, [int(smashbot_state.position.x < end_x)])
                    return
                # If we've got a lot of time and we're not moving already just run towards the correct spot
                if frames_left > 20 and abs(smashbot_state.position.x - end_x) > 20 and abs(smashbot_state.speed_ground_x_self) < 1.7 and abs(end_x) < melee.stages.EDGE_GROUND_POSITION[gamestate.stage]:
                    x = 1
                    if smashbot_state.position.x > end_x:
                        x = 0
                    self.chain = None
                    self.pickchain(Chains.Run, [x])
                    return
                    
                # TODO 13 is the fastest getup attack of the legal character, do a lookup for the actual one
                if opponent_state.action in [Action.TECH_MISS_UP, Action.TECH_MISS_DOWN]:
                    frames_left += 13

                # Stomp if we have a shit ton of time and are in range and they won't be invincible
                if frames_left >= 20 and frames_left < 25 and gamestate.distance < 40: 
                    self.chain = None
                    self.pickchain(Chains.AirAttack, [end_x, 10, 1, AIR_ATTACK_DIRECTION.DOWN])
                    return
                # Knee if stomp won't come out fast enough
                if 14 <= frames_left < 20 and gamestate.distance < 40:
                    self.chain = None
                    self.pickchain(Chains.AirAttack, [end_x, 10, 1, AIR_ATTACK_DIRECTION.FORWARD])
                    return
                # Just nair towards them
                if 10 <= frames_left < 14 and gamestate.distance < 30:
                    self.chain = None
                    self.pickchain(Chains.Shffl, [Shffl.SHFFL_DIRECTION.NEUTRAL])
                # Grab them
                if 7 <= frames_left <= 9:
                    if opponent_state.action not in [Action.TECH_MISS_UP, Action.TECH_MISS_DOWN] and gamestate.distance < 10:
                        self.pickchain(Chains.GrabAndThrow, [THROW_DIRECTION.UP])
                        return
                # Gentleman missed tech
                if 3 <= frames_left <= 5:
                    if gamestate.distance < 8:
                        self.pickchain(Chains.Gentleman)
                        return

        print("fell off punish function, resorting to dd")
        self.chain = None
        self.pickchain(Chains.DashDance, [end_x])
