# bot.py - Kamui Bot v2 (sem whitelist, responde direto)
# pip install discord.py aiohttp flask

import json
import os
import threading
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask

# ============ VARIÁVEIS DE AMBIENTE ============
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_KEY      = os.getenv("GROQ_KEY")
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

config    = load_json(CONFIG_FILE, {"listen_channel": None})
whitelist = load_json(WHITELIST_FILE, [])

# ============ SERVIDOR WEB (health check) ============
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Kamui Bot online!", 200

def run_server():
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ============ BOT DISCORD ============
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

# ============ /ajuda ============
@bot.tree.command(name="ajuda", description="Mostra os comandos disponíveis")
async def ajuda(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎮 Kamui Bot",
        description="Fale direto no canal configurado — a IA responde sem precisar de comando.",
        color=0x8b5cf6
    )
    embed.add_field(name="/setchannel #canal", value="Define o canal de escuta da IA", inline=False)
    embed.add_field(name="/java <dúvida>", value="Ajuda com Java", inline=False)
    embed.add_field(name="/bash <dúvida>", value="Ajuda com Bash/Linux", inline=False)
    embed.add_field(name="/lua <dúvida>", value="Ajuda com Lua/Roblox", inline=False)
    embed.add_field(name="/hub <pedido>", value="Ajuda com hub Roblox", inline=False)
    embed.add_field(name="/clear <n>", value="Apaga mensagens", inline=False)
    embed.set_footer(text="Kamui x Hub — por testeeeeeeeepouraa_99391")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ============ /setchannel (RESPOSTA RÁPIDA - evita timeout) ============
@bot.tree.command(name="setchannel", description="Define o canal onde a IA responde")
async def setchannel(interaction: discord.Interaction, canal: discord.TextChannel):
    # Responder IMEDIATAMENTE para não dar timeout
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
    
    config["listen_channel"] = canal.id
    save_json(CONFIG_FILE, config)
    await interaction.response.send_message(f"✅ Canal de escuta definido: {canal.mention}")

# ============ /clear ============
@bot.tree.command(name="clear", description="Apaga N mensagens")
async def clear(interaction: discord.Interaction, quantidade: int = 10):
    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=quantidade)
    await interaction.followup.send(f"🧹 {quantidade} mensagens apagadas.", ephemeral=True)

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

# ============ ESCUTA SEM PREFIXO (sem whitelist) ============
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    
    # Só responde no canal configurado
    if config.get("listen_channel") and message.channel.id == config["listen_channel"]:
        # Ignora se for comando (começar com / ou !)
        if not message.content.startswith("/") and not message.content.startswith("!"):
            async with message.channel.typing():
                resp = await ask_ai(message.content)
                for i in range(0, len(resp), 1900):
                    await message.channel.send(resp[i:i+1900])
    
    await bot.process_commands(message)

# ============ START ============
if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    if not DISCORD_TOKEN:
        print("❌ ERRO: variável DISCORD_TOKEN não definida.")
    else:
        bot.run(DISCORD_TOKEN)
