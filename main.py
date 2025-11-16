import os
import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput

# =======================
# Intents ir bot
# =======================
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# =======================
# Globalūs duomenys
# =======================
applications = {}  # Laikys paraiškas: {user_id: {character_name, reason, status}}

# =======================
# Modal paraiškai
# =======================
class ApplicationModal(Modal):
    def __init__(self):
        super().__init__(title="Guild Application")
        self.add_item(TextInput(label="Character name", placeholder="Enter your character's name"))
        self.add_item(TextInput(label="Why do you want to join?", style=discord.TextStyle.paragraph))

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        applications[user_id] = {
            "character_name": self.children[0].value,
            "reason": self.children[1].value,
            "status": "pending"
        }

        await interaction.response.send_message("✅ Application submitted!", ephemeral=True)

        # Siųsti embed į moderatorių channel
        channel = discord.utils.get(interaction.guild.text_channels, name="applications")
        if channel:
            embed = discord.Embed(
                title=f"New Application from {interaction.user}",
                color=discord.Color.blue()
            )
            embed.add_field(name="Character", value=self.children[0].value)
            embed.add_field(name="Reason", value=self.children[1].value)
            await channel.send(embed=embed, view=ApplicationApprovalView(user_id))

# =======================
# View moderatoriui
# =======================
class ApplicationApprovalView(View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: Button):
        if self.user_id not in applications:
            await interaction.response.send_message("⚠️ Application not found!", ephemeral=True)
            return
        applications[self.user_id]["status"] = "accepted"
        await interaction.response.send_message(f"✅ Application accepted for <@{self.user_id}>", ephemeral=False)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: Button):
        if self.user_id not in applications:
            await interaction.response.send_message("⚠️ Application not found!", ephemeral=True)
            return
        applications[self.user_id]["status"] = "rejected"
        await interaction.response.send_message(f"❌ Application rejected for <@{self.user_id}>", ephemeral=False)

# =======================
# Slash komanda paraiškai
# =======================
@tree.command(name="apply", description="Submit a guild application")
async def apply(interaction: discord.Interaction):
    await interaction.response.send_modal(ApplicationModal())

# =======================
# Įvykiai
# =======================
@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
    await tree.sync()
    print("Slash commands synchronized.")

# =======================
# Paleidimas
# =======================
if __name__ == "__main__":
    bot.run(os.environ["DISCORD_TOKEN"])
