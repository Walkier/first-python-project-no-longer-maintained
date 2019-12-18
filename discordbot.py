#walkbot 0.1.2 by Walkier
#python 3.5.3

import discord
from discord.ext import commands
from discord.ext.commands import bot
import asyncio
from datetime import datetime, timedelta
import pytz

import logging

from PrivateInfo import PrivateInfo
senInfo = PrivateInfo()

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

client = commands.Bot(command_prefix='-')
botStartTime = datetime.now()
member_lastseen = {} #global dictionary for lastseen time

#runs when bot is ready
@client.event
async def on_ready():
    print("I am " + client.user.name)
    print(str(client.guilds))

    await client.change_presence(activity = discord.Game(name="-help yourself :)"))

    chamber = client.get_channel(senInfo.chamber)
    void = client.get_channel(senInfo.void)
    await chamber.send("ran")
    await void.send("ran")

    await last_seen_background()
    # await background_hook_loop()
    #await client.edit_profile(username="What name?")

#lmao deletse all of kevin's messages
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    await client.process_commands(message) #allows @client.command methods to work
    
    if str(message.author) == senInfo.kevin:
        print("Got him", message.author, message.content)
        await message.delete(delay=1.0)
        await client.get_channel(senInfo.void).send(str(message.author)+"|"+str(message.content))

#runs a bunch of shit in the background every minute
async def background_hook_loop():
    await client.wait_until_ready()
    while not client.is_closed():
        #hooks
        await last_seen_background()

        nextmin = 60 - datetime.now().second
        await asyncio.sleep(nextmin)

#looping function to check member status
async def last_seen_background():
    await client.wait_until_ready()
    while not client.is_closed():
        members = client.get_all_members()
        for member in members:
            if str(member.status) != "offline" and (await bot_or_not(member) == False):
                member_lastseen[member.name] = datetime.now()
        
        nextmin = 60 - datetime.now().second
        await asyncio.sleep(nextmin)

#helper function to check if bot
async def bot_or_not(user: discord.User):
    return user.bot

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

#commands...

@client.command(pass_context=True, brief="Accepts @user & displays their last online time.")
async def lastseen(ctx, user: discord.User):
    print(str(datetime.now()) + " lastseen ran by " + str(ctx.message.author))
    channel = ctx.channel

    try:
        time = member_lastseen[user.name]
    except:
        await channel.send("Have not seen user since %s (UTC)." % (botStartTime))
        return

    if str(ctx.message.author) == senInfo.kevin:
        await channel.send("Why do you care?")
        return

    await channel.send(format_time(time) + '\n On (HK Date): ' + time.strftime("%m/%d"))

@lastseen.error
async def lastseen_error(ctx, error):
    channel = ctx.channel
    await channel.send(str(error)+". Please tag user with @ symbol.")
    print("@Error:", ctx.guild, ctx.message.content)

@client.command(pass_context=True, brief="Pings client.")
async def ping(ctx):
    print(str(datetime.now()) + " ping ran by " + str(ctx.message.author))
    channel = ctx.channel
    if str(ctx.message.author) == senInfo.kevin:
        await channel.send("Who are you?")
        return
    await channel.send("pew")

@client.command(pass_context=True, brief="Shows time of various timezones.")
async def time(ctx):
    channel = ctx.channel

    if str(ctx.message.author) == senInfo.kevin:
        await channel.send("Who are you?")
        return

    await channel.send(format_time(datetime.now()))
    print(str(datetime.now()) + " time ran by " + str(ctx.message.author))

@client.command(pass_context=True, brief="Utilizes quantum tunneling to probe a @user for gayness particles.")
async def gayornot(ctx, user: discord.User):
    channel = ctx.channel
    await channel.send("**Processing...**")
    await asyncio.sleep(3)
    if str(ctx.message.author) == senInfo.kevin:
        await channel.send("You're gay Kevin.")
        return
    if str(user) == senInfo.author or int(user.display_name, 36)%2 == 0:
        await channel.send("gayness particles not found.")
    else:
        await channel.send("gay.")
    print(str(datetime.now()) + " gayornot ran by " + str(ctx.message.author))

@gayornot.error
async def gayornot_error(ctx, error):
    await lastseen_error(ctx, error)

@client.command(pass_context=True)
async def suck_it(ctx):
    channel = ctx.channel
    msg = await channel.send(senInfo.emoji_pop+senInfo.emoji_kev)
    await asyncio.sleep(1)

    delay = 0.05
    for j in range(3):
        for i in range(2):
            space = ' '*(i+1)*2
            await asyncio.sleep(delay)
            await msg.edit(content=senInfo.emoji_pop + space + senInfo.emoji_kev)
        for i in range(1, -1, -1):
            space = ' '*i*2
            await asyncio.sleep(delay)
            await msg.edit(content=senInfo.emoji_pop + space + senInfo.emoji_kev)
        await asyncio.sleep(5)
    for i in range(2):
        space = ' '*(i+1)*2
        await asyncio.sleep(delay)
        await msg.edit(content=senInfo.emoji_pop + space + senInfo.emoji_kev)
    await msg.edit(content=senInfo.emoji_pop+"▫️▫️▫️"+senInfo.emoji_kev) 

    print(str(datetime.now()) + " suck_it ran by " + str(ctx.message.author))

@client.command(pass_context=True, brief="Coming soon!")
async def gametime(ctx):
    print(str(datetime.now()) + " gametime ran by " + str(ctx.message.author))

'''
stuff to do:
command ran function
error outputs to chat if arguments are wrong
ai stuff
refactor to be class based

file i/o for lastseen
remindme/them
game time planner

functions to make
'''

#client.loop.create_task(last_seen_background())
client.run(senInfo.token)

'''
@client.command(pass_context=True, brief="Displays info about a user.")
async def info(ctx, user: discord.Member):    
    channel = ctx.channel
    embed = discord.Embed(color = 0xef0404, title = "%s's Info" % (user.name), description = str(user.top_role))
    embed.set_thumbnail(url = user.avatar_url)
    embed.add_field(name = "ID", value = user.id, inline = True)
    embed.add_field(name = "Registration Date", value = str(user.created_at), inline = True)
    embed.add_field(name = "Join Date", value = str(user.joined_at), inline = True)
    if user.server_permissions.administrator:
        embed.set_footer(text = "admin")
    await channel.send(embed=embed)
    print(str(datetime.now()) + " info ran by " + str(ctx.message.author))

@info.error
async def info_error(ctx, error):
    channel = ctx.channel
    void = client.get_channel(senInfo.void)
    code = str(ctx).split(" ")
    if code[2] + code[3] == "notfound":
        await channel.send("User not found. (Capitalization is required.)")
    else:
        await void.send("GAYORNOT ERROR:")
        await void.send(ctx)

@client.command(pass_context=True, brief="Displays info about a channel.")
async def chan(ctx, in_chan: discord.channel):
    channel = ctx.channel
    print("hi")
    print("ID: " + in_chan.id)
    await channel.send("ID: " + in_chan.id)

@chan.error
async def chan_error(ctx, error):
    channel = ctx.channel
    void = client.get_channel(senInfo.void)
    code = str(ctx).split(" ")
    if code[2] + code[3] == "notfound.":
        await channel.send(ctx)
    else:
        await void.send("CHAN ERROR:")
        await void.send(ctx)
'''