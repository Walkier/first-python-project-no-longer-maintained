#walkbot 0.1.4 by Walkier
#python 3.5.3

import discord
from discord.ext import commands
from discord.ext.commands import bot
import asyncio
from datetime import datetime, timedelta
import json
import collections

import logging

from util import format_time
from PrivateInfo import PrivateInfo
from GameTime import GameTimeUI, GameTime
senInfo = PrivateInfo()

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

client = commands.Bot(command_prefix='-')
Game_time_ui = GameTimeUI("Global :(", client)
Bot_start_time = datetime.now()

# global dictionaries T-T
try:
    with open("member_lastseen.json") as f:
        Member_lastseen = json.loads(f.read())
    #parses datetime string from file to obj
    for member in Member_lastseen:
        Member_lastseen[member] = datetime.strptime(Member_lastseen[member], '%Y-%m-%d %H:%M:%S.%f')
except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
    Member_lastseen = {} 

try:
    with open("temp_msg_count_global.json") as f:
        Temp_msg_count_global = json.loads(f.read())
    Temp_msg_count_global['date\nx'] = datetime.strptime(Temp_msg_count_global['date\nx'], '%Y-%m-%d %H:%M:%S.%f')
except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
    Temp_msg_count_global = {'date\nx': Bot_start_time}
Last_week_stat_msg = [None]

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

    await background_hook_loop()
    #await client.edit_profile(username="What name?")

#runs when any message is recieved by bot in any of the channels it is in
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content == "$safe-exit" and str(message.author) == senInfo.author:
        print("$QUIT RAN BY", senInfo.author)
        with open("member_lastseen.json", 'w') as f:
            f.write(json.dumps(Member_lastseen, default=str))
        with open("temp_msg_count_global.json", 'w') as f:
            f.write(json.dumps(Temp_msg_count_global, default=str))
        await message.channel.send("SHUTTING DOWN...")
        await client.close()

    # weekly_msg_stats() on_message hook
    if message.channel.id == PrivateInfo.peruni_gen_id and not message.author.bot:
        if message.author.display_name in Temp_msg_count_global:
            Temp_msg_count_global[message.author.display_name] += 1
        else:
            Temp_msg_count_global[message.author.display_name] = 1

    if (str(message.author) == PrivateInfo.rust) and message.channel.id == PrivateInfo.peruni_gen_id:
        if len(message.channel.members) > 9:
            for mem in message.channel.members:
                if mem.bot and mem != client.user:
                    await message.channel.send("I detect "+str(mem)+" in this channel and therefore it can read and log all your messages.\nAre you sure you want this stranger to have this power?\n"+message.content)

    await client.process_commands(message) #allows @client.command methods to work

#runs a bunch of shit in the background every minute
async def background_hook_loop():
    await client.wait_until_ready()
    while not client.is_closed():
        #hooks
        await last_seen_background()
        if datetime.now().weekday() == 5 and datetime.now().hour == 0 and datetime.now().minute == 0:
            await weekly_msg_stats() 

        nextmin = 60 - datetime.now().second
        await asyncio.sleep(nextmin)

#check member status and store time (in bot's tz) in Member_lastseen dic
async def last_seen_background():
    members = client.get_all_members()
    for member in members:
        if str(member.status) != "offline" and not member.bot:
            Member_lastseen[member.name] = datetime.now()

#sends weekly msg count stats to channel
async def weekly_msg_stats():
    channel = client.get_channel(senInfo.peruni_gen_id)

    #unpin last week's message
    if Last_week_stat_msg[0]:
        try:
            await Last_week_stat_msg[0].unpin()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException) as e:
            print("weekly_msg_stats: Unpin exception.", e)
        except:
            print("weekly_msg_stats: Unexpected unpin exception.")

    statStartDate = datetime.strftime(Temp_msg_count_global['date\nx'], '%m/%d')
    del Temp_msg_count_global['date\nx']

    #sort users in dic by message count into a list of tuples 
    sorted_buffer = sorted(Temp_msg_count_global.items(), key = lambda kv:(kv[1], kv[0]), reverse=True)
    total_msgs = sum(msg[1] for msg in sorted_buffer)

    #turn string buffer into " user1: msg% | user2: msg% | user3: msg% "
    string_buffer = " "
    for user_record in sorted_buffer:
        string_buffer += "{}: *{}*% | ".format(user_record[0], round(user_record[1]/total_msgs*100, 2))
    for member in channel.members:
        if member.display_name not in Temp_msg_count_global.keys() and not member.bot:
            string_buffer += member.display_name + ": *0%* | "
    string_buffer = string_buffer[:-2]

    msg = await channel.send("**Weekly Message Count Breakdown** ("+statStartDate+" - "+datetime.strftime(datetime.now(),'%m/%d')+"):"+ \
        "\nLoneliest ->**" + string_buffer + "**<- Nonexistent")
    
    await msg.pin()
    Last_week_stat_msg[0] = msg

    #reset dic and repopulate with date
    print(datetime.now(), "msg count bf clear", Temp_msg_count_global)
    Temp_msg_count_global.clear()
    Temp_msg_count_global['date\nx'] = datetime.now()

#commands...

@client.command(pass_context=True, brief="Accepts @user & displays their last online time.")
async def lastseen(ctx, user: discord.User):
    print(str(datetime.now()) + " lastseen ran by " + str(ctx.message.author))
    channel = ctx.channel

    try:
        time = Member_lastseen[user.name]
    except KeyError:
        await channel.send("Have not seen user since at least %s (HKT)." % (Bot_start_time))
        return

    await channel.send(format_time(time) + '\n On (HK Date): ' + time.strftime("%m/%d"))

@lastseen.error
async def lastseen_error(ctx, error):
    print("@Error:", ctx.guild, ctx.message.content)
    channel = ctx.channel

    await channel.send(str(error)+"\nPlease tag user with @ symbol.")

@client.command(pass_context=True, brief="Pings client.")
async def ping(ctx):
    print(str(datetime.now()) + " ping ran by " + str(ctx.message.author))
    channel = ctx.channel

    await channel.send("pew")

@client.command(pass_context=True, brief="Shows time of various timezones.")
async def time(ctx):
    print(str(datetime.now()) + " time ran by " + str(ctx.message.author))
    channel = ctx.channel

    if str(ctx.message.author) == PrivateInfo.arm:
        await channel.send(PrivateInfo.appreciate_msg)
        return

    await channel.send(format_time(datetime.now()))

@client.command(pass_context=True, brief="Utilizes quantum tunneling to probe a @user for gayness particles.")
async def gayornot(ctx, user: discord.User):
    print(str(datetime.now()) + " gayornot ran by " + str(ctx.message.author))
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

@gayornot.error
async def gayornot_error(ctx, error):
    await lastseen_error(ctx, error)

@client.command(pass_context=True)
async def suck_it(ctx):
    print(str(datetime.now()) + " suck_it ran by " + str(ctx.message.author))
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

@client.command(pass_context=True, brief="Schedule a game time with friends! Takes no arguments.")
async def gametime(ctx):
    print(str(datetime.now()) + " gametime ran by " + str(ctx.message.author))
    await ctx.channel.send("This command is still under construction.")
    await Game_time_ui.new_gametime(ctx)

'''
stuff to do:
command ran function
error outputs to chat if arguments are wrong
ai stuff
refactor to be class based

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