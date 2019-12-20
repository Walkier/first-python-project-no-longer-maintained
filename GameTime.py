import discord
import asyncio

class GameTimeUI:
    timeout = 60.0

    def __init__(self, guild, client):
        self.guild = guild
        self.client = client
        self._in_use = False
        self.game_times = []

    async def new_gametime(self, ctx):
        game_time = GameTime(ctx)

        if self._in_use:
            await game_time.channel.send("A user is already currently setting up a game time, please try again later.")
            return 
        
        for gt in self.game_times:
            if gt.author == game_time.author:
                await game_time.channel.send("You already have a game time set up. Delete it to set up another.")
                return

        self._in_use = True
        await self._select_tz(game_time)

    async def _select_tz(self, game_time):
        msg = await game_time.channel.send("Select your timezone.")
        reactions = ['🇨🇦', '🇺🇸', '🇬🇧', '🇭🇰', '🇦🇺']
        
        async def add_reactions(msg, reactions):
            for emoji in reactions:
                await msg.add_reaction(emoji)
        
        asyncio.get_event_loop().create_task(add_reactions(msg, reactions))

        def check(reaction, user):
            return user == game_time.author and reaction.message.id == msg.id and reaction.emoji in reactions

        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=self.timeout, check=check)
        except asyncio.TimeoutError:
            await self._time_out(game_time)
            return
        else:
            await game_time.channel.send('👍')

        await self._time_out(game_time)

    async def _time_out(self, game_time):
        await game_time.channel.send("No response for 60 seconds. Aborting game time setup.")
        self._in_use = False

class GameTime:
    def __init__(self, ctx):
        self.author = ctx.author
        self.channel = ctx.channel