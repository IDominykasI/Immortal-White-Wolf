import os
import discord
from discord.ext import commands
from threading import Thread
from flask import Flask

# =======================
# Flask (Web service)
# =======================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# =======================
# Global Data
# =======================
splits = {}
balances = {}  # <<< money bank

# =======================
# Discord Bot Setup
# =======================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# =======================
# Events
# =======================
@bot.event
async def on_ready():
    print(f"Joined as {bot.user}")
    try:
        synced = await tree.sync()
        print(f"Synchronized {len(synced)} slash commands")
    except Exception as e:
        print("Sync error:", e)

# ============================================================
# /balance COMMAND — check how much money the user has
# ============================================================
@tree.command(name="balance", description="Check how much money you have")
async def balance(interaction: discord.Interaction, user: discord.Member = None):

    # Jei user nepaduotas – rodo paties vartotojo balansą
    target = user or interaction.user
    user_id = str(target.id)

    amount = balances.get(user_id, 0)

    await interaction.response.send_message(
        f"💰 **{target.display_name}** has **{amount}M**",
        ephemeral=True
    )

# ============================================================
# /add_money COMMAND — Officer ONLY
# ============================================================
@tree.command(name="add-money", description="Add money (Officer only)")
async def add_money(
    interaction: discord.Interaction,
    user: discord.Member,
    amount: float
):

    # Officer role check
    officer_role = discord.utils.get(interaction.guild.roles, name="Officer")
    if officer_role not in interaction.user.roles:
        await interaction.response.send_message(
            "❌ This command can only be used by **Officers**!",
            ephemeral=True
        )
        return

    # Add money
    user_id = str(user.id)
    balances[user_id] = balances.get(user_id, 0) + amount

    await interaction.response.send_message(
        f"✅ Added **{amount}M** to {user.mention}. "
        f"Now he has **{balances[user_id]}M**."
    )

# ============================================================
# /remove_money COMMAND — Officer ONLY
# ============================================================
@tree.command(name="remove-money", description="Remove money (Officer only)")
async def remove_money(
    interaction: discord.Interaction,
    user: discord.Member,
    amount: float
):

    # Officer role check
    officer_role = discord.utils.get(interaction.guild.roles, name="Officer")
    if officer_role not in interaction.user.roles:
        await interaction.response.send_message(
            "❌ This command can only be used by **Officers**!",
            ephemeral=True
        )
        return

    user_id = str(user.id)
    current_balance = balances.get(user_id, 0)

    # Cannot remove more than the user has
    if amount > current_balance:
        await interaction.response.send_message(
            f"❌ {user.mention} has only **{current_balance}M**. "
            f"Can't remove **{amount}M**!",
            ephemeral=True
        )
        return

    # Remove money
    balances[user_id] = current_balance - amount

    await interaction.response.send_message(
        f"🟥 Removed **{amount}M** from {user.mention}. "
        f"Now he has **{balances[user_id]}M**."
    )

# ============================================================
# /split COMMAND — Your original code
# ============================================================
@tree.command(name="split", description="Start loot split")
async def split(
    interaction: discord.Interaction,
    total_amount: float,
    percentage: float,
    repairs: float,
    accounting: float,
    members: str
):
    guild = interaction.guild
    user_mentions = [m.strip() for m in members.split()]
    selected_members = []

    for m in user_mentions:
        if m.startswith("<@") and m.endswith(">"):
            user_id = int(m[2:-1].replace("!", ""))
            member = guild.get_member(user_id)
            if member:
                selected_members.append(member)

    if not selected_members:
        await interaction.response.send_message("❌ No valid members specified!", ephemeral=True)
        return

    final_amount = round((total_amount * percentage / 100) - repairs - accounting, 2)

    if final_amount < 0:
        await interaction.response.send_message("❌ Final amount cannot be negative!", ephemeral=True)
        return

    per_share = round(final_amount / len(selected_members), 2)

    embed = discord.Embed(
        title="💰 Loot Split Breakdown 💰",
        color=discord.Color.gold()
    )
    embed.add_field(name="📣 Started by", value=interaction.user.mention, inline=False)
    embed.add_field(name="Total estimated value", value=f"💰 {total_amount}M", inline=False)
    embed.add_field(name="Guild buys for", value=f"💳 {percentage}% of estimated value", inline=False)
    embed.add_field(name="Repairs", value=f"🔧 {repairs}M", inline=False)
    embed.add_field(name="Accounting fees", value=f"📘 {accounting}M", inline=False)
    embed.add_field(name="Final amount to split", value=f"💰 {final_amount}M", inline=False)
    embed.add_field(name="Each player's share", value=f"💸 {per_share}M", inline=False)

    split_id = str(interaction.id)
    splits[split_id] = {
        "members": {str(m.id): False for m in selected_members},
        "each": per_share,
        "message_id": None,
        "channel_id": interaction.channel.id,
    }

    msg = await interaction.channel.send(
        content=f"Hello {' '.join(m.mention for m in selected_members)}, you are part of this split.",
        embed=embed,
    )

    splits[split_id]["message_id"] = msg.id
    await interaction.response.send_message("✅ Split created!", ephemeral=True)

# =======================
# Run
# =======================
if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.environ["DISCORD_TOKEN"])
