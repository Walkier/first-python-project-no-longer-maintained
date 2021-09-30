#walkbot 0.2.1 comm.0 by Walkier
#python 3.5.3 on pi

# SEE async def ping(ctx) for definition of the simplest command

import discord
from discord.ext import commands
from discord.ext.commands import bot #https://stackoverflow.com/questions/51234778/what-are-the-differences-between-bot-and-client#:~:text=Just%20use%20commands.,Bot%20.&text=If%20you%20simply%20want%20your,means%2C%20use%20the%20base%20Client%20.

import time as stime
from datetime import datetime, timedelta
import asyncio
import random, json, errno, os
import urllib.parse
import pdb

import util
from PrivateVals import PrivateValsV1 as PrivateVals
from PublicVals import PublicVals
from EncapLogic import EncapLogic
# from GameTime import GameTimeUI, GameTime

import dateparser
import pytz

import logging
import traceback
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

client = commands.Bot(command_prefix='-', intents = discord.Intents.all())
# Game_time_ui = GameTimeUI("Global :(", client)
Bot_start_time = datetime.now()
fm_bool = False

# global dictionaries T-T
try:
    with open("savefiles/member_lastseen.json") as f:
        Member_lastseen = json.loads(f.read())
    #parses datetime string from file to obj
    for member in Member_lastseen:
        Member_lastseen[member] = datetime.strptime(Member_lastseen[member], '%Y-%m-%d %H:%M:%S.%f')
except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
    Member_lastseen = {} 

try:
    with open("savefiles/temp_msg_count_global.json") as f:
        Temp_msg_count_global = json.loads(f.read())
    Temp_msg_count_global['date\nx'] = datetime.strptime(Temp_msg_count_global['date\nx'], '%Y-%m-%d %H:%M:%S.%f')
except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
    Temp_msg_count_global = {'date\nx': Bot_start_time}
Last_week_stat_msg = [None]

uni_instance_dict = {
    'vc_join_sub': { str(PrivateVals.peruni_guild_id): PrivateVals.peruni_gen_id, str(PrivateVals.alert_guild_id): PrivateVals.alert_vc_text_chan_id },
}
siege_stopper_dic = {}
encapLogic = EncapLogic(client)

# -- runs when bot is ready --
@client.event
async def on_ready():
    print("I am ", client.user.name, datetime.now())
    print(str(client.guilds))

    await client.change_presence(activity = discord.Game(name="-help by Walker"))

    chamber = client.get_channel(PrivateVals.chamber)
    void = client.get_channel(PrivateVals.void)
    await chamber.send("ran")
    await void.send("ran")

    #load in uni_time_triggers global dict :(
    try:
        with open("savefiles/uni_time_triggers.json") as f:
            uni_time_triggers = json.loads(f.read())
            for date in uni_time_triggers:
                for author in list(uni_time_triggers[date]):
                    # print("_", uni_time_triggers[date][author]['channel'], date, "_")
                    if uni_time_triggers[date][author]['channel'] != None:
                        if uni_time_triggers[date][author]['channel'].isnumeric():
                            uni_time_triggers[date][author]['channel'] = client.get_channel(int(uni_time_triggers[date][author]['channel']))
                        else:
                            del uni_time_triggers[date][author]
            globals()['uni_time_triggers'] = uni_time_triggers
    except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
        globals()['uni_time_triggers'] = {}
    except Exception as e:
        print("Unexpected exception:", e)
        globals()['uni_time_triggers'] = {}

    await background_hook_loop()
    #await client.edit_profile(username="What name?")

