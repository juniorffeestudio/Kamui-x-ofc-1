import os
import threading
import aiohttp
import discord
from discord.ext import commands
from flask import Flask

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_KEY      = os.getenv("GROQ_KEY")
GROQ_URL      = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL    = "openai/gpt-oss-120b"

UPDATE_CHANNEL_ID    = 1401891387363823706
COMMUNITY_CHANNEL_ID = 1551177524711788595
CREATOR_NAME         = "testeeeeeeeepouraa_99391"

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

async def ask_ai(prompt: str, is_update: bool = False) -> str:
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    if is_update:
        system = "Você é o Kamui Bot. Vai receber anotações do criador do hub sobre atualizações. Formate a resposta como um anúncio limpo e organizado, com título, lista de mudanças usando + para adicionado, @ para corrigido e - para removido. Seja direto e técnico."
    else:
        system = "Você é o Kamui Bot. Especialista em programação, Roblox Lua, Java, Bash, Python, Discord bots e exploits. Responda direto, técnico, sem enrolação. Quando pedirem código, entregue o código completo em bloco ```linguagem```."
    
    messages = [
        {"role": "system", "content": system},
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

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.channel.id == UPDATE_CHANNEL_ID:
        if message.author.name == CREATOR_NAME:
            async with message.channel.typing():
                resp = await ask_ai(message.content, is_update=True)
                for i in range(0, len(resp), 1900):
                    await message.channel.send(resp[i:i+1900])
        return

    if message.channel.id == COMMUNITY_CHANNEL_ID:
        if message.content.startswith("/") or message.content.startswith("!"):
            return
        async with message.channel.typing():
            resp = await ask_ai(message.content)
            for i in range(0, len(resp), 1900):
                await message.channel.send(resp[i:i+1900])
        return

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    if not DISCORD_TOKEN:
        print("❌ ERRO: variável DISCORD_TOKEN não definida.")
    else:
        bot.run(DISCORD_TOKEN)
