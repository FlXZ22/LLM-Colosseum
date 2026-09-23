# DEVLOG

## Day 1
I implemented the simplest working engine, with 2 agents that do actions at random.

## Day 2
I improved the engine with validation, death by hunger and health, and what each action does.

## Day 3
I implemented the encounter option: when 2 agents are in the same area, they can choose to attack, ignore, or flee.

## Day 4
I implemented what each action does. Attack starts a fight that one side can win; ignore and flee got their own separate behaviour.

## Day 5
I implemented the combat formula that makes the game less random, then added some randomness on top of it. I used a new `match`/`case` structure to make the code simpler and more effective. I also made the game run until only one agent is left standing on the battleground.

## Day 6
I implemented the seeded random function, so we can recreate a game from the same seed value.

## Day 7
I implemented JSON exporting of the whole game, and later transformed it into JSON Lines so it is easier to work with. I learnt about the JSON functions, `json.dump()`, etc.

## Day 8
I added a new way to choose an action. It is simpler because all the actions live in one place: to see whether an action is available we just use `get_available_actions()`, plus helpers like `is_legal()`.

I also fixed the JSONL on this day — then modified it again on a later day. LOL

## Day 9
I implemented the events (really, refined them), changed how the hide action works, and created a `config` folder where we can tweak all the parameters. For example, if we want to change how much damage is dealt when you lose a fight, we just edit a variable in `balance.py` inside the `config` directory.

## Day 10
I added a tiny inventory to the agent in `agent.py` and connected it to the config file (I added the values there). I basically did Day 10, Day 11, and Day 12 in one sitting.

## Day 11
I added medicine, and made it so that an agent can use that item to heal when the item is a medicine.

## Day 12
I added a weapon inventory, wrote it into the record log when the agents attack each other, and made it affect an agent's combat value.

## Day 13
Today is the first of September and I wrote the perception layer in Python. What it does is show the agent the status of its health, stamina, and hunger. It does not show numeric values — it shows text values from a set of functions we wrote: with if/else conditions we assign a text value (for example "badly hurt", "hurt", "bruised") to different levels of health, hunger, and stamina.

We created a `to_prompt` function that gives the agent a status report: its name, how its health is, whether anyone else is in the room, what items it has, and so on. `to_prompt` lives inside the `Observation` class, because the `Observation` class is basically what the agent sees — the agent only gets what is in `to_prompt`. The `Observation` is filled by the `observe` function, which sits outside the class and completes it.

On top of that we have separate functions that convert health, hunger, and stamina into text, and another function that tells the agent how it sees the other agents in the same area. There is also a location description: each location has variables for danger (how dangerous the place is), food, and cover. In this version we did not use danger, because there is no mechanic for it yet, so I commented it out — in the future, to add danger, we can just remove the comment.

The only thing left to complete Week 2 is to write the test-case functions that check everything works. After that we move to Week 3, the week where we actually implement the real LLM, and we'll see how it goes.

# Day 14
I have finished the test cases and definitely finished the whole week 2. I wrote the unis test function all of them and verify that they work correctly and they do each test passed correctly and I definitely finished week 2 and I think this was very useless because no it wasn't useless because it was really cool to test everything okay what the test case okay I didn't give into that impression of writing it by AI but I still needed help from him because I don't know how to write unis test but he gave me how to do and I wrote following his instruction and they worked okay they work correctly and I understand how they work we test and we tested game events we tested that we tested inventory and we tested even game logics and we tested even the tester itself if it works.

# day 15
on this day we have build a personality layer for the llm using the OCEAN principle, the way it works is that we have different traits, openness and 4 others and they can have a value in high, low and medium and other thing is we design a other layer on top with profiles, for now we have 3 total profiles: agressor, survivalist, diplomat, they have different names: Rocky, Flint, Mike.
and then i make the ai write a simple test case that I CAN UNDERSTAND!
