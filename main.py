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
GUILD_ID = 1183116557505798324          # tavo serverio ID
APPLICATIONS_CHANNEL_ID = 123456789012345678  # pakeisk į savo applications kanalo ID

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ======================================
# Modal forma
# ======================================
class ApplicationModal(Modal):
    def __init__(self, user: discord.Member):
        super().__init__(title="Guild Application")
        self.user = user

        # Pridėti klausimus (galima pridėti daugiau)
        self.add_item(TextInput(
            label="1. What's your in-game name?",
            placeholder="Enter your IGN...",
            style=discord.TextStyle.short
        ))
        self.add_item(TextInput(
            label="2. Why do you want to join?",
            placeholder="Enter your reason...",
            style=discord.TextStyle.paragraph
        ))

    async def on_submit(self, interaction: discord.Interaction):
        answers = [item.value for item in self.children]

        # Atsakymas vartotojui (ephemeral)
        await interaction.response.send_message(
            "✅ Your application has been submitted!", ephemeral=True
        )

        # Siunčiame į applications kanalą
        channel = bot.get_channel(APPLICATIONS_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title=f"New Application from {self.user}",
                color=discord.Color.green()
            )
            embed.add_field(name="1. In-game name", value=answers[0], inline=False)
            embed.add_field(name="2. Reason", value=answers[1], inline=False)
            await channel.send(embed=embed)
        else:
            print("Applications channel not found!")

# ======================================
# View su mygtuku
# ======================================
class SimpleButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green)
    async def button_callback(self, interaction: discord.Interaction, button: Button):
        # Atidarome modal formą tame pačiame kanale
        await interaction.response.send_modal(ApplicationModal(interaction.user))

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
        description="Click the button below to submit your application. Officers will review your submission shortly.",
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
