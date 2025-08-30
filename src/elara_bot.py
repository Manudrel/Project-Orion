import os

import discord
from dotenv import load_dotenv
from discord.ext import commands

from services.logger import logger, discord_logger
from groq_client import get_response, process_message
from services.user_manager import *
from services.context_manager import ContextManager

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
if token is None:
    raise ValueError("DISCORD_TOKEN environment variable not set.")


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

commands_list = ["!help"]

elara = commands.Bot(command_prefix = '!', intents=intents, help_command=None)

ctx_manager = ContextManager()

@elara.event
async def on_ready():
    if elara.user is not None:
        logger.info(f"- Bot started and ready.")
        print(f"[{elara.user.name}] - Okay master, lets kill da ho... beeetch!")
    else:
        logger.error("Bot user returned None.")
        
@elara.event
async def on_message(message: discord.Message) -> None:
    
    '''Handle incoming messages and respond using Groq API.'''
    if message.author == elara.user:
        return
     
    if not is_trustable(message.author.id):
        logger.warning(f"UNAUTHORIZED ACCESS ATTEMPT BY: [{message.author.name.upper()}] - ID: {message.author.id}")
        return
    
    if message.content.startswith('!') and message.content.split(' ')[0] in commands_list:
        await elara.process_commands(message)
        return
    
    # Log the incoming message
    discord_logger.info(f"[{message.author.name.upper()}]: {message.content}")
    
    # Update context with the incoming message
    ctx_window = ctx_manager.update_context(
        user_id=message.author.id,
        message=message.content,
        username=message.author.name,
        chat_id=message.channel.id  
    )
    
    try:
        response = await process_message(
            prompt=message.content, 
            user_id=message.author.id, 
            context_window=ctx_window
        )
        response = response.replace("$Elara says: $", "").strip()
    
    except Exception as e:
        logger.error(f"Error getting response: {e}")
        await message.channel.send("Ocurred an Error!.")
        return
    
    # Update context with the response
    ctx_manager.update_context(
            user_id=message.author.id,
            message=response,
            username="Elara",
            chat_id=message.channel.id
        )
    
    
    # Log the response
    discord_logger.info(f"[ELARA] send to [{message.author}]: {response[:80]}...")
    
    
    await message.channel.send(response)

@elara.command(name="help")
async def help_command(ctx: commands.Context) -> None:
    embed = discord.Embed(
        title="💜 Elara Help",
        description=(
            f"Olá {ctx.author.mention}, meu nome é Elara e eu sou sua assistente pessoal do Discord!\n\n"
            "Com **muito carinho e fofura** para alegrar seu servidor, **sistemas inteligentes** que entendem suas intenções "
            "e uma **personalidade adaptável** que se molda ao seu humor...\n\n"
            "Tudo feito pelo meu criador **Emanuel**, com amor, para espalhar felicidade digital! ✨💜"
        ),
        color=discord.Color.purple() 
    )
    
    embed.add_field(
        name="!help",
        value="Mostra esta mensagem de ajuda.",
        inline=False
    )

    embed.add_field(
        name="setrole <@usuário> <cargo>",
        value=(
            "Altera o cargo do usuário mencionado (ou o seu próprio).\n"
            "_Funciona com **intents**: basta dar a intenção de trocar de cargo e o cargo requirido._"
        ),
        inline=False
    )

    embed.add_field(
        name="setmood <@usuário> <humor>",
        value=(
            "Altera o humor do usuário mencionado (`good`, `bad`, `neutral`).\n"
            "_Funciona apenas com **intents**, por exemplo: `Estou feliz`, `Estou triste`, `Estou neutro`._"
        ),
        inline=False
    )

    embed.set_footer(text=f"Comando solicitado por {ctx.author.display_name}")

    await ctx.send(embed=embed)
    
elara.run(token)
    