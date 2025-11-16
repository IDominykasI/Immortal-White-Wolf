import discord
from discord.ext import commands

# ===== CONFIG =====
TOKEN = "MTQzOTU5NzM4NjM0NjI2Njc5Nw.GmO4tA.lLwmN_TiZcUFtwcbvxLdoGpUIoEEKttyiboKcs"
GUILD_ID = 1183116557505798324  # tavo serverio ID
APPLY_CHANNEL_ID = 1439589588623429816  # 📢│apply-here kanalas
APPLICATIONS_CHANNEL_ID = 1439593741898747915  # 🔒│applications kanalas

# ===== INTENTS =====
intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.guilds = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== BUTTON =====
class ApplyButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # view niekada nebeexpire
        self.add_item(discord.ui.Button(label="Apply", style=discord.ButtonStyle.primary, custom_id="apply_button"))

    @discord.ui.button(label="Apply", style=discord.ButtonStyle.primary, custom_id="apply_button")
    async def apply(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("Sveikas! Atsakyk į kelis klausimus DM.", ephemeral=True)
        try:
            dm = await interaction.user.create_dm()
            
            # Formos klausimai
            questions = [
                "Koks tavo vardas?",
                "Kiek tau metų?",
                "Kodėl nori prisijungti prie gildijos?",
                "Ar turi patirties su žaidimu / gildijos veikla?"
            ]
            
            answers = []
            for q in questions:
                await dm.send(q)
                
                def check(m):
                    return m.author == interaction.user and isinstance(m.channel, discord.DMChannel)
                
                msg = await bot.wait_for("message", check=check, timeout=300)  # 5 min limitas
                answers.append(msg.content)
            
            # Siunčiame atsakymus į applications kanalą
            guild = bot.get_guild(GUILD_ID)
            applications_channel = guild.get_channel(APPLICATIONS_CHANNEL_ID)
            embed = discord.Embed(title="Nauja Application forma", color=discord.Color.green())
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            for i, q in enumerate(questions):
                embed.add_field(name=q, value=answers[i], inline=False)
            
            await applications_channel.send(embed=embed)
            await dm.send("Tavo atsakymai buvo sėkmingai pateikti gildijos officeriams.")
        
        except Exception as e:
            print(e)
            await interaction.user.send("Įvyko klaida siunčiant formą. Bandyk vėliau.")

# ===== EVENTS =====
@bot.event
async def on_ready():
    print(f"Prisijungta kaip {bot.user}")
    guild = bot.get_guild(GUILD_ID)
    channel = guild.get_channel(APPLY_CHANNEL_ID)

    # Sukuriame arba atnaujiname žinutę su mygtuku
    async for message in channel.history(limit=100):
        if message.author == bot.user:
            await message.edit(content="Spauskite mygtuką norėdami pildyti application formą:", view=ApplyButton())
            break
    else:
        await channel.send("Spauskite mygtuką norėdami pildyti application formą:", view=ApplyButton())

# ===== RUN BOT =====
bot.run(TOKEN)

