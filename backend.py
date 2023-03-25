import discord
import gspread
from discord.ext import commands
from custom_logger import backend_logger

def rep_overwrite():
    overwrite = discord.PermissionOverwrite()
    overwrite.read_messages = True
    overwrite.send_messages = True
    overwrite.read_message_history = True
    overwrite.attach_files = True
    overwrite.embed_links = True
    return overwrite
    
def get_category(bot:discord.Client, worksheet: gspread.Worksheet):
    category_id = worksheet.cell(1, 6).value
    try:
        league_category = bot.get_channel(int(category_id))
        return league_category
    except:
        backend_logger.exception('Cannot get league category')

async def add_reps(channel: discord.TextChannel, reps):
    overwrite = rep_overwrite()
    try:
        for rep in reps:
            await channel.set_permissions(rep, overwrite=overwrite)
            await channel.send(f'welcome to the channel {rep.mention}')
    except:
        backend_logger.exception('Cannot add reps')

def get_rep_ids(worksheet: gspread.Worksheet, clan1: str, clan2: str):

    clan1_row = worksheet.find(clan1).row
    clan2_row = worksheet.find(clan2).row

    rep1_id = worksheet.cell(clan1_row, 5).value
    rep2_id = worksheet.cell(clan1_row, 6).value
    rep3_id = worksheet.cell(clan2_row, 5).value
    rep4_id = worksheet.cell(clan2_row, 6).value
    return int(rep1_id), int(rep2_id), int(rep3_id), int(rep4_id)

async def create_channel(ctx: commands.Context ,category: discord.CategoryChannel, channelname, *reps):
    try:
        channel = await category.create_text_channel(channelname)
        await channel.send('add reps hereee')
    except:
        backend_logger.exception('unable to create channel')

    try:
        await add_reps(channel, reps)
    except:
        await ctx.send('`unable to add reps in the channel`')
        return
    else:
        await ctx.send('`Success! Reps added in the channel`')

async def add_user_to_channel(channel: discord.TextChannel, user:discord.User):
    overwrite = rep_overwrite()
    try:
        await channel.set_permissions(user, overwrite=overwrite)
    except:
        backend_logger.exception('cannot add user to the channel')

