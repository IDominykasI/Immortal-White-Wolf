import os
import threading
import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from flask import Flask

# ======================================
# Flask server (Render keep-alive)
# ======================================
app = Flask(__name__)

@app.route("/", methods=["GET", "HEAD"])
def root():
    return {"status": "ok"}, 200

def run_server():
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, threaded=True)

# ======================================
# Discord bot
# ======================================
GUILD_ID = 1183116557505798324  # your server ID
APPLICATIONS_CHANNEL_ID = 1439593741898747915  # replace with your applications channel ID
MEMBER_ROLE_ID = 1183366708073877566  # replace with the Member role ID

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # needed to assign roles

bot = commands.Bot(command_prefix="!", intents=intents)

# ======================================
# Modal
# ======================================
class ApplicationModal(Modal):
    def __init__(self, applicant: discord.Member):
        super().__init__(title="Guild Application")
        self.applicant = applicant
        # Add questions
        self.add_item(TextInput(
            label="1. What's your in-game name?",
            placeholder="Enter your IGN here...",
            style=discord.TextStyle.short
        ))

    async def on_submit(self, interaction: discord.Interaction):
        answer = self.children[0].value
        # Send application to applications channel with buttons
        channel = bot.get_channel(APPLICATIONS_CHANNEL_ID)
        embed = discord.Embed(
            title="New Guild Application",
            description=f"Applicant: {self.applicant.mention}\n**IGN:** {answer}",
            color=discord.Color.green()
        )
        view = DecisionView(self.applicant)
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(
            "✅ Your application has been submitted!", ephemeral=True
        )

# ======================================
# Decision View
# ======================================
class DecisionView(View):
    def __init__(self, applicant: discord.Member):
        super().__init__(timeout=None)
        self.applicant = applicant

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: Button):
        role = interaction.guild.get_role(MEMBER_ROLE_ID)
        if role:
            await self.applicant.add_roles(role)
        await self.applicant.send("🎉 Your application has been accepted! You now have the Member role.")
        await interaction.message.delete()  # remove application message
        await interaction.response.send_message("Application accepted!", ephemeral=True)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: Button):
        await self.applicant.send("❌ Your application has been declined.")
        await interaction.message.delete()  # remove application message
        await interaction.response.send_message("Application declined!", ephemeral=True)

# ======================================
# Button View
# ======================================
class SimpleButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green)
    async def button_callback(self, interaction: discord.Interaction, button: Button):
        # Show modal in channel (cannot send modal via DM)
        await interaction.response.send_modal(ApplicationModal(interaction.user))

# ======================================
# Slash command to send embed
# ======================================
@bot.tree.command(
    name="send_embed",
    description="Send an embed with a button",
    guild=discord.Object(GUILD_ID)
)
async def send_embed(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Guild Recruitment – Apply Here",
        description="Click the button below to submit your application. Officers will review it shortly.",
        color=discord.Color.green()
    )
    view = SimpleButtonView()
    await interaction.response.send_message(embed=embed, view=view)

# ======================================
# on_ready
# ======================================
@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
    guild = discord.Object(GUILD_ID)
    try:
        await bot.tree.sync(guild=guild)
        print("Slash commands synced for this guild ONLY.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# ======================================
# Run bot
# ======================================
if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    bot.run(os.environ["DISCORD_TOKEN"])
