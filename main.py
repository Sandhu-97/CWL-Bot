import os
import pandas
import discord
from discord.ext import commands
import asyncio
import gspread
import time
from custom_logger import main_logger
from backend import get_category, add_reps, rep_overwrite, add_user_to_channel, get_league_default, get_league_logo
from keep_alive import keep_alive

gc = gspread.service_account(filename='credentials.json')
mastersheet = gc.open_by_key('1FTcrMhe71MQoLhhtJfjOfhCVxKcnOAF2GnDKqiEKUtg')
infosheet = mastersheet.worksheet('info')
penaltysheet = mastersheet.worksheet('penalty')

abbs = infosheet.col_values(3)[1:]
reps = infosheet.get('D2:F75')
df = pandas.DataFrame(data=reps, index=abbs, columns=['clan', 'rep1', 'rep2'])

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
async def createall(ctx:commands.Context, league:str, week:str):
    await ctx.send('***processing***')
    try:
        leaguesheet = mastersheet.worksheet(league)
    except:
        return
    
    weeks_cells = leaguesheet.findall(week, None, 3)
    category_name = f'{league.upper()} Week {week[1:]}'

    try:    
        guild = ctx.guild
        cat = await guild.create_category(name=category_name)
    except:
        await ctx.send('`ERROR: Unable to create category`')
        return
    
    everyone_role = discord.utils.get(guild.roles, id=1070556590505209897)
    applicant_role = discord.utils.get(guild.roles, name="applicant")
    admin_role = discord.utils.get(guild.roles, name='league admin')
    admin_overwrite = rep_overwrite()

    try:
        await cat.set_permissions(guild.me, overwrite=rep_overwrite())
        await cat.set_permissions(applicant_role, read_messages=False)
        await cat.set_permissions(admin_role, overwrite=admin_overwrite)
        await cat.set_permissions(everyone_role, read_messages=False)
    except Exception as e:
        await ctx.send('error')
        return

    for cell in weeks_cells:
        row = cell.row
        clan1 = leaguesheet.cell(row, 4).value
        clan2 = leaguesheet.cell(row, 5).value

        clan1name = df.loc[clan1]['clan']
        clan2name = df.loc[clan2]['clan']

        rep1_id = df.loc[clan1]['rep1']
        rep2_id = df.loc[clan1]['rep2']
        rep3_id = df.loc[clan2]['rep1']
        rep4_id = df.loc[clan2]['rep2']

        rep2, rep4 = '', ''
        try:
            rep1 = await bot.fetch_user(rep1_id)
        except:
            await ctx.send(f'`ERROR: Unable to find {clan1} rep with id {rep1_id}`')
        try:
            if rep2_id:
                rep2 = await bot.fetch_user(rep2_id)
        except:
            await ctx.send(f'`ERROR: Unable to find {clan1} rep with id {rep2_id}`')
        try:
            rep3 = await bot.fetch_user(rep3_id)
        except:
            await ctx.send(f'`ERROR: Unable to find {clan2} rep with id {rep3_id}`')
        try:
            if rep4_id:
                rep4 = await bot.fetch_user(rep4_id)
        except:
            await ctx.send(f'`ERROR: Unable to find {clan2} rep with id {rep4_id}`')

        try:
            channel = await cat.create_text_channel(f'{week} {clan1} {clan2}')
            logo_url = get_league_logo(league)
            default = get_league_default(league)

            embed = discord.Embed(title=f'{clan1name} vs {clan2name}', description=f'**{league.upper()} Week {week[1:]}**', color=discord.Colour.dark_gold())
            embed.set_thumbnail(url=logo_url)
            embed.add_field(name='Default Day', value=default, inline=False)

        except:
            await ctx.send(f'`Cannot create channel for {clan1} and {clan2}`')
            continue
            reps_msg = ''
        
        if rep2 and rep4:
            embed.add_field(name=f'{clan1} Reps', value=f'{rep1.name}#{rep1.discriminator}\n{rep2.name}#{rep2.discriminator}', inline=False)
            embed.add_field(name=f'{clan2} Reps', value=f'{rep3.name}#{rep3.discriminator}\n{rep4.name}#{rep4.discriminator}', inline=False)
            reps_msg = f'<{rep1.id}> <{rep2.id}> <{rep3.id}> <{rep4.id}>'

        elif rep2 and not rep4:
            embed.add_field(name=f'{clan1} Reps', value=f'{rep1.name}#{rep1.discriminator}\n{rep2.name}#{rep2.discriminator}', inline=False)
            embed.add_field(name=f'{clan2} Reps', value=f'{rep3.name}#{rep3.discriminator}', inline=False)
            reps_msg = f'<{rep1.id}> <{rep2.id}> <{rep3.id}>'

        elif not rep2 and rep4:
            embed.add_field(name=f'{clan1} Reps', value=f'{rep1.name}#{rep1.discriminator}', inline=False)
            embed.add_field(name=f'{clan2} Reps', value=f'{rep3.name}#{rep3.discriminator}\n{rep4.name}#{rep4.discriminator}', inline=False)
            reps_msg = f'<{rep1.id}> <{rep3.id}> <{rep4.id}>'

        await channel.send(content=reps_msg,embed=embed)
    
        overwrite = rep_overwrite()
        try:
            if rep1:
                await channel.set_permissions(rep1, overwrite=overwrite)
        except:
            await ctx.send(f'`Unable to add {clan1} rep 1 to the channel`')
        try:
            if rep2:
                await channel.set_permissions(rep2, overwrite=overwrite)
        except:
            await ctx.send(f'`Unable to add {clan1} rep 2 to the channel`')
        try:
            if rep3:
                await channel.set_permissions(rep3, overwrite=overwrite)
        except:
            await ctx.send(f'`Unable to add {clan2} rep 1 to the channel`')
        try:
            if rep4:
                await channel.set_permissions(rep4, overwrite=overwrite)
        except:
            await ctx.send(f'`Unable to add {clan2} rep 2 to the channel`')
        
        e = discord.Embed(description=f'Channel created for **{clan1name}** and **{clan2name}** at <#{channel.id}>', color=discord.Colour.dark_gold())
        await ctx.send(embed=e)
    await ctx.send('***processed***')
        
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

