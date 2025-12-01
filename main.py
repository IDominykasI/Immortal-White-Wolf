import os
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, Button
from threading import Thread
from flask import Flask

# =======================
# Flask dalis (Web service)
# =======================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# =======================
# Globalūs duomenys
# =======================
splits = {}

# =======================
# Discord dalis
# =======================
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# =======================
# Mygtukų + dropdown View
# =======================
class SplitView(View):
    def __init__(self, split_id: str, starter_id: int, guild: discord.Guild):
        super().__init__(timeout=None)
        self.split_id = split_id
        self.starter_id = starter_id
        self.guild = guild

# =======================
# Įvykiai
# =======================
@bot.event
async def on_ready():
    print(f"Joined as {bot.user}")
    try:
        synced = await tree.sync()
        print(f"Slash commands synchronized ({len(synced)})")
    except Exception as e:
        print(e)


# =======================
# PADARYTA NAUJA /split KOMANDA
# =======================
@tree.command(name="split", description="Start loot split")
async def split(
    interaction: discord.Interaction,
    Total_amount: float,
    Repairs: float,
    Accounting_fees: float,
    Percentage: float,
    members: str
):
    guild = interaction.guild
    user_mentions = [m.strip() for m in members.split()]
    selected_members = []

    # Parse players
    for m in user_mentions:
        if m.startswith("<@") and m.endswith(">"):
            user_id = int(m[2:-1].replace("!", ""))
            member = guild.get_member(user_id)
            if member:
                selected_members.append(member)

    # Final amount after deductions
    final_amount = round(Total_amount - Repairs - Accounting_fees * Percentage, 2)
    if final_amount < 0:
        await interaction.response.send_message("❌ Final amount cannot be negative!", ephemeral=True)
        return

    per_share = round(final_amount / len(selected_members), 2)

    # Build embed
    embed = discord.Embed(
        title="💰 Loot Split Breakdown 💰",
        color=discord.Color.gold()
    )
    embed.add_field(name="Total split amount", value=f"💰 {Total_amount}M", inline=False)
    embed.add_field(name="Repairs", value=f"🔧 {Repairs}M", inline=False)
    embed.add_field(name="Accounting fees", value=f"📘 {Accounting_fees}M", inline=False)
    embed.add_field(name="Guild buying for % of estm", value=f"📘 {Percentage}M", inline=False)
    embed.add_field(name="Final amount to split", value=f"💵 {Final_amount}M", inline=False)
    embed.add_field(name="Each player's share", value=f"💰 {per_share}M", inline=False)
    embed.add_field(name="📣 Started by", value=interaction.user.mention, inline=False)

    # Save split data
    split_id = str(interaction.id)
    splits[split_id] = {
        "members": {str(m.id): False for m in selected_members},
        "Total_amount": Total_amount,
        "Repairs": Repairs,
        "Accounting_fees": Accounting_fees,
        "Final_amount": Final_amount,
        "each": per_share,
        "message_id": None,
        "channel_id": interaction.channel.id,
        "starter": interaction.user.id
    }

    # Create view
    view = SplitView(split_id, interaction.user.id, guild)
    msg = await interaction.channel.send(
        content=f"Hello {' '.join(m.mention for m in selected_members)}, the split has started.",
        embed=embed,
        view=view
    )

    splits[split_id]["message_id"] = msg.id


# =======================
# Paleidimas
# =======================
if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.environ["DISCORD_TOKEN"])
