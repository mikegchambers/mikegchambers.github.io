---
title: "My Generative Adventure Game"
date: 2024-11-11
categories: [AI, Tutorials]
tags: [amazon-bedrock, agents, generative-ai, python, game-development]
description: "Build a text-based RPG adventure game powered by Amazon Bedrock generative AI with DnD-style mechanics. Full Python setup guide and code walkthrough."
---

> This article was originally published on the [AWS Builder Center](https://builder.aws.com/content/2ogvbYrb6RzMIvNX3ZvQIYSBa9j/my-generative-adventure-game).

Introducing "The Adventure Game", an unoriginal title for a game I wrote for this November's "AWS Game Builder Challenge". It's a text based, open ended, RPG (role playing game), and while I mainly wrote it to experiment with some application architecture concepts, I found that I really enjoyed playing it, and so have a few others who have tried it out.

The game is designed as a base from which to experiment. Either through playing the game, or making some adjustments to the code. How far you go, is up to you, your interests and the time you have available.

This post is split in to several different sections. First I will outline the simple idea behind the game mechanics. Then I will walk through a level 100 of how to get the game up and running on your machine. I will then move on to a level 200 of how to make some adjustments, a level 300 of how the game state actually works, and finally a level 400 walk through of making a significant change to the game mechanics.

If you enjoy this post, please give it a 👍 up above! Thanks!

The Game Concept
================

The Adventure Game (UNLIKE its 1980's BBC TV Show namesake), is an RPG, with similar basic mechanics as DnD (Dungeons and Dragons). The game itself takes the role of a story teller (or a DM) and will guide you through a unique story each time you play. The decisions YOU make and what YOU choose to do will influence the narrative as much as the story telling game. If you decide to try and throw the game by doing weird and non-obvious actions (what my family called "Deadpooling" :) ) then that is on you, and what ever happens next happens. I suggest, as with any RPG you play, is to mostly go along with the spirit of the story teller, and have fun. During the game, when an action is taken, the story teller may choose to roll a dice (or many dice) to allow some randomness to decide your fate.

When you start the game, you choose the scenario, and off you go. I enjoy playing "Space Wars" inspired games, but the choice is yours. Here is a sample of some game play:

![Space Pirate Wars with Dragons](https://assets.community.aws/a/2ogyGS2fz9jpIl7LbbcHhCHYHVK/Scre.webp?imgSize=1067x563)

### Note on Cost:

> Running this project will incur costs that are NOT covered by AWS Free Tier (and may not be covered by AWS credits). This project makes use of generative models through Amazon Bedrock, and depending on which model is used, the size of prompts and the number of turns, the cost will vary. This project is not intended to be a cost effective way to run a game. Please review the [Amazon Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/) page for more details.

### Note on Game Play (and Kids):

> This game uses generative AI, and as such the game state may not be consistent or predictable. Caution should be used when playing this game, especially with sensitive topics or allowing children to play. It is not recommended to enter private information or allow children to play without adult supervision.

Getting Started
===============

`123456TL:DR;- Set up a Python environment that runs AWS code.- Enable access to the LLM in the Amazon Bedrock console page.- Clone the Python repo.- From the code folder run pip install -r- Run main.py`

This game is written in Python, in simple text mode, so it can just run on your local machine, from the command line. The game uses AWS services specifically Amazon Bedrock for generative AI stuff, and if you want more detail on that, read this post to the end. If all you want to do is get started and play, then this is what you will need to do:

Setting Up Your Environment
===========================

1. Python Environment Setup
---------------------------

First, you'll need a Python environment that can work with AWS services. Here's how to set this up:

*   Install Python 3.8 or later if you haven't already. You can download it from [python.org](https://python.org/)
*   We recommend using a virtual environment to keep things clean:

`1python -m venv venv`

*   Activate your virtual environment:
*   On Windows:

`1venv\Scripts\activate`

*   On macOS/Linux:

`1source venv/bin/activate`

2. AWS Setup and Security
-------------------------

### Setting Up AWS Credentials

There are several ways to configure AWS credentials, but here's the most straightforward method for getting started:

1.   Create an AWS IAM User:

*   Sign in to the AWS Console as an administrator
*   Go to IAM (Identity and Access Management)
*   Create a new IAM User
*   Enable "Programmatic access" to get access keys

1.   Apply Least Privilege Access:

*   Create a custom policy that only allows access to Bedrock
*   Example minimal policy (save as JSON):

`123456789101112{  "Version": "2012-10-17",  "Statement": [    {      "Effect": "Allow",      "Action": [        "bedrock:InvokeModel"      ],      "Resource": "*"    }  ]}`

*   Attach this policy to your new IAM user

1.   Get Your Credentials:

*   After creating the user, you'll receive an Access Key ID and Secret Access Key
*   Save these somewhere secure - you won't be able to see the Secret Access Key again

1.   Configure Your Local Environment:

`1aws configure`

*   Enter your Access Key ID and Secret Access Key when prompted
*   Set your default region (e.g., us-east-1)
*   Set the output format to json

Security Notes:

*   Never commit AWS credentials to source control
*   Don't share your access keys
*   Consider using AWS IAM Identity Center (formerly AWS SSO) for enterprise environments
*   For production deployments, consider using IAM Roles instead of access keys
*   Regularly rotate your access keys
*   You can store credentials in environment variables if you prefer:

`123export AWS_ACCESS_KEY_ID=your_access_keyexport AWS_SECRET_ACCESS_KEY=your_secret_keyexport AWS_DEFAULT_REGION=your_region`

Alternative Setup Methods:

*   AWS CLI credentials file (~/.aws/credentials)
*   AWS IAM Identity Center
*   Environment variables
*   AWS SDK credential providers

3. AWS Bedrock Access
---------------------

The game uses Amazon Bedrock for its AI storytelling. You'll need to:

1.   Sign in to your AWS Console
2.   Navigate to the Amazon Bedrock console
3.   Click on "Model access" in the left navigation
4.   Find and enable the language model. _(Initially the game uses **Anthropic's Claude 3.5 Haiku**, but you can experiment with other models from Amazon Bedrock.)_
5.   Click "Save changes"

Note: You'll need an AWS account with appropriate permissions.

4. Get the Game Code
--------------------

There are two ways to get the code:

### Option 1: Clone with Git

If you have Git installed, you can clone the repository:

`12git clone https://github.com/build-on-aws/amazon-bedrock-adventure-game.gitcd amazon-bedrock-adventure-game`

### Option 2: Download ZIP File

If you're not familiar with Git:

1.   Visit the game's GitHub page at [https://github.com/build-on-aws/amazon-bedrock-adventure-game](https://github.com/build-on-aws/amazon-bedrock-adventure-game)
2.   Click the green "Code" button
3.   Select "Download ZIP"
4.   Extract the downloaded ZIP file to your preferred location
5.   Open a terminal/command prompt and navigate to the extracted folder

5. Install Dependencies
-----------------------

With your virtual environment activated, open your command line terminal, change to the project folder and install all required packages:

`1pip install -r requirements.txt`

This will install all necessary Python packages, including the AWS SDK (boto3) and other dependencies the game needs.

6. Run the Game
---------------

Now you're ready to play! Start the game by running:

`1python main.py`

Troubleshooting Common Issues
-----------------------------

If you encounter errors:

*   Ensure your virtual environment is activated
*   Verify your AWS credentials are properly configured
*   Check that you have enabled the correct model in Amazon Bedrock
*   Make sure all dependencies installed correctly

How The Game Works (Level 100)
==============================

![Lvl 100](https://assets.community.aws/a/2ogzF2A6qr2SjHFEZLQeDr464fn/adventure-game-100-jpg.webp?imgSize=1920x1080)

This game is a text adventure that uses AI to create an interactive story experience. While traditional text adventures use pre-written responses and fixed maps, this game creates the story dynamically using Amazon's Bedrock AI service. Here's a high-level overview of how it works:

The Basic Structure
-------------------

*   The game maintains a "world" using a graph structure where rooms connect to each other
*   Each room can contain:
    *   Objects that can be picked up
    *   NPCs (Non-Player Characters) to interact with
    *   Descriptions of what you see
    *   Exits to other rooms

The Game Loop
-------------

1.   You type in what you want to do (like "look around", "go north" or "slay the dragon!")
2.   The AI interprets your command and decides what should happen
3.   The AI uses an agent, and uses tools to:

*   Create or modify rooms
*   Move your character around
*   Add or remove objects
*   Control NPC

The AI's Role
-------------

The AI acts like a dungeon master in D&D - it:

*   Creates the story and environment
*   Controls how NPCs react to you
*   Decides what happens when you try to do something
*   Keeps track of what's possible and what isn't
*   Maintains a consistent world and story

Behind The Scenes
-----------------

The game uses several key components:

*   A game state manager that tracks where everything is
*   A tool system that lets the AI modify the game world
*   Amazon Bedrock to provide the AI capabilities
*   A simple command-line interface for player interaction

The beauty of this design is that the game world can adapt and change based on your actions, creating a unique story each time you play. While traditional text adventures follow a script, this game creates the adventure as you go, responding to your choices in creative ways.

Making Simple Changes (Level 200)
=================================

![Lvl 200](https://assets.community.aws/a/2ogzHjtOHiMUih5isUK5jyFBw2Q/adventure-game-200-jpg.webp?imgSize=1920x1080)

When I first started building this game, I wanted to make sure that anyone could customize it, whether they could code or not. That's why one of my favorite features is the system prompt - it's just a text file that controls how the AI behaves, but it's surprisingly powerful. Think of it as the AI's personality and rulebook all rolled into one.

The Magic of the System Prompt
------------------------------

Open up `system.txt` in any text editor, and you'll find what looks like a set of instructions. This is where all the magic happens. It tells the AI everything from "you're a dungeon master" to specific rules about how it should describe scenes or handle player actions. The beauty of this setup is that you can completely transform your game just by editing this file.

Let me give you a practical example. Say you're tired of the standard way the game responds and you want the game to use the voice of a pirate no matter what the theme (a common request?). You don't need to touch any code - just find the writing style section in the system prompt and change:

`1234567Original:Writing Style:- Use active voiceModified:Writing Style:- Use the sing song voice of a pirate shanty!`

Just like that, your game takes on a completely different tone. The same AI that was describing dragon-filled dungeons is now talking filled with 'arr me matty!'.

Experimenting with Game Feel
----------------------------

The system prompt isn't just about changing the writing style though. Want longer, more detailed descriptions? Find this section:

`1234567Original:Keep all descriptions under 3 sentencesFocus on the most important or interesting detailsModified:Provide rich, detailed descriptions up to 5 sentencesInclude sensory details about sights, sounds, and smells`

Or maybe you want to change how the game handles chance and skill checks:

`123456Original:If the player is performing an action that requires skill or luck, roll the diceModified:Roll dice for all social interactionsUse d20 for physical challenges and d12 for magical events`

You can even change how the game world is initially set up:

`123456Original:Create at least one room with a unique ID and brief descriptionModified:Create three connected rooms forming a hub areaEach room must contain at least one interactive object`

Making Changes Safely
---------------------

Before you dive in and start editing, though, let me share some lessons I learned the hard way. First, always back up your original `system.txt`. It's easy to get carried away with changes and forget what the original looked like.

Start small - change one section at a time. The AI is pretty smart about following instructions, but it can sometimes interpret things in unexpected ways. I once tried to make the descriptions more detailed and accidentally ended up with a game that spent three paragraphs describing every doorknob.

Be specific in your instructions. Instead of saying "make it funnier," tell the AI exactly what kind of humor you want. And always check that your changes don't contradict other parts of the prompt - the AI will try to follow all instructions simultaneously, which can lead to some interesting but unintended results.

Getting Creative
----------------

Once you're comfortable with basic changes, you can start getting more creative. Add new sections to handle specific situations. Include examples of exactly how you want the AI to respond in certain situations. You can even create different system prompts for different genres or game styles.

Remember, the system prompt is essentially the AI's instruction manual - it will follow these guidelines religiously. This makes it an incredibly powerful tool for customizing your game without needing to understand the code behind it. Try adding in detail about the kind of theme you want, more than you type in at the start of the game. Whether you want to create a horror game, a space opera, or a romantic comedy, it's all possible just by editing this one file.

The only real limit is your imagination. Well, that and remembering to back up your files before you start experimenting!

Understanding the Agent Architecture (Level 300)
================================================

![Lvl 300](https://assets.community.aws/a/2ogzKejXNZSHkxZEng7FQQ6sqkL/adventure-game-300-jpg.webp?imgSize=1920x1080)

When I first started building this game, I could have gone the simple route - just keeping the game state in the AI's context window and letting it manage everything. But I wanted to build something more robust, something that could grow beyond simple text adventures. Let me walk you through what I built and why it matters.

The Three-Layer Architecture
----------------------------

At its heart, the game is built on three main components working together: an AI agent that makes decisions, a tool manager that executes those decisions, and a graph database that keeps track of everything. Think of it like a movie production - the AI is the director, the tools are the crew, and the graph is the set where everything happens.

The star of the show is the `ConverseAgent`. This is our director, taking in the player's input and deciding what should happen next. It talks directly to Amazon Bedrock, maintaining the conversation and figuring out what tools it needs to use to make things happen. Here's what that looks like in practice:

`123456789101112131415response = self.client.converse(    modelId=self.model_id,    messages=self.messages,    system=[        {            "text": self.system_prompt        }    ],    inferenceConfig={        "maxTokens": 1024,        "temperature": 0.7,    },    toolConfig=self.tools.get_tools())return(response)`

> What does the code do? Use Amazon Q Developer installed in your IDE to explain the code. Once you have installed [Amazon Q Developer](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/q-in-IDE-setup.html) and logged in with your [AWS Builder ID](https://docs.aws.amazon.com/signin/latest/userguide/sign-in-aws_builder_id.html), highlight any code you want to query, then right click and select "Amazon Q" > "Explain". Try is here, and try it on any code you want more information on!

But a director needs a crew, and that's where the `ConverseToolManager` comes in. Instead of letting the AI directly modify the game state (which could get messy), we give it a set of specific tools it can use. Each tool is like a specialist on our crew - one for creating rooms, another for moving players, another for handling objects. Here's how we set up one of these tools:

`123456789101112131415tools.register_tool(    name="create_room",    func=game_state.create_room,    description="Create a new room with a unique ID and description",    input_schema={        'json': {            "type": "object",            "properties": {                "room_id": {"type": "string"},                "description": {"type": "string"}            },            "required": ["room_id"]        }    })`

Finally, we have our set - the `GameState`. This is where everything gets interesting. Instead of trying to cram everything into the AI's context window (which has limits), we use a graph structure built with NetworkX. Rooms connect to other rooms, players can hold items, NPCs can be in locations - everything is represented as nodes and edges in this graph. It's like a web of relationships that can grow as complex as we need it to.

Why This Matters
----------------

You might be wondering why go to all this trouble. Why not just let the AI keep track of everything in its context? The answer becomes clear when you start pushing the boundaries of what's possible.

Imagine you're playing a massive open-world game. The AI's context window can only hold so much information - maybe a few rooms and some recent history. But our graph structure? It can hold an entire world. Players can leave items in one room, travel across the map, and come back to find everything exactly where they left it. The state persists independently of any conversation with the AI.

But it gets better. Because we're using tools with clear interfaces, we can have multiple AIs working with the same world. One AI could be controlling a shopkeeper while another manages the town guard. They're all working with the same consistent state, but each bringing their own personality and goals to the interaction.

Here's a tantalizing possibility:

`1234567# One AI sets up a trapagent1.invoke_with_prompt("Create a trap in the treasury")# Another AI investigates independentlyagent2.invoke_with_prompt("Patrol the treasury")# The game state maintains consistency between both interactions`

The Experimental Frontier
-------------------------

This is where things get really interesting. The architecture I've built here is just the beginning - it's a foundation for experimentation. You could extend this in fascinating ways:

The graph structure is currently just stored in memory while you play, but it could be backed by a database, allowing persistent worlds that exist beyond single play sessions. You could add new types of relationships - maybe items could have magical connections, or rooms could shift based on time of day.

The tool system could be expanded with more complex behaviors. Imagine creating compound tools that execute multiple actions in sequence, or tools that have prerequisites and consequences. You could even have tools that generate new tools dynamically.

And the agent itself? It could be enhanced with memory systems, learning from past interactions. You could implement planning systems that let it think several moves ahead. Different agents could specialize in different aspects of the game world - one for combat, another for puzzles, another for character interaction.

This is why I find this architecture so exciting. It's not just about running a text adventure - it's about building a framework for experimentation with AI-driven interactive experiences. Every component is a hook for future expansion, every interface a door to new possibilities.

Adding Health (Level 400)
=========================

![Lvl 400](https://assets.community.aws/a/2ogzMkTBpqTohY2wrOGG6B3seCw/adventure-game-400-jpg.webp?imgSize=1920x1080)

Let's make some changes to the game mechanics.

One fundamental element missing from our text adventure is the concept of health - that classic RPG mechanic that adds tension and consequences to our actions. Let's walk through how to add this to our game, building on the existing graph-based architecture.

Understanding What We're Building
---------------------------------

We want to add a few key capabilities:

*   Track player health
*   Allow damage and healing
*   Let the AI use these mechanics in storytelling
*   Enable game-over scenarios

The nice thing about our graph structure is that we can add these properties to any entity - not just the player. This means the same system could track NPC health too.

Extending the GameState
-----------------------

First, let's add health tracking to our `GameState` class:

`123456789101112131415161718192021222324252627282930313233343536373839404142434445464748495051525354class GameState:    def __init__(self, display_callback=None):        self.graph = nx.MultiDiGraph()        self.player_id = None        self.display_callback = display_callback    @tool_response    def set_health(self, entity_id, max_health):        """Set an entity's maximum and current health."""        if not self.graph.has_node(entity_id):            raise ValueError(f"Entity '{entity_id}' does not exist.")                    self.graph.nodes[entity_id]['max_health'] = max_health        self.graph.nodes[entity_id]['current_health'] = max_health                return f"Set {entity_id} health to {max_health}"    @tool_response    def modify_health(self, entity_id, amount):        """Modify an entity's health (positive for healing, negative for damage)."""        if not self.graph.has_node(entity_id):            raise ValueError(f"Entity '{entity_id}' does not exist.")                    current = self.graph.nodes[entity_id].get('current_health', 0)        max_health = self.graph.nodes[entity_id].get('max_health', 0)                # Update health, staying within 0 and max_health        new_health = min(max_health, max(0, current + amount))        self.graph.nodes[entity_id]['current_health'] = new_health                if amount < 0:            return f"{entity_id} took {abs(amount)} damage. Health: {new_health}/{max_health}"        else:            return f"{entity_id} healed for {amount}. Health: {new_health}/{max_health}"    @tool_response    def get_health(self, entity_id):        """Get an entity's current and max health."""        if not self.graph.has_node(entity_id):            raise ValueError(f"Entity '{entity_id}' does not exist.")                    current = self.graph.nodes[entity_id].get('current_health', 0)        max_health = self.graph.nodes[entity_id].get('max_health', 0)                return f"{current}/{max_health}"    @tool_response    def is_alive(self, entity_id):        """Check if an entity is alive (health > 0)."""        if not self.graph.has_node(entity_id):            raise ValueError(f"Entity '{entity_id}' does not exist.")                    current = self.graph.nodes[entity_id].get('current_health', 0)        return current > 0`

Registering the New Tools
-------------------------

Add these tools to your `register_tools.py`:

`1234567891011121314151617181920212223242526272829303132333435363738394041424344454647484950def register_game_tools(tools: ConverseToolManager, game_state: GameState):    # ... existing tool registrations ...        # Health System Tools    tools.register_tool(        name="set_health",        func=game_state.set_health,        description="Set an entity's maximum and current health",        input_schema={            'json': {                "type": "object",                "properties": {                    "entity_id": {"type": "string"},                    "max_health": {"type": "integer", "minimum": 1}                },                "required": ["entity_id", "max_health"]            }        }    )        tools.register_tool(        name="modify_health",        func=game_state.modify_health,        description="Modify an entity's health (positive for healing, negative for damage)",        input_schema={            'json': {                "type": "object",                "properties": {                    "entity_id": {"type": "string"},                    "amount": {"type": "integer"}                },                "required": ["entity_id", "amount"]            }        }    )        tools.register_tool(        name="get_health",        func=game_state.get_health,        description="Get an entity's current and max health",        input_schema={            'json': {                "type": "object",                "properties": {                    "entity_id": {"type": "string"}                },                "required": ["entity_id"]            }        }    )`

Updating the System Prompt
--------------------------

Add these instructions to your system prompt so the AI knows how to use the new mechanics:

`12345678910111213141516Health System:1. When creating a new player:   - Set their initial health to 20   - Report their health in combat situations2. When handling combat:   - Use dice rolls to determine damage   - Describe injuries based on damage amount   - Check health after damage to describe appropriate effects   - End the game if player health reaches 03. Health Guidelines:   - Minor hits: 1-3 damage   - Solid hits: 4-6 damage   - Critical hits: 7-10 damage   - Healing potions restore 5-10 health`

Give it a try...
----------------

Work with the code examples above, test, experiment and see if it manages the health of the characters in a way that you want. What happens when the game ends? Do you want to add code that will stop the game? Or should you play on as a ghost? :) 

Taking It Further
-----------------

This basic health system opens up lots of possibilities:

1.   Add armor that reduces damage
2.   Create healing items and spells
3.   Implement different damage types
4.   Add status effects that modify health over time
5.   Create NPCs with different health pools

Remember to handle edge cases:

*   What happens to items when a character dies?
*   Should some damage bypass armor?
*   How does healing work in combat vs. out of combat?

The beauty of using our graph structure is that health becomes just another property we can track and modify. Because it's stored in the graph, it persists between interactions and can be referenced by any tool or agent that needs it.

This implementation provides a solid foundation for adding more complex combat mechanics later. You could expand it to include mana for spells, stamina for actions, or even complex status effects building on this same pattern.

What's Next?
============

So there you have it - a text adventure game powered by AI that you can extend and modify to your heart's content. Whether you stick with the basics or dive into the advanced features, I hope this gives you a foundation to build something unique.

> If you enjoyed this post, please give it a 👍 at the end! Thanks!

AWS Games Builder Challenge
---------------------------

Speaking of building something unique - this kind of project would be perfect for the AWS Games Builder Challenge! The challenge is all about exploring innovative ways to use AWS services in game development, and an AI-powered text adventure certainly fits the bill. Whether you use this code as a starting point or create something completely different, the challenge is a great opportunity to showcase your creativity.

[Check out the AWS Games Builder Challenge here](https://awsdevchallenge.devpost.com/) to learn more about participating. You can enter solo or as part of a team, and there are some amazing prizes up for grabs!

Get Involved!
-------------

I'd love to see what you create with this. The code is available on GitHub, and I'm particularly excited to see:

*   New system prompts that create unique game genres
*   Creative tool implementations
*   Interesting game mechanics
*   Novel uses of the graph structure
*   Fun game scenarios you create

Some Ideas to Get Started
-------------------------

*   Create a murder mystery where NPCs have complex relationships
*   Build a trading game with dynamic economies
*   Design a dungeon crawler with procedurally generated rooms
*   Make a diplomatic simulation where AI NPCs negotiate with each other
*   Build a survival game with resource management

Give it a Try
-------------

The beauty of this project is that it scales with your ambition. You can start by tweaking the system prompt to create your own adventure, then gradually add new features as you get comfortable with the code. The AI will adapt to whatever new tools and mechanics you add, often in surprising and delightful ways.

Stay in Touch
-------------

I'm always excited to see what people build with AI. If you create something cool or just want to chat about AI game development:

*   Find me on [https://linkedin.com/in/mikegchambers](https://linkedin.com/in/mikegchambers)
*   Share your creations using the tag “game-challenge” on [https://community.aws](https://community.aws/)
*   Let me know if you enter the [AWS Games Builder Challenge](https://awsdevchallenge.devpost.com/)!

Remember, the real magic of AI isn't just in what it can do out of the box - it's in how we can shape and direct it to create new experiences. This game is just one example of what's possible when we combine AI with traditional game mechanics and AWS services.

Now go forth and create some adventures! And if you're wondering if the AI made me write that last line... well, maybe it did, maybe it didn't. That's part of the fun, isn't it?

_PS: And yes, I know you made it all the way to the end of this very long post. You're exactly the kind of person who might build something amazing with this. Can't wait to see what you create in the challenge!_
