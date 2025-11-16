import os
import threading
import discord
from discord.ext import commands
from discord.ui import View, Button
from flask import Flask

# =======================
# Minimalus HTTP serveris Render (Flask)
# =======================
app = Flask(__name__)

@app.route("/", methods=["GET", "HEAD"])
def root():
    return {"status": "ok"}, 200

def run_server():
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, threaded=True)

# =======================
# Discord bot
# =======================
intents = discord.Intents.default()
intents.message_content = True  # Pakanka modalams, mygtukams, slash komandoms

bot = commands.Bot(command_prefix="!", intents=intents)

# =======================
# View su mygtuku
# =======================
class SimpleButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Click me!", style=discord.ButtonStyle.green)
    async def button_callback(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("You clicked the button!", ephemeral=True)

# =======================
# Slash komanda /send_embed
# =======================
@bot.tree.command(name="send_embed", description="Sends a simple embed with a button")
async def send_embed(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Hello!",
        description="This is a simple embed with a button below.",
        color=discord.Color.green()
    )
    view = SimpleButtonView()
    await interaction.response.send_message(embed=embed, view=view)

# =======================
# Eventai
# =======================
@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
    try:
        await bot.tree.sync()  # global sync
        print("Slash commands synchronized globally.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# =======================
# Paleidimas
# =======================
if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    bot.run(os.environ["DISCORD_TOKEN"])
