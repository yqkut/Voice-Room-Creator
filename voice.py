import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.voice_states = True

bot = commands.Bot(command_prefix='ur prefix', intents=intents)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="https://github.com/yqkut"))

@bot.event
async def on_voice_state_update(member, before, after):
    waiting_room_channel_id = 1234567890
    category_id = 1234567890
    
    user_name = member.display_name
    
    user_channel_id = after.channel.id if after.channel else None
    
    if user_channel_id == waiting_room_channel_id:
        guild = member.guild
        category = discord.utils.get(guild.categories, id=category_id)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=True),
            member: discord.PermissionOverwrite(connect=True, mute_members=True)
        }
        
        channel = await category.create_voice_channel(f"💭・ {user_name}'s Room", overwrites=overwrites)
        await member.move_to(channel)
        
    elif before.channel and before.channel.category_id == category_id:
        if len(before.channel.members) == 0:
            await before.channel.delete()

bot.run("ur token")