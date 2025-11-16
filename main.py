import os
import threading
import discord
from discord.ext import commands
from discord.ui import View, Button
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
# Button View
# ======================================
class SimpleButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Click me!", style=discord.ButtonStyle.green)
    async def button_callback(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("You clicked the button!", ephemeral=True)

# ======================================
# Slash komanda (GUILD ONLY – instant update)
# ======================================
@bot.tree.command(
    name="send_embed",
    description="Send an embed with a button",
    guild=discord.Object(GUILD_ID)
)
async def send_embed(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Hello!",
        description="This is a simple embed with a button.",
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

    # Sync tik tavo serveriui — bus iškart
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