# -- runs when any message is recieved by bot in any of the channels it is in --
@client.event
async def on_message(message):
    #prevent echo and bots
    if message.author == client.user or message.author.bot or message.channel.id in PrivateVals.channel_blacklist:
        return

    #admin_commands hook
    if message.content and message.content[0] == '$' and str(message.author) == PrivateVals.author:
        await admin_commands(message)

    # weekly_msg_stats() on_message hook
    if message.channel.id == PrivateVals.peruni_gen_id:
        if message.author.display_name in Temp_msg_count_global:
            Temp_msg_count_global[message.author.display_name] += 1
        else:
            Temp_msg_count_global[message.author.display_name] = 1

    #protect general hook
    if (str(message.author) == PrivateVals.rust) and message.channel.id == PrivateVals.peruni_gen_id:
        if len(message.channel.members) > 9:
            for mem in message.channel.members:
                if mem.bot and mem != client.user:
                    await message.channel.send("I detect "+str(mem)+" in this channel and therefore it can read and log all your messages.\nAre you sure you want this stranger to have this power?\n"+message.content)

    if encapLogic.debug:
        await encapLogic.debug_hook(message)

    # if str(message.author) == "RPG Schedule#4691" and message.channel.id == PrivateVals.peruni_eventschan_id:
    # await inform_event(message)

    await client.process_commands(message) #allows @client.command methods to work

#  -- on_message hook defs --

async def admin_commands(message):
    if(message.content == "$exit"):
        print("$QUIT RAN BY", PrivateVals.author)
        with open("savefiles/member_lastseen.json", 'w') as f:
            f.write(json.dumps(Member_lastseen, default=str))
        with open("savefiles/temp_msg_count_global.json", 'w') as f:
            f.write(json.dumps(Temp_msg_count_global, default=str))
        with open("savefiles/uni_time_triggers.json", 'w') as f:
            f.write(json.dumps(uni_time_triggers, default=util.serialize_uni_time_triggers))
        await message.channel.send("SHUTTING DOWN...")
        if datetime.now() > Bot_start_time + timedelta(minutes=5):
            for guild, channel in uni_instance_dict['vc_join_sub'].items():
                await client.get_channel(channel).send("vc_join_sub unsubbed, bot shutting down")
        await client.close()
    elif(message.content.split()[0] == "$status"):
        await client.change_presence(activity = discord.Game(name = message.content[8:]))
        globals()['fm_bool'] = False
    elif(message.content.split()[0] == "$lastfm"):
        globals()['fm_bool'] = not globals()['fm_bool']
        if globals()['fm_bool']:
            await client.change_presence(activity = discord.Activity(name='last.fm', type=discord.ActivityType.listening))
        else:
            await client.change_presence(activity = discord.Game(name="-help"))
    else:
        await encapLogic.admin_commands(message)

#sends event notif to general
# async def inform_event(message):
#     try:
#         if message.embeds[0].fields[0].name == 'When':
#             per_gen = client.get_channel(PrivateVals.peruni_gen_id)
#             for field in message.embeds[0].fields:
#                 if field.name.startswith('Sign Ups'):
#                     invited = field.value.split('\n')
#             if 'invited' not in locals():
#                 return
#             invited_str = ""
#             if invited[0] != "No players":
#                 for person in invited:
#                     invited_str += '<' + person.split('<')[1] + ' '
#                 sent_msg = await per_gen.send("New event **{}** at <#{}>!\n".format(message.embeds[0].title, PrivateVals.peruni_eventschan_id)\
#                     + invited_str + "Confirm your attendance now. :white_check_mark:")
#                 await sent_msg.add_reaction('✅')
#             else:
#                 await per_gen.send("New event **{}** at <#{}>!\n".format(message.embeds[0].title, PrivateVals.peruni_eventschan_id)\
#                     + invited_str + "Join the event by clicking + in <#{}>.".format(PrivateVals.peruni_eventschan_id))
#     except IndexError:
#         pass

# runs once in the background every minute
async def background_hook_loop():
    await client.wait_until_ready()
    while not client.is_closed():
        #hooks
        await last_seen_background()
        if datetime.now().day == 1:
            await weekly_msg_stats() 

        try:
            await siege_stopper_check()
            await uni_time_triggers_check()
            if datetime.now() > Bot_start_time + timedelta(minutes=5):
                await new_vc_join_check()
        except Exception as e:
            print("Background loop exception", e)

        if globals()['fm_bool']:
            asyncio.get_event_loop().create_task(last_fm_update(client))

        nextmin = 60 - datetime.now().second
        await asyncio.sleep(nextmin)

