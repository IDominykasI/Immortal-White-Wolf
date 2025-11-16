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
GUILD_ID = 1183116557505798324
APPLICATIONS_CHANNEL_ID = 123456789012345678  # replace with your channel ID
MEMBER_ROLE_ID = 123456789012345678           # replace with your member role ID

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ======================================
# Modal form for applicants
# ======================================
class ApplicationModal(Modal):
    def __init__(self, user: discord.Member):
        super().__init__(title="Guild Application")
        self.user = user
        self.add_item(TextInput(
            label="1. What's your in-game name?",
            placeholder="Enter your IGN here...",
            style=discord.TextStyle.short
        ))

    async def on_submit(self, interaction: discord.Interaction):
        answer = self.children[0].value
        await interaction.response.send_message(
            f"✅ Thanks! Your answer: `{answer}`", ephemeral=True
        )

        # Send to applications channel with officer buttons
        guild = bot.get_guild(GUILD_ID)
        channel = guild.get_channel(APPLICATIONS_CHANNEL_ID)
        embed = discord.Embed(
            title="New Guild Application",
            description=f"**Applicant:** {self.user.mention}\n**IGN:** {answer}",
            color=discord.Color.green()
        )
        view = OfficerReviewView(self.user)
        await channel.send(embed=embed, view=view)

# ======================================
# View with button to start application
# ======================================
class SimpleButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green)
    async def button_callback(self, interaction: discord.Interaction, button: Button):
        try:
            await interaction.user.send_modal(ApplicationModal(interaction.user))
            await interaction.response.send_message(
                "📬 Check your DMs to fill the application!", ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I cannot DM you. Please enable DMs from server members.", ephemeral=True
            )

# ======================================
# Officer buttons (Accept/Decline)
# ======================================
class OfficerReviewView(View):
    def __init__(self, applicant: discord.Member):
        super().__init__(timeout=None)
        self.applicant = applicant

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept_button(self, interaction: discord.Interaction, button: Button):
        guild = bot.get_guild(GUILD_ID)
        member = guild.get_member(self.applicant.id)
        if member:
            await member.add_roles(discord.Object(MEMBER_ROLE_ID))
            await interaction.response.send_message(
                f"✅ {self.applicant} has been given the Member role.", ephemeral=True
            )
            await interaction.message.delete()
        else:
            await interaction.response.send_message(
                "❌ Member not found.", ephemeral=True
            )

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline_button(self, interaction: discord.Interaction, button: Button):
        try:
            await self.applicant.send("❌ Your application was declined.")
        except discord.Forbidden:
            pass
        await interaction.response.send_message(
            f"❌ {self.applicant}'s application declined.", ephemeral=True
        )
        await interaction.message.delete()

# ======================================
# Slash command to send the embed in apply-here channel
# ======================================
@bot.tree.command(
    name="send_embed",
    description="Send an embed with a button",
    guild=discord.Object(GUILD_ID)
)
async def send_embed(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Guild Recruitment – Apply Here",
        description="Click the button below to submit your application. An officer will review your ticket shortly.",
        color=discord.Color.green()
    )
    view = SimpleButtonView()
    await interaction.response.send_message(embed=embed, view=view)

# ======================================
# Bot ready
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
# Run bot + Flask server
# ======================================
if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    bot.run(os.environ["DISCORD_TOKEN"])