@bot.command()
async def penalty(ctx:commands.Context, clan:str, week:str, unrostered_players:int=0, suspended_players:int=0, behaviour_pp:int=0, late_spin:str='F', missed_spin:str='F'):
    clan = clan.upper()
    try:
        clan_row = penaltysheet.find(clan, in_column=1).row
    except:
        await ctx.send('`Invalid Clan`')
        return
    
    late_spin_pp, missed_spin_pp = 0, 0
    if late_spin in ('T', 't', 'True', 'true'):
        late_spin_pp = 2
    if missed_spin in ('T', 't', 'True', 'true'):
        missed_spin_pp = 4

    unrostered_players_pp = unrostered_players * 2
    suspended_players_pp = suspended_players * 2

    total_pp = unrostered_players_pp + suspended_players_pp + behaviour_pp + late_spin_pp + missed_spin_pp
    await ctx.send(f'''```
Unrostered Players Penalty: {unrostered_players_pp}
Suspended Players Penalty:  {suspended_players_pp}
Behaviour Penalty:          {behaviour_pp}
Late Spin Penalty:          {late_spin_pp}
Missed Spin Penalty:        {missed_spin_pp}
Total Penalty:              {total_pp}```''')

    try:
        col = int(week[1:])
        penaltysheet.update_cell(clan_row, col+1, total_pp)
    except:
        await ctx.send('`Unable to edit sheet`')
        main_logger.exception('unable to add pp to sheet')
        return
    await ctx.send('`Penalty points sheet has been updated`')

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
    await bot.start('OTM0MzIyODkwMzM2MjY4MzM5.Grdbm1.RINHbH_m3gAgRrVi5zmMuvkyCREuPN_IOjsy6I')
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

    