# -- background_hook_loop hook defs --

vc_dic = {}
async def new_vc_join_check():
    for guild_id in uni_instance_dict['vc_join_sub']:
        guild = client.get_guild(int(guild_id))
        peruni_gen_channel = client.get_channel(uni_instance_dict['vc_join_sub'][guild_id])
        
        for vc in guild.voice_channels:
            if str(vc.id) not in vc_dic:
                vc_dic[str(vc.id)] = 0

            if len(vc.members) > 0 and vc_dic[str(vc.id)] == 0:
                await peruni_gen_channel.send("@here "+vc.name+" is open")
                if random.random() <= 0.07:
                    if guild_id == str(PrivateVals.al_guild_id):
                        del uni_instance_dict['vc_join_sub'][guild_id]

            vc_dic[str(vc.id)] = len(vc.members)

async def last_fm_update(client):
    #get json of last 1 track
    try:
        api = "http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=Forever_Walking&api_key={}&format=json&limit=1".format(PrivateVals.last_fm_api_key)
        json_dict = await util.get_json(api)

        if json_dict and '@attr' in json_dict['recenttracks']['track'][0]:
            status = json_dict['recenttracks']['track'][0]['name'] + ' by ' + json_dict['recenttracks']['track'][0]['artist']['#text']
            await client.change_presence(activity = discord.Game(name=status))
        else:
            await client.change_presence(activity = discord.Activity(name='last.fm', type=discord.ActivityType.listening))
    except KeyError as key_e:
        await void.send("last_fm keyerror:"+str(json_dict))
    except Exception as e:
        logging.error(traceback.format_exc())
        void = client.get_channel(PrivateVals.void)
        await void.send("last_fm exception:"+str(e))

#check member status and store time (in bot's tz) in Member_lastseen dic
async def last_seen_background():
    members = client.get_all_members()
    for member in members:
        if str(member.status) != "offline" and not member.bot:
            Member_lastseen[util.getUsername(member)] = datetime.now()

#sends weekly msg count stats to channel
async def weekly_msg_stats():
    channel = client.get_channel(PrivateVals.peruni_gen_id)

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
            string_buffer += member.mention + ": *0%* | "
    string_buffer = string_buffer[:-2]

    msg = await channel.send("**Weekly? Message Count Breakdown** ("+statStartDate+" - "+datetime.strftime(datetime.now(),'%m/%d')+"):"+ \
        "\nLoneliest ->**" + string_buffer + "**<- Nonexistent" + "\nTotal: " + str(total_msgs))
    
    await msg.pin()
    Last_week_stat_msg[0] = msg

    #reset dic and repopulate with date
    print(datetime.now(), "msg count bf clear", Temp_msg_count_global)
    Temp_msg_count_global.clear()
    Temp_msg_count_global['date\nx'] = datetime.now()

