# bot.py - Kamui Bot (com credenciais embutidas)
# pip install discord.py aiohttp

import json
import os
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands

# ============ CREDENCIAIS ============
DISCORD_TOKEN = "MTU1MTE4MTAxMDM5NjUxMjMzNg.Ggdd_Q.wGR4Sb8-aVMChAr4GWZIOJhasUsIv6kmOcnqpA"
GROQ_KEY      = "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"
GROQ_URL      = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL    = "llama-3.3-70b-versatile"

# ============ ARQUIVOS ============
CONFIG_FILE    = "config.json"
WHITELIST_FILE = "whitelist.json"

def load_json(p, default=None):
    if not os.path.exists(p):
        return default if default is not None else {}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(p, data):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

config    = load_json(CONFIG_FILE, {"listen_channel": None, "owner_ids": []})
whitelist = load_json(WHITELIST_FILE, [])

# ============ BOT ============
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!km ", intents=intents, help_command=None)

# ============ IA (Groq) ============
async def ask_ai(prompt: str, history=None) -> str:
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    messages = [
        {"role": "system", "content":
            "Você é o Kamui Bot. Especialista em Roblox Lua, Java, Bash, Linux, Python, "
            "scripts de exploit, hubs, Discord bots e programação em geral. "
            "Responda direto, técnico, sem enrolação. Quando pedirem código, "
            "entregue o código completo em bloco ```linguagem```."}
    ]
    if history:
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": prompt})

    body = {"model": GROQ_MODEL, "messages": messages, "temperature": 0.4}

    async with aiohttp.ClientSession() as s:
        async with s.post(GROQ_URL, headers=headers, json=body) as r:
            if r.status != 200:
                return f"❌ Erro da IA ({r.status}): {await r.text()}"
            data = await r.json()
            return data["choices"][0]["message"]["content"]

def is_whitelisted(uid: int) -> bool:
    return str(uid) in [str(x) for x in whitelist]

# ============ EVENTOS ============
@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user} ({bot.user.id})")
    await bot.change_presence(activity=discord.Game(name="Kamui x Hub | /ajuda"))
    try:
        synced = await bot.tree.sync()
        print(f"🔁 {len(synced)} slash commands sincronizados.")
    except Exception as e:
        print("Erro sync:", e)

# ============ SLASH /ajuda ============
@bot.tree.command(name="ajuda", description="Mostra os comandos disponíveis")
async def ajuda(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎮 Kamui Bot",
        description="Responda no canal dedicado, sem prefixo, com IA + comandos.",
        color=0x8b5cf6
    )
    embed.add_field(name="/setchannel #canal", value="Define o canal de escuta da IA", inline=False)
    embed.add_field(name="/addwhite @user", value="Adiciona à whitelist", inline=False)
    embed.add_field(name="/delwhite @user", value="Remove da whitelist", inline=False)
    embed.add_field(name="/listwhite", value="Lista a whitelist", inline=False)
    embed.add_field(name="/java", value="Ajuda com Java", inline=False)
    embed.add_field(name="/bash", value="Ajuda com Bash/Linux", inline=False)
    embed.add_field(name="/lua", value="Ajuda com Lua/Roblox", inline=False)
    embed.add_field(name="/clear <n>", value="Apaga mensagens", inline=False)
    embed.set_footer(text="Kamui x Hub — por testeeeeeeeepouraa_99391")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ============ ADMIN ============
@bot.tree.command(name="setchannel", description="Define o canal onde a IA responde")
async def setchannel(interaction: discord.Interaction, canal: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
    config["listen_channel"] = canal.id
    save_json(CONFIG_FILE, config)
    await interaction.response.send_message(f"✅ Canal de escuta: {canal.mention}")

@bot.tree.command(name="addwhite", description="Adiciona à whitelist")
async def addwhite(interaction: discord.Interaction, usuario: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
    if str(usuario.id) in [str(x) for x in whitelist]:
        return await interaction.response.send_message(f"⚠️ Já está na whitelist.", ephemeral=True)
    whitelist.append(str(usuario.id))
    save_json(WHITELIST_FILE, whitelist)
    await interaction.response.send_message(f"✅ {usuario.mention} adicionado.")

@bot.tree.command(name="delwhite", description="Remove da whitelist")
async def delwhite(interaction: discord.Interaction, usuario: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
    if str(usuario.id) not in [str(x) for x in whitelist]:
        return await interaction.response.send_message(f"⚠️ Não está na whitelist.", ephemeral=True)
    whitelist[:] = [x for x in whitelist if str(x) != str(usuario.id)]
    save_json(WHITELIST_FILE, whitelist)
    await interaction.response.send_message(f"🗑️ {usuario.mention} removido.")

@bot.tree.command(name="listwhite", description="Lista a whitelist")
async def listwhite(interaction: discord.Interaction):
    if not whitelist:
        return await interaction.response.send_message("📭 Whitelist vazia.", ephemeral=True)
    linhas = []
    for uid in whitelist:
        m = interaction.guild.get_member(int(uid))
        linhas.append(f"• {m.mention if m else f'`{uid}`'}")
    await interaction.response.send_message(
        embed=discord.Embed(title="📋 Whitelist", description="\n".join(linhas), color=0x22c55e),
        ephemeral=True
    )

@bot.tree.command(name="clear", description="Apaga N mensagens")
async def clear(interaction: discord.Interaction, quantidade: int = 10):
    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
    await interaction.channel.purge(limit=quantidade)
    await interaction.response.send_message(f"🧹 {quantidade} mensagens apagadas.", ephemeral=True)

# ============ IA - Atalhos ============
@bot.tree.command(name="java", description="Ajuda com Java")
async def java_cmd(interaction: discord.Interaction, duvida: str):
    await interaction.response.defer()
    await interaction.followup.send((await ask_ai(f"Em Java: {duvida}"))[:1900])

@bot.tree.command(name="bash", description="Ajuda com Bash/Linux")
async def bash_cmd(interaction: discord.Interaction, duvida: str):
    await interaction.response.defer()
    await interaction.followup.send((await ask_ai(f"Em Bash/Linux: {duvida}"))[:1900])

@bot.tree.command(name="lua", description="Ajuda com Lua/Roblox")
async def lua_cmd(interaction: discord.Interaction, duvida: str):
    await interaction.response.defer()
    await interaction.followup.send((await ask_ai(f"Em Lua/Roblox: {duvida}"))[:1900])

@bot.tree.command(name="hub", description="Ajuda com hub Roblox")
async def hub_cmd(interaction: discord.Interaction, pedido: str):
    await interaction.response.defer()
    await interaction.followup.send((await ask_ai(f"Crie ou ajude com um hub Roblox: {pedido}"))[:1900])

# ============ ESCUTA SEM PREFIXO ============
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if config.get("listen_channel") and message.channel.id == config["listen_channel"]:
        is_admin = message.author.guild_permissions.administrator
        if is_whitelisted(message.author.id) or is_admin:
            async with message.channel.typing():
                resp = await ask_ai(message.content)
                for i in range(0, len(resp), 1900):
                    await message.channel.send(resp[i:i+1900])
        else:
            await message.reply("🚫 Você não está na whitelist.")
    await bot.process_commands(message)

# ============ START ============
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
