import discord
from discord.ext import commands, tasks
from discord.ui import Modal, View, Button, TextInput
from datetime import datetime

intents = discord.Intents.default()
intents.voice_states = True
bot = commands.Bot(command_prefix='!', intents=intents)

CATEGORY_ID = 12345678910  # add the id of the category where the vc rooms will occur here
TEXT_CHANNEL_ID = 12345678910  # add the id of the text channel here, where there will be a button for users to create their own vc channels

class CustomChannelModal(Modal):
    def __init__(self):
        super().__init__(title="Create Custom Channel")
        self.channel_name = TextInput(label="Channel Name", placeholder="Enter channel name here dude")
        self.add_item(self.channel_name)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("Please choose if the channel should be locked.", view=LockChoiceView(self.channel_name.value), ephemeral=True)

class LockChoiceView(View):
    def __init__(self, channel_name):
        super().__init__(timeout=60)
        self.channel_name = channel_name

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.danger)
    async def lock_channel(self, interaction: discord.Interaction, button: Button):
        await self.create_channel(interaction, lock_channel=True)
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.success)
    async def unlock_channel(self, interaction: discord.Interaction, button: Button):
        await self.create_channel(interaction, lock_channel=False)
        self.stop()

    async def create_channel(self, interaction: discord.Interaction, lock_channel: bool):
        category = discord.utils.get(interaction.guild.categories, id=CATEGORY_ID)
        if not category:
            await interaction.response.send_message("Category not found.", ephemeral=True)
            return

        member = interaction.user

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(connect=not lock_channel),
            member: discord.PermissionOverwrite(connect=True, mute_members=True, manage_channels=True)
        }

        try:
            channel = await category.create_voice_channel(self.channel_name, overwrites=overwrites)
        except Exception as e:
            await interaction.response.send_message(f"Error occurred while creating the channel: {e}", ephemeral=True)
            return

        if member.voice:
            await member.move_to(channel)
        await interaction.response.send_message(f"Custom channel '{self.channel_name}' created successfully!", ephemeral=True)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == interaction.user

    async def on_timeout(self) -> None:
        self.stop()

    async def on_error(self, interaction: discord.Interaction, error: Exception, item, /) -> None:
        await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

async def send_create_channel_button(channel):
    class CreateChannelView(View):
        @discord.ui.button(label="Create Room", style=discord.ButtonStyle.primary)
        async def create_channel_button(self, interaction: discord.Interaction, button: Button):
            await interaction.response.send_modal(CustomChannelModal())

    view = CreateChannelView()
    await channel.send("Click the button below to create a custom voice channel:", view=view)

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')
    await bot.change_presence(activity=discord.Game(name="https://yakut.lol"))
    
    channel = bot.get_channel(TEXT_CHANNEL_ID)
    if channel:
        send_channel_button.start(channel)
    else:
        print(f"Text channel with ID {TEXT_CHANNEL_ID} not found.")

@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.id == TEXT_CHANNEL_ID:
        guild = member.guild
        category = discord.utils.get(guild.categories, id=CATEGORY_ID)
        if not category:
            print(f"Category with ID {CATEGORY_ID} not found.")
            return
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=True),
            member: discord.PermissionOverwrite(connect=True, mute_members=True, manage_channels=True)
        }
        
        channel = await category.create_voice_channel(f"{member.display_name}'s Room", overwrites=overwrites)

        await member.move_to(channel)
        
    if before.channel and before.channel.category_id == CATEGORY_ID:
        if len(before.channel.members) == 0:
            try:
                before_channel = await before.channel.guild.fetch_channel(before.channel.id)
                await before_channel.delete()
            except discord.NotFound:
                print(f"Channel {before.channel.name} not found or already deleted.")
            except discord.Forbidden:
                print(f"Bot does not have permission to delete channel {before.channel.name}.")

@bot.command()
async def create_channel(ctx):
    modal = CustomChannelModal()
    await ctx.send_modal(modal)

@tasks.loop(minutes=3)
async def send_channel_button(channel):
    await channel.purge(limit=10)
    await send_create_channel_button(channel)

bot.run("ur bot token")