# kicks people off voice channels after assigned time
async def siege_stopper_check():
    guild = client.get_guild(PrivateVals.peruni_guild_id)
    peruni_gen_channel = client.get_channel(PrivateVals.peruni_gen_id) # TODO: require generalization

    time_now = datetime.now()

    #shift reset time by 24 hours at 0:00
    if time_now.hour == 8 and time_now.minute == 0:
        for key in siege_stopper_dic:
            siege_stopper_dic[key]['time_reset'] += timedelta(hours=24)
            siege_stopper_dic[key]['day_reset'] = True

    for key, person_dict in siege_stopper_dic.items():
        #if time hits
        if time_now >= person_dict['time'] + person_dict['active_delta'] and time_now < person_dict['time'] + person_dict['end_delta']:
            user = guild.get_member(key)
            if str(user.status) != 'offline': #online
                person_dict['active'] = True

                for guild in client.guilds:
                    guild_user = guild.get_member(key)
                    if guild_user.voice:
                        try:
                            await guild_user.move_to(None, reason='stopper command')
                            if str(guild.id) in uni_instance_dict['vc_join_sub']:
                                await uni_instance_dict['vc_join_sub'][str(guild.id)].send('Get out of there.\nReason: '+str(person_dict['reason'])) # TODO: require generalization
                        except discord.errors.Forbidden:
                            await guild_user.send(content='REEEEEEEEEEEEE set a timer')
                
                await user.send(content=person_dict['reason'], tts=True)
        elif time_now >= person_dict['time'] + person_dict['active_delta'] - timedelta(minutes=3) and person_dict['delays'] > 0: # t - 3 min warning
            user = guild.get_member(key)
            if str(user.status) != 'offline': #online
                
                await user.send(content="less than 3 minutes until kick sir", tts=True)

        if person_dict['active'] or person_dict['day_reset']:
            user = guild.get_member(key)
            if str(user.status) == 'offline' or (person_dict['day_reset'] and not person_dict['active']):
                user = guild.get_member(key)
                person_dict['active'] = False
                if person_dict['day_reset']:
                    person_dict['time'] = person_dict['time_reset']
                    person_dict['active_delta'] = timedelta(0)
                    person_dict['delays'] = 0
                    person_dict['day_reset'] = False

async def uni_time_triggers_check():
    time_now = datetime.now()

    for time_key in uni_time_triggers:
        # print('check', time_key == time_now.strftime("%H:%M on %B %-d, %Y"), time_key, time_now.strftime("%H:%M on %B %-d, %Y"))
        if time_key == time_now.strftime("%H:%M on %B %-d, %Y"):
            for user_key in uni_time_triggers[time_key]:
                await uni_time_triggers[time_key][user_key]['channel'].send('From <@'+str(user_key)+'>: '+uni_time_triggers[time_key][user_key]['msg'])
    
# -- commands... --

@client.command(pass_context=True, brief="Pings client.")
async def ping(ctx):
    print(str(datetime.now()) + " ping ran by " + str(ctx.message.author))
    channel = ctx.channel

    await channel.send("pew")

@client.command(pass_context=True, brief="subscribes this channel to updates of people joining voice call", \
    help="example usage:\n-vc_join_sub true\n-vc_join_sub false")
async def vc_join_sub(ctx, enable_boolean: bool):
    print(str(datetime.now()) + " vc_join_sub ran by " + str(ctx.message.author) + ' ' + str(ctx.message.guild.id))
    channel = ctx.channel

    if enable_boolean:
        uni_instance_dict['vc_join_sub'][str(ctx.message.guild.id)] = ctx.channel.id
        await channel.send("channel is now subscribed to voice channel joins")
    elif not enable_boolean:
        uni_instance_dict['vc_join_sub'].pop(str(ctx.message.guild.id), None)
        await channel.send("channel is now unsubscribed to voice channel joins")
    else:
        await channel.send("something went wrong")

@vc_join_sub.error
async def lastseen_error(ctx, error):
    print("@Error:", ctx.message.content, error, ctx.guild, sep=' | ')
    channel = ctx.channel

    await channel.send(str(error))

@client.command(pass_context=True, brief="Accepts @user & displays their last online time.")
async def lastseen(ctx, user: discord.User):
    print(str(datetime.now()) + " lastseen ran by " + str(ctx.message.author))
    channel = ctx.channel

    await ctx.message.delete()

    try:
        time = Member_lastseen[util.getUsername(user)]
    except KeyError:
        await channel.send("Have not seen user since at least %s (HKT)." % (Bot_start_time))
        return

    await channel.send('Hi ' +str(ctx.message.author.display_name)+ ', this person was **last seen**:\n' + util.format_time(time) + '\n On (HK Date): ' + time.strftime("%m/%d"))

