import os
import threading
import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
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
intents.message_content = True  # pakanka modalams, buttonams ir slash komandoms

bot = commands.Bot(command_prefix="!", intents=intents)

# ======================================
# Modal forma
# ======================================
class ApplicationModal(Modal):
    def __init__(self):
        super().__init__(title="Guild Application")
        # Pridėti vieną klausimą (galima pridėti daugiau)
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

# ======================================
# View su mygtuku
# ======================================
class SimpleButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green)
    async def button_callback(self, interaction: discord.Interaction, button: Button):
        try:
            await interaction.user.send_modal(ApplicationModal())
            await interaction.response.send_message(
                "📬 Check your DMs to fill the application!", ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I cannot DM you. Please enable DMs from server members.", ephemeral=True
            )

# ======================================
# Slash komanda (guild-specific)
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
# on_ready event
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
