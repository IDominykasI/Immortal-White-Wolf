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
balances = {}  # money bank

# =======================
# Number formatting
# =======================
def format_full(n):
    return f"{int(n):,}"

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
# /balance
# ============================================================
@tree.command(name="balance", description="Check how much money you have")
async def balance(interaction: discord.Interaction, user: discord.Member = None):
    target = user or interaction.user
    user_id = str(target.id)
    amount = balances.get(user_id, 0)

    await interaction.response.send_message(
        f"💰 **{target.display_name}** has **{format_full(amount)}**",
        ephemeral=True
    )

# ============================================================
# /add-money — Officer only
# ============================================================
@tree.command(name="add-money", description="Add money (Officer only)")
async def add_money(interaction: discord.Interaction, user: discord.Member, amount: int):

    officer_role = discord.utils.get(interaction.guild.roles, name="Officer")
    if officer_role not in interaction.user.roles:
        await interaction.response.send_message(
            "❌ This command can only be used by Officers!",
            ephemeral=True
        )
        return

    user_id = str(user.id)
    balances[user_id] = balances.get(user_id, 0) + amount

    await interaction.response.send_message(
        f"✅ Added **{format_full(amount)}** to {user.mention}. "
        f"Now he has **{format_full(balances[user_id])}**."
    )

# ============================================================
# /remove-money — Officer only
# ============================================================
@tree.command(name="remove-money", description="Remove money (Officer only)")
async def remove_money(interaction: discord.Interaction, user: discord.Member, amount: int):

    officer_role = discord.utils.get(interaction.guild.roles, name="Officer")
    if officer_role not in interaction.user.roles:
        await interaction.response.send_message(
            "❌ This command can only be used by Officers!",
            ephemeral=True
        )
        return

    user_id = str(user.id)
    current_balance = balances.get(user_id, 0)

    if amount > current_balance:
        await interaction.response.send_message(
            f"❌ {user.mention} has only **{format_full(current_balance)}**. "
            f"Can't remove **{format_full(amount)}**!",
            ephemeral=True
        )
        return

    balances[user_id] = current_balance - amount

    await interaction.response.send_message(
        f"🟥 Removed **{format_full(amount)}** from {user.mention}. "
        f"Now he has **{format_full(balances[user_id])}**."
    )

# ============================================================
# /split
# ============================================================
@tree.command(name="split", description="Start loot split")
async def split(interaction: discord.Interaction, total_amount: int, repairs: int, members: str):

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

    # Final amount = 80% - repairs - 250k
    final_amount = (total_amount * 80 // 100) - repairs - 250000

    if final_amount < 0:
        await interaction.response.send_message("❌ Final amount cannot be negative!", ephemeral=True)
        return

    per_share = final_amount // len(selected_members)

    embed = discord.Embed(
        title="💰 Loot Split Breakdown 💰",
        color=discord.Color.gold()
    )

    embed.add_field(name="📣 Started by", value=interaction.user.mention, inline=False)
    embed.add_field(name="Total estimated value", value=f"💰 {format_full(total_amount)}", inline=False)
    embed.add_field(name="Guild buys for", value="💳 80% of estimated value", inline=False)
    embed.add_field(name="Repairs", value=f"🔧 {format_full(repairs)}", inline=False)
    embed.add_field(name="Accounting fees", value="📘 250,000", inline=False)
    embed.add_field(name="Final amount to split", value=f"💰 {format_full(final_amount)}", inline=False)
    embed.add_field(name="Each player's share", value=f"💸 {format_full(per_share)}", inline=False)

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