@lastseen.error
async def lastseen_error(ctx, error):
    print("@Error:", ctx.message.content, error, ctx.guild, sep=' | ')
    channel = ctx.channel

    await channel.send(str(error)+"\nPlease tag user with @ symbol.")

@client.command(pass_context=True, brief="Shows time of various timezones.")
async def time(ctx):
    print(str(datetime.now()) + " time ran by " + str(ctx.message.author))
    channel = ctx.channel

    if str(ctx.message.author) == PrivateVals.arm:
        await channel.send(PrivateVals.appreciate_msg)
        return

    await channel.send(util.format_time(datetime.now()))

@client.command(pass_context=True, brief="Utilizes quantum tunneling to probe a @user for particles.")
async def yayornot(ctx, user: discord.User):
    await encapLogic.yayornot(ctx, user)

@yayornot.error
async def yayornot_error(ctx, error):
    await lastseen_error(ctx, error)

@client.command(pass_context=True)
async def suck_it(ctx):
    print(str(datetime.now()) + " suck_it ran by " + str(ctx.message.author))
    channel = ctx.channel

    # encap and server whitelist

    msg = await channel.send(PrivateVals.emoji_pop+PrivateVals.emoji_kev)
    await asyncio.sleep(1)

    delay = 1
    for j in range(3):
        for i in range(2):
            space = ' '*(i+1)*2
            await asyncio.sleep(delay)
            await msg.edit(content=PrivateVals.emoji_pop + space + PrivateVals.emoji_kev)
        for i in range(1, -1, -1):
            space = ' '*i*2
            await asyncio.sleep(delay)
            await msg.edit(content=PrivateVals.emoji_pop + space + PrivateVals.emoji_kev)
        await asyncio.sleep(5)
    for i in range(2):
        space = ' '*(i+1)*2
        await asyncio.sleep(delay)
        await msg.edit(content=PrivateVals.emoji_pop + space + PrivateVals.emoji_kev)
    await msg.edit(content=PrivateVals.emoji_pop+"▫️▫️▫️"+PrivateVals.emoji_kev)

@client.command(pass_context=True, brief="Try it. I was clearly too bored.")
async def theworm(ctx):
    print(str(datetime.now()) + " theworm ran by " + str(ctx.message.author))
    channel = ctx.channel

    CANVAS_LEN = 32

    msg = await channel.send('⠀'*CANVAS_LEN)
    await asyncio.sleep(1)

    start = 0
    length = 0
    end = start + length
    forward_mode = False
    worm = "-"
    space = "⠀"

    while length != CANVAS_LEN:
        #boundary checking
        end = start + length
        if end == CANVAS_LEN or start == 0:
            forward_mode = not forward_mode
            length += 1
            start -= int(not forward_mode)
            if channel.id == PrivateVals.al_gen_id:
                CANVAS_LEN = 8
                space = PrivateVals.emoji_ai_null
                worm = PrivateVals.emoji_al_kev if forward_mode else PrivateVals.emoji_al_kev_rev

        content= space*start + worm*length + space*(CANVAS_LEN-length-start)
        await msg.edit(content=content)

        #move snake
        if forward_mode:
            start += 1
        else:
            start -= 1

        await asyncio.sleep(1)

    await msg.edit(content=worm*CANVAS_LEN)

# @client.command(pass_context=True, brief="Schedule a game time with friends! Takes no arguments.")
# async def gametime(ctx):
#     print(str(datetime.now()) + " gametime ran by " + str(ctx.message.author))
#     await ctx.channel.send("This command is still under construction.")
#     await Game_time_ui.new_gametime(ctx)

