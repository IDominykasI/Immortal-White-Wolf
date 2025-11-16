import os
import threading
import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, InputText
from flask import Flask

# ======================================
# Flask serveris (Render keep-alive)
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
GUILD_ID = 1183116557505798324  # tavo serverio ID

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ======================================
# MODAL (forma)
# ======================================
class ApplicationForm(Modal, title="Guild Application Form"):

    in_game_name = InputText(
        label="Your in-game name",
        placeholder="Write your IGN...",
        required=True
    )

    role = InputText(
        label="Your main role/class",
        placeholder="Example: Healer / DPS / Tank",
        required=True
    )

    experience = InputText(
        label="How long have you been playing?",
        style=discord.InputTextStyle.long,
        placeholder="Describe your experience...",
        required=True
    )

    async def callback(self, interaction: discord.Interaction):
        """Čia gauni atsakymus iš formos"""

        response_msg = (
            f"**New Application Submitted**\n"
            f"**IGN:** {self.in_game_name.value}\n"
            f"**Role:** {self.role.value}\n"
            f"**Experience:** {self.experience.value}"
        )

        # Bandome siųsti į DMs
        try:
            await interaction.user.send(response_msg)
            await interaction.response.send_message(
                "Your application has been submitted. Check your DMs.",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "Application received, but I could not DM you. Your DMs are closed.",
                ephemeral=True
            )

# ======================================
# Button View
# ======================================
class SimpleButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green)
    async def button_callback(self, interaction: discord.Interaction, button: Button):
        modal = ApplicationForm()
        await interaction.response.send_modal(modal)

# ======================================
# Slash komanda (GUILD ONLY)
# ======================================
@bot.tree.command(
    name="send_embed",
    description="Send an embed with a button",
    guild=discord.Object(GUILD_ID)
)
async def send_embed(interaction: discord.Interaction):

    embed = discord.Embed(
        title="Guild Recruitment – Apply Here",
        description="Click the button below to start your application.",
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
# Paleidimas
# ======================================
if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    bot.run(os.environ["DISCORD_TOKEN"])
