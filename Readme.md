# FalconBot
###### The AI that I forked from smashbot.

##### Falconbot plays Falcon in Super Smash Brother's Melee for the Nintendo Game Cube. He may or may not beat you.

#### Video Demo (CS50):  https://youtu.be/xvpkZfp1-As

### FAQ

1. **What character does FalconBot play?**

    Falcon, of course!

2. **Does SmashBot work with Slippi?**

    It does! To run SmashBot, you can just use your regular Slippi Dolphin install.

3. **What's different from smashbot?**
    
    Well, I cooked up a few new chains and implemented the punish game completely differently

4. **Can I actually play against it?**
    Yes, but it's not programmed to throw out any moves ever. Unless you attack it all it does is dash dance on your current position. 
    He also only plays vs Marth on FD

#### CS50 Project Information
This project is forked from smashbot so the structure is inherited and some of the code is shared. 
What I've done is modified it such that it can play Falcon instead of Fox. The first thing I implemented was
the gentleman chain (Chains/gentleman.py) in this file we inherit and extend the chain class, and also
take in the gamestate. Gentleman keeps track of 3 variables, goodrelease1-3. A good release means it let go
of A at the correct time. Knowing how many good releases we have branches the logic for going from
jab 2 and 3. Other than the initialized variables a chain is sort of stateless in a way. A chain is called
into on each frame so you must analyze the gamestate to decide what to do. Gentleman keeps track of of a few
different actions and groups them together at the stop of the step function. gentactions is a list that 
contains the actions that were started by this chain. canjab contains a list of actions we can start the
chain out of. Finally, rapidjabs is a list that contains the actions we would enter if a mistake is made.
After creating the lists of actions we're looking for we branch out and decide what buttons to press 
depending on our current action. The first thing we check is if we have made a mistake, in which case
we let the higher level strategy know that we no longer have to iterate over this chain. If we're in a 
position to start a jab we can just press A. And if we're not we don't press anything. Next we check if
it's the correct time to release A, and flag a good release on jab 1, 2 or 3 if it was. Then we check if 
we have enough good releases, and if we don't, we walk out of the second jab instead of inputing the next 
one right away. If the chain enters while in the third hit it might be time to stop the chain as well. 
After the third hit connects we can do something else.

The next chains I worked on were grabedge and ledgedash (Chains.grabedge.py, Chains.ledgedash.py). The
same logic applies to these, however the inputs are much different. A challenge during this project was 
detecting and inputing the correct action for each state. The states started from the chain are easy to 
implement, but the chains can be called from anywhere. Detecting when a chain like grabedge has been called
at a time where the inputs we might start out with in a normal situation would kill us instead was quite
challenging (and as seen in the video not completely worked out)

The commit log for this project is empty because I moved it over from another folder before I made it public
as I had mistakenly been commiting some of my personal notes about the project's state along the way that I 
didn't want to make public. However if the grading team would like access to the full repository I would
be happy to provide it. For now I've dumped the gitlog from the other repo into a txt file at the top level
called oldgitlog.txt That has a list of the other chains I worked on.

The bulk of my time was spent on the AirAttack chain (Chains/airattack.py) and the juggle Tactic (Tactics/juggle.py). This is what allows the bot to keep hitting once it has the opponent in the air and the part of the
project I think might be useful to it's Fox playing upstream. I modified AirAttack with quite a few helper 
functions. Most notably get_jump_direction and get_drift_direction. These functions take into consideration
the ground speed of the bot, which move it's doing, and where the opponent is going to end up in order to
figure out how to adjust it's momentum in order to line up with the opponent at just the right time.
Once we get into the step function the code branches many times off of each action depending on the 
height of the target and which attack it's doing. 

Juggle was maybe the most challenging part. Getting the airattack chain to always line up with the opponent
was difficult, but it's the job of juggle to make sure that it's possible and a good idea. Starting at line
84 we know the opponent is in the air and has some amount of hitstun left. The first check we make is
if the opponent will end up above the stage after hitstun. If they will, and we have a lot of time left, we
call the GotoX chain to take us there laterally. Tactics, like chains, are called into from the top 
at every frame. GotoX will block juggle from picking a new chain until the bot is standing about where we told
it to go though, so we don't have to worry about overwriting that action. We do however check how far we are
and if we're close we won't call GotoX again. 

The next part (starting at line 105) checks our position and our speed. If we're close we must have used gotox
to get right under them, or they popped up right above our heads. If we're not very close we want to start
moving in their direction. Then we check for speed. If we've already starting running towards them maybe
there is something else we can do.

The next (massive) block of code (starting form 115) will get called if we are either right under the opponent
or traveling towards them. We run a check using the best possible numbers to see if there's a chance of us 
being able to hit them. If there is we run a couple loops until we find an attack to do that will work (lines
131 - 195). After we've found an attack to do we need to make sure we don't start it too early. We've been
checking the position of where they will end up at the end of hitstun, so they could still be flying through
the air. If they are we need to wait, either by getting under them or just stopping in place.

I hope that's a good walkthrough of some of the files in my project and gives some insight into how it works.
Thanks! 
