import os
import discord
from discord.ext import commands
import asyncio
import gspread
import time
from custom_logger import main_logger
from backend import get_category, add_reps, rep_overwrite, add_user_to_channel
from keep_alive import keep_alive

gc = gspread.service_account(filename='credentials.json')
mastersheet = gc.open_by_key('1FTcrMhe71MQoLhhtJfjOfhCVxKcnOAF2GnDKqiEKUtg')
infosheet = mastersheet.worksheet('info')


intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='cwl ', intents=intents)

@bot.event
async def on_ready():
    print(bot.user, 'is ready')

@bot.command()
async def ping(ctx):
    await ctx.send('`pong`')

@bot.command()
async def createall(ctx, league:str, week:str):
    await ctx.send('processing')
    try:
        leaguesheet = mastersheet.worksheet(league)
    except:
        return
    
    weeks_cells = leaguesheet.findall(week, None, 3)
    league_category = get_category(bot, leaguesheet)

    for cell in weeks_cells:
        row = cell.row
        clan1 = leaguesheet.cell(row, 4).value
        clan2 = leaguesheet.cell(row, 5).value

        clan1_row = infosheet.find(clan1, in_row=None, in_column=3).row
        clan1_rep1_id = infosheet.cell(clan1_row, 5).value
        clan1_rep2_id = infosheet.cell(clan1_row, 6).value

        clan2_row = infosheet.find(clan2, in_row=None, in_column=3).row
        clan2_rep1_id = infosheet.cell(clan2_row, 5).value
        clan2_rep2_id = infosheet.cell(clan2_row, 6).value

        overwrite = rep_overwrite()
        found_reps = False
        try:
            clan1_rep1 = await bot.fetch_user(int(clan1_rep1_id))
            clan1_rep2 = ''
            if clan1_rep2_id:
                clan1_rep2 = await bot.fetch_user(int(clan1_rep2_id))
            clan2_rep1 = await bot.fetch_user(int(clan2_rep1_id))
            clan2_rep2 = ''
            if clan2_rep2_id:
                clan2_rep2 = await bot.fetch_user(int(clan2_rep2_id))
            found_reps = True

        except:
            await ctx.send(f'`Unable to find {clan1} {clan2} reps in the server`')
        try:
            nego_channel = await league_category.create_text_channel(f'{week} {clan1} {clan2}')

        except:
            await ctx.send(f'`Unable to create channel for {clan1} and {clan2}`')

        try:
            if found_reps:
                await nego_channel.set_permissions(clan1_rep1, overwrite=overwrite)
                await nego_channel.set_permissions(clan2_rep1, overwrite=overwrite)
                
            if clan1_rep2:
                await nego_channel.set_permissions(clan1_rep2, overwrite=overwrite)
            if clan2_rep2:
                await nego_channel.set_permissions(clan2_rep2, overwrite=overwrite)
        except:
            await ctx.send('`Unable to add reps to the channel`')
        await ctx.send(f'`channel created for {clan1} and {clan2}`')
    await ctx.send('processed')
        
    time.sleep(1)

@bot.command()
async def channel(ctx, league:str, week:str, clan1:str, clan2:str):
    try:
        leaguesheet = mastersheet.worksheet(league)
    except:
        await ctx.send('invalid league name')

    league_category = get_category(bot, leaguesheet)

    try:
        channel = await league_category.create_text_channel(f'{week} {clan1} {clan2}')
    except:
        await ctx.send('`Unable to create channel`')
        main_logger.exception('Cannot create channel - cwl channel')
        return
    await ctx.send(f'`Success! Channel created at `<#{channel.id}>')

@bot.command()
async def addreps(ctx, channel: discord.TextChannel, *reps: discord.User):
    try:
        await add_reps(channel, reps)
    except:
        await ctx.send('`unable to add reps in the channel`')
        return
    else:
        await ctx.send('`Success! Reps added in the channel`')

# @bot.command()
# async def delreps(ctx, channel: discord.TextChannel):
#     members = channel.members

#     for member in members:
#         has_role = discord.utils.get(member.roles, name='Approved') is not None
        
#         if has_role:
#             await channel.set_permissions(member, read_messages=False)
#             await ctx.send(f'`Removed access from {member.name}`')
#     await ctx.send('`processed`')

@bot.command()
async def delreps(ctx, channel:discord.TextChannel, *reps: discord.Member):
    for rep in reps:
        await channel.set_permissions(rep, read_messages=False)
        await ctx.send(f'`Removed access from {rep.name}`')
    await ctx.send('`processed`')

@bot.command()
async def member(ctx, member: discord.Member=None):
    if not member:
        member = ctx.author
    name = member.name
    disc = member.discriminator
    id = member.id
    avatar = member.avatar
    joindate = str(member.joined_at)
    createdate = str(member.created_at)
    high_role = member.top_role

    embed = discord.Embed(title=f'{name}#{disc}', description=f'ID: **{id}**\n\nJoined Server: **{joindate[:19]}**\n\nJoined Discord: **{createdate[:19]}**\n\nHighest Role: **{high_role}**', colour=discord.Color.gold())
    if avatar:
        embed.set_thumbnail(url=avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def interview(ctx, user: discord.Member):
    interview_category_id = 1088412327562453053
    admin_category_id = 1088412154530635836

    interview_category = bot.get_channel(interview_category_id)
    admin_category = bot.get_channel(admin_category_id)

    name = user.name
    created_at = str(user.created_at)
    id = user.id
    disc = user.discriminator

    try:
        interview_channel = await interview_category.create_text_channel(name)
        admin_channel = await admin_category.create_text_channel(name)
    except:
        await ctx.send('`Unable to create channels`')
        return
    
    try:
        await add_user_to_channel(interview_channel, user)
    except:
        await ctx.send('`Unable to add user in the channel`')
        return
    
    await admin_channel.send(f"```Name: {name}#{disc}\nId: {id}\nCreated at: {created_at[:19]}```")
    await interview_channel.send('''```
Welcome and congratulations for advancing to the next step of the admin application! Currently we are looking for admins who are active, driven and willing to work. 

Please take a few moments to read through the questions and provide a thorough response. Some are similar to the application, but we are looking for a few more details. 

• What strengths can you bring to the admin team?

• Do you have any specific skills that you may qualify you for this job? (E.g. Discord, warmatch, top ten attacker, Google sheets, Social media, Content creation, gfx)

• What challenges do you see for yourself if you are selected as an admin?

• If you could change any one thing in the CWL, what would it be and why?

•Roughly how much time do you have to spend on discord, more specifically CWL?

• What time zone are you from? 

•Does it suit you to dedicate time and do a bigger task, or pop on and off during the day as needed?```''')
    await ctx.send('`processed`')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        message = '`ERROR: Missing Arguement(s)`'  
    if isinstance(error, commands.CommandNotFound):       
        message = ''    
    if isinstance(error, commands.CommandInvokeError):
        message = "`ERROR: Internal Error`"
        main_logger.exception(f'INVOKE ERROR {error}')
    if isinstance(error, discord.errors.NotFound):
        message = "`ERROR: Not Found`" 
    if isinstance(error, gspread.WorksheetNotFound):
        message = '`ERROR: Invalid League Name`'
        main_logger.exception('WORKSHEET NOT FOUND')

    await ctx.send(message)
token = os.environ['TOKEN']   
async def main():
    keep_alive()
    await bot.start(token)
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

    