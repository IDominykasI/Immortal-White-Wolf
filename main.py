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

        if split_id in splits:
            member_options = []
            for uid, taken in splits[split_id]["members"].items():
                member = guild.get_member(int(uid))
                name = member.display_name if member else f"User {uid}"
                label = f"{name} {'✅' if taken else '❌'}"
                member_options.append(discord.SelectOption(label=label, value=uid))

            select = Select(
                placeholder="Select a player...",
                options=member_options,
                custom_id=f"select_{split_id}"
            )
            select.callback = self.select_callback
            self.add_item(select)

            check_button = Button(
                label="Check",
                style=discord.ButtonStyle.success,
                custom_id=f"check_{split_id}"
            )
            check_button.callback = self.check_callback
            self.add_item(check_button)

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.starter_id:
            await interaction.response.send_message(
                "❌ Only the split creator can select players!",
                ephemeral=True
            )
            return

        selected_uid = interaction.data["values"][0]
        splits[self.split_id]["selected"] = selected_uid
        await interaction.response.send_message(
            f"✅ Selected <@{selected_uid}>. Now press **Check**.",
            ephemeral=True
        )

    async def check_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.starter_id:
            await interaction.response.send_message(
                "❌ Only the split creator can use this!",
                ephemeral=True
            )
            return

        split = splits.get(self.split_id)
        if not split or "selected" not in split:
            await interaction.response.send_message(
                "⚠️ No player selected!",
                ephemeral=True
            )
            return

        uid = split["selected"]
        split["members"][uid] = True
        del split["selected"]

        channel = bot.get_channel(split["channel_id"])
        msg = await channel.fetch_message(split["message_id"])
        embed = msg.embeds[0]

        # Rebuild players list
        new_value = ""
        for member_id, taken in split["members"].items():
            member = channel.guild.get_member(int(member_id))
            status = "✅" if taken else "❌"
            new_value += f"**{member.display_name if member else member_id}**\nShare: {split['each']}M | Status: {status}\n"

        embed.set_field_at(index=5, name="Players", value=new_value, inline=False)
        await msg.edit(embed=embed, view=SplitView(self.split_id, self.starter_id, channel.guild))

        if all(split["members"].values()):
            await channel.send("✅ All players confirmed! Split is now closed!")
            del splits[self.split_id]

        await interaction.response.defer()


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
    total_amount: float,
    repairs: float,
    accounting: float,
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

    if not selected_members:
        await interaction.response.send_message("No valid members specified!", ephemeral=True)
        return

    # Final amount after deductions
    final_amount = round(total_amount - repairs - accounting, 2)
    if final_amount < 0:
        await interaction.response.send_message("❌ Final amount cannot be negative!", ephemeral=True)
        return

    per_share = round(final_amount / len(selected_members), 2)

    # Build embed
    embed = discord.Embed(
        title="💰 Loot Split Breakdown 💰",
        color=discord.Color.gold()
    )
    embed.add_field(name="Total split amount", value=f"💰 {total_amount}M", inline=False)
    embed.add_field(name="Repairs", value=f"🔧 {repairs}M", inline=False)
    embed.add_field(name="Accounting fees", value=f"📘 {accounting}M", inline=False)
    embed.add_field(name="Final amount to split", value=f"💵 {final_amount}M", inline=False)
    embed.add_field(name="Each player's share", value=f"💰 {per_share}M", inline=False)
    embed.add_field(name="📣 Started by", value=interaction.user.mention, inline=False)

    # Players list
    status_text = ""
    for m in selected_members:
        status_text += f"**{m.display_name}**\nShare: {per_share}M | Status: ❌\n"

    embed.add_field(name="Players", value=status_text, inline=False)
    embed.set_footer(text="📸 Upload your screenshot to confirm!")

    # Save split data
    split_id = str(interaction.id)
    splits[split_id] = {
        "members": {str(m.id): False for m in selected_members},
        "total_amount": total_amount,
        "repairs": repairs,
        "accounting": accounting,
        "final_amount": final_amount,
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

    await interaction.response.send_message("✅ Split created!", ephemeral=True)


# =======================
# Screenshot patvirtinimas
# =======================
@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.author.bot or not message.attachments:
        return

    for split_id, data in list(splits.items()):
        if message.channel.id != data["channel_id"]:
            continue

        if str(message.author.id) in data["members"] and not data["members"][str(message.author.id)]:
            data["members"][str(message.author.id)] = True
            await message.add_reaction("✅")

            msg = await message.channel.fetch_message(data["message_id"])
            embed = msg.embeds[0]

            new_value = ""
            for uid, taken in data["members"].items():
                member = message.guild.get_member(int(uid))
                status = "✅" if taken else "❌"
                new_value += f"**{member.display_name if member else uid}**\nShare: {data['each']}M | Status: {status}\n"

            embed.set_field_at(index=5, name="Players", value=new_value, inline=False)
            await msg.edit(embed=embed, view=SplitView(split_id, data["starter"], message.guild))

            if all(data["members"].values()):
                await message.channel.send("✅ All players confirmed! Split is now closed!")
                del splits[split_id]


# =======================
# Paleidimas
# =======================
if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.environ["DISCORD_TOKEN"])