#TODO: Rus
#blatantly copied from NotSoBot
@client.command(pass_context=True, aliases=['image', 'photo', 'img'], brief="Blatant copy of NotSoBot's image search command.", cooldown=(3, 5))
@commands.cooldown(rate=2, per=15.0, type=commands.BucketType.user)
async def im(ctx, *, search:str):
    print(str(datetime.now()) + " image ran by " + str(ctx.message.author))
    channel = ctx.channel

    #manual limit on num of searches
    try:
        with open("savefiles/daily_search_use.txt") as f:
            #if file last mod date not today
            if stime.strftime('%d', stime.localtime(os.path.getmtime("savefiles/daily_search_use.txt"))) != datetime.strftime(datetime.now(), '%d'):
                use_count = 0
            else:
                use_count = int(f.read())
    except IOError as e:
        if e.errno == errno.ENOENT:
            print('im: day restart?', datetime.now())
        else:
            print('im: some other file io ERROR')
        use_count = 0

    #use_count check
    if use_count > 95:
        await channel.send("Exceeded 100 daily free searches given by Google API. Pay me so I can pay Google for more searches.")
        return

    choice = 0#random.randint(0, 9)
    #request
    try:
        key = PrivateVals.google_cus_search_json_api_key
        api = "https://www.googleapis.com/customsearch/v1?key={0}&cx=015418243597773804934:it6asz9vcss&searchType=image&q={1}".format(key, urllib.parse.quote(search))
        load = await util.get_json(api)
        assert 'error' not in load.keys() and 'items' in load.keys()
        assert len(load)
        # rand = random.choice(load['items'])
        # print([x['link'] for x in load['items']])
        # image = rand['link']
        desc = lambda choice: '[Result '+str(choice+1)+']'+'('+load['items'][choice]['link']+')'
        embed_sent = discord.Embed(title='Image Search Results for "'+search+'"', rich=True, description=desc(choice), colour=53633)
        embed_sent.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar_url)
        embed_sent.set_image(url=load['items'][choice]['link'])
        embed_sent.set_footer(text="Page "+str(choice+1)+"/10")
        image_msg = await channel.send(embed=embed_sent)
    except discord.errors.Forbidden:
        await channel.send("no send_file permission")
        return
    except AssertionError:
        await channel.send(":warning: `API Quota Reached or Invalid Search`")
        return
    except:
        raise
    
    #use_count update
    use_count += 1
    with open("savefiles/daily_search_use.txt", 'w') as f:
        f.write(str(use_count))

    #scrolling
    await util.add_reactions(image_msg, ['⬅️', '➡️'])

    while True:
        reaction = await util.reaction_reponse_listener(image_msg, client, True)
        if reaction is None:
            break

        if reaction[0].emoji == '➡️':
            choice = (choice + 1) % len(load['items'])
        elif reaction[0].emoji == '⬅️':
            choice = (choice - 1) % len(load['items'])

        embed_sent.description = desc(choice)
        embed_sent.set_image(url=load['items'][choice]['link'])
        embed_sent.set_footer(text="Page "+str(choice+1)+"/10")
        await image_msg.edit(embed=embed_sent)
        # await channel.send(load['items'][choice]['fileFormat'])

@im.error
async def im_error(ctx, error):
    print("@Error:", ctx.message.content, error, ctx.guild, sep=' | ')
    channel = ctx.channel

    await channel.send("Hi! Command 'im' says: "+str(error))

@client.command(pass_context=True, brief="Stops Siege from ruining your life.", help="testing string")
async def stopper(ctx, time: str, *args):
    print(str(datetime.now()) + " stopper ran by " + str(ctx.message.author))
    channel = ctx.channel

    #optimize later and help menu lol
    date = dateparser.parse(time, languages=['en'])
    if date == None:
        await channel.send("dateparser did not understand you")
        return

    if date < datetime.now():
        await channel.send("might not go off")

    #reason parsing
    reason = ""
    for arg in args:
        reason += arg + ' '
    if len(reason) == 0:
        reason = "Hi, it's time bro."

    await channel.send("args recived: "+"time="+time+", reason="+reason)
    await channel.send("parsed time: " + date.strftime("%m/%d/%Y, %H:%M:%S") + " tz: " + str(date.tzinfo))

    #op to save time only later
    siege_stopper_dic[ctx.message.author.id] = {'time': date, 'reason': reason, 'time_reset': date, 'day_reset': False,
        'end_delta': timedelta(hours=6), 'active_delta': timedelta(hours=0), 'active': False, 'delays': 0}

