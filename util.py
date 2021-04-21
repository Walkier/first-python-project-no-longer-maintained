from datetime import datetime
import pytz
import aiohttp, asyncio
import discord

def format_time(time):
    '''takes datetime.now(), returns formatted string of timezones'''
    local_tz = pytz.timezone("Asia/Hong_Kong")
    time = local_tz.localize(time)

    hkt = datetime.strftime(time.astimezone(pytz.timezone("Asia/Hong_Kong")), "%I:%M %p")
    pdt = datetime.strftime(time.astimezone(pytz.timezone("America/Vancouver")), "%I:%M %p")
    aus = datetime.strftime(time.astimezone(pytz.timezone("Australia/Melbourne")), "%I:%M %p")
    use = datetime.strftime(time.astimezone(pytz.timezone("America/Toronto")), "%I:%M %p")
    ukt = datetime.strftime(time.astimezone(pytz.timezone("Europe/London")), "%I:%M %p")

    return(":flag_ca:: %s | :flag_us:&T: %s | :flag_gb:: %s | :flag_hk:: %s | :flag_au:: %s" % (pdt, use, ukt, hkt, aus))

#helper function for im
async def get_json(url: str):
    session = aiohttp.ClientSession()
    try:
        async with session.get(url, timeout=5) as resp:
            try:
                load = await resp.json()
                await session.close()
                return load
            except:
                await session.close()
                return {}
    except asyncio.TimeoutError:
        return None

#add reactions to message
async def add_reactions(msg, emojis):

    async def adding(msg, reactions):
        for emoji in reactions:
            await msg.add_reaction(emoji)

    asyncio.get_event_loop().create_task(adding(msg, emojis))

"""returns None or (reaction, user)
waits and returns emoji added to the passed message
optional: emojis = specify specific to wait for, sec = timeout time (default 60), remove = enable removing reaction after listen"""
async def reaction_reponse_listener(msg, client, remove=False, emojis=None, sec=60):
    def check(reaction, user):
        if emojis:
            return reaction.message.id == msg.id and reaction.emoji in emojis and not user.bot
        return reaction.message.id == msg.id and not user.bot

    try:
        reaction, user = await client.wait_for('reaction_add', timeout=sec, check=check)
    except asyncio.TimeoutError:
        return None

    if remove:
        await msg.remove_reaction(reaction, user)

    return reaction, user

def getUsername(user):
    return user.name + '#' + user.discriminator

def serialize_uni_time_triggers(obj):
    if isinstance(obj, (discord.DMChannel, discord.TextChannel)):
        return str(obj.id)
    else:
        return str(obj)
