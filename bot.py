import json
import os
import threading
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_KEY      = os.getenv("GROQ_KEY")
GROQ_URL      = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL    = "llama3-70b-8192"

CONFIG_FILE    = "config.json"

def load_json(p, default=None):
    if not os.path.exists(p):
        return default if default is not None else {}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(p, data):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

config = load_json(CONFIG_FILE, {"listen_channel": None})

app = Flask(__name__)

@app.route('/')
def health_check():
    return "Kamui Bot online!", 200

def run_server():
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!km ", intents=intents, help_command=None)

async def ask_ai(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    messages = [
        {"role": "system", "content": "Você é o Kamui Bot. Especialista em programação, Roblox Lua, Java, Bash, Python, Discord bots e exploits. Responda direto, técnico, sem enrolação. Quando pedirem código, entregue o código completo em bloco ```linguagem```."},
        {"role": "user", "content": prompt}
    ]
    body = {"model": GROQ_MODEL, "messages": messages, "temperature": 0.4}

    async with aiohttp.ClientSession() as s:
        async with s.post(GROQ_URL, headers=headers, json=body) as r:
            if r.status != 200:
                return f"❌ Erro da IA ({r.status}): {await r.text()}"
            data = await r.json()
            return data["choices"][0]["message"]["content"]

@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user}")
    await bot.change_presence(activity=discord.Game(name="Kamui x Hub"))
    try:
        await bot.tree.sync()
        print("🔁 Slash commands sincronizados.")
    except Exception as e:
        print("Erro sync:", e)

@bot.tree.command(name="setchannel", description="Define o canal onde a IA responde")
async def setchannel(interaction: discord.Interaction, canal: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
    config["listen_channel"] = canal.id
    save_json(CONFIG_FILE, config)
    await interaction.response.send_message(f"✅ Canal definido: {canal.mention}")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    
    if config.get("listen_channel") and message.channel.id == config["listen_channel"]:
        if not message.content.startswith("/") and not message.content.startswith("!"):
            async with message.channel.typing():
                resp = await ask_ai(message.content)
                for i in range(0, len(resp), 1900):
                    await message.channel.send(resp[i:i+1900])
    
    await bot.process_commands(message)

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    if not DISCORD_TOKEN:
        print("❌ ERRO: variável DISCORD_TOKEN não definida.")
    else:
        bot.run(DISCORD_TOKEN)