@stopper.error
async def stopper_error(ctx, error):
    print("@Error:", ctx.message.content, error, ctx.guild, sep=' | ')
    channel = ctx.channel

    await channel.send("Hi! Command 'siege_stopper' says: "+str(error))

@client.command(pass_context=True, brief="Status of siege_stopper")
async def stopper_dict(ctx):
    print(str(datetime.now()) + " stopper_status ran by " + str(ctx.message.author))
    channel = ctx.channel

    # TODO: lim access 

    await channel.send(siege_stopper_dic)

@client.command(pass_context=True, brief="Delays the effect of stopper in minutes")
async def will_sleep(ctx, minutes: int):
    print(str(datetime.now()) + " will_sleep ran by " + str(ctx.message.author))
    channel = ctx.channel
    
    # TODO: tz support, dm after kick, enablers

    person_dict = siege_stopper_dic[ctx.message.author.id]

    #7 second rule
    await channel.send("Please confirm in 7 seconds...")
    await asyncio.sleep(7.0)
    await channel.send("you sure?")

    def check(m):
        return m.content == 'i am sure' and m.author == ctx.message.author

    msg = await client.wait_for('message', check=check, timeout=10.0)
    # await channel.send('Hello {.author}!'.format(msg))

    #perform delay
    if minutes > 20:
        await channel.send("A bit too much don't you think? ;)")
        return
    
    if ctx.message.author.id in siege_stopper_dic.keys() and person_dict['delays'] < 3:
        person_dict['active_delta'] += timedelta(minutes=minutes)
        await channel.send('Stopped delayed by '+str(minutes)+' minutes '+str(person_dict['time'] + person_dict['active_delta']))

        person_dict['delays'] += 1
        if person_dict['delays'] == 3:
            await channel.send('This is the last time you can delay me, use it wisely.')
        elif person_dict['delays'] == 2:
            await channel.send('You are on your second delay.')
    else:
        await channel.send('Soz you used all your delays. Now buzz off.')

@will_sleep.error
async def will_sleep_error(ctx, error):
    print("@Error:", ctx.message.content, error, ctx.guild, sep=' | ')
    channel = ctx.channel

    await channel.send("Hi! Command 'will_sleep' says: "+str(error))

@client.command(pass_context=True, brief="Returns emoji IDs of the server and channel ID.")
async def get_ids(ctx):
    print(str(datetime.now()) + " get_emojis ran by " + str(ctx.message.author))
    channel = ctx.channel

    await channel.send(str(channel.guild.emojis) + '\nChannel ID: '+ str(channel.id) + '\nGuild ID: ' + str(ctx.guild.id))

@client.command(pass_context=True,  aliases=['remindme'], brief='Reminds you at specificed time (-remindme "date/time" @tags msg)', 
    help='example: -remindme "12pm EST March 12" @roboto all hail')
async def schping(ctx, time: str, *args):
    print(str(datetime.now()) + " remindme ran by " + str(ctx.message.author))
    channel = ctx.channel

    date = dateparser.parse(time, languages=['en'])
    if date == None:
        await channel.send("dateparser did not understand you")
        return

    #msg parsing
    msg = ""
    for arg in args:
        msg += arg + ' '
    if len(msg) == 0:
        msg = "Hey, it's your reminder speaking."

    tz_string = ' ({})'.format(str(date.tzinfo)) if date.tzinfo != None else ''
    time_code = date.strftime("%H:%M on %B %-d, %Y")
    await channel.send(msg+'\nI will remind you at ' + time_code + tz_string)
    
    if len(tz_string) > 0:
        date = (date - date.tzinfo.utcoffset(date) + timedelta(hours=8)).replace(tzinfo=None)
        time_code = date.strftime("%H:%M on %B %-d, %Y")
        await channel.send('AKA '+time_code+' HKT')

    #op to save time only later
    uni_time_triggers[time_code] = {ctx.message.author.id: {'name': ctx.message.author.name, 'msg': msg, 'channel': channel}}

@client.command(pass_context=True,  aliases=['listreminders'], brief="List all scheduled pings/reminders on specified day")
async def listsch(ctx, *args):
    print(str(datetime.now()) + " lssch ran by " + str(ctx.message.author))
    channel = ctx.channel

    await channel.send("Temporarily disabled soz")
    return

    # todo show only by server

    time = ""
    for arg in args:
        time += arg + ' '

    if time == 'all ' and str(ctx.message.author) == PrivateVals.author:
        msg_block = ''
        for i, c in enumerate(str(uni_time_triggers)):
            if i%2000 == 0 and i != 0:
                await channel.send(msg_block)
                msg_block = ''
            else:
                msg_block += c
        await channel.send(msg_block)

    date = dateparser.parse(time, languages=['en'])
    if date == None:
        await channel.send("dateparser did not understand you")
        return

    tz_string = ' ({})'.format(str(date.tzinfo)) if date.tzinfo != None else ''
    if len(tz_string) > 0:
        date = (date - date.tzinfo.utcoffset(date) + timedelta(hours=8)).replace(tzinfo=None)
    time_code = date.strftime("%B %-d, %Y")

    msg_block = ''
    flag = False
    await channel.send(time_code)
    for time_key in uni_time_triggers:
        if time_key.endswith(time_code):
            for user_key in uni_time_triggers[time_key]:
                flag = True
                msg_block += '**'+uni_time_triggers[time_key][user_key]['name']+'**\n'
                msg_block += time_key+': '+uni_time_triggers[time_key][user_key]['msg']+'\n'

    if flag:
        await channel.send(msg_block)
    else:
        await channel.send("Nothing found.")

@client.command(pass_context=True,  aliases=['delreminder'], brief="Delete scheduled ping/reminder of a given time")
async def delping(ctx, *args):
    print(str(datetime.now()) + " remindme ran by " + str(ctx.message.author))
    channel = ctx.channel

    time = ""
    for arg in args:
        time += arg + ' '

    date = dateparser.parse(time, languages=['en'])
    if date == None:
        await channel.send("dateparser did not understand you")
        return

    tz_string = ' ({})'.format(str(date.tzinfo)) if date.tzinfo != None else ''
    if len(tz_string) > 0:
        date = (date - date.tzinfo.utcoffset(date) + timedelta(hours=8)).replace(tzinfo=None)
    time_code = date.strftime("%H:%M on %B %-d, %Y")

    if time_code in uni_time_triggers:
        for user_id in uni_time_triggers[time_code]:
            if ctx.message.author.id == user_id:
                del uni_time_triggers[time_code][user_id]
                await channel.send("Delete successful")
                return

    await channel.send("You do not own any reminder at "+time_code)

'''
stuff to do:
command ran function
error outputs to chat if arguments are wrong
ai stuff
refactor to be class based

background_loop optimization, await/sch
redis/memcache 

commands:
siege_stopper
tz conversion
last.fm hook

functions to make
'''

#client.loop.create_task(last_seen_background())
client.run(PrivateVals.token)

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
    void = client.get_channel(PrivateVals.void)
    code = str(ctx).split(" ")
    if code[2] + code[3] == "notfound":
        await channel.send("User not found. (Capitalization is required.)")
    else:
        await void.send("INFO ERROR:")
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
    void = client.get_channel(PrivateVals.void)
    code = str(ctx).split(" ")
    if code[2] + code[3] == "notfound.":
        await channel.send(ctx)
    else:
        await void.send("CHAN ERROR:")
        await void.send(ctx)
'''
