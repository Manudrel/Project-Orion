from groq import Groq
from dotenv import load_dotenv
from services import user_manager
import os
import json
import re


load_dotenv()
api_key = os.getenv("GROQ_API_KEY_PARSER")
if not api_key:
    raise ValueError("GROQ_API_KEY_PARSER environment variable not set.")

client = Groq(api_key=api_key)


def classify_and_extract(message: str) -> dict:
    """ Uses a mini LLM to classify intent and extract relevant info.
        Always returns a dict with {intent, extracted_data}."""
    
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant", 
        messages=[
            {
                "role": "system",
                "content": """Você é um classificador de intenções. 
            
                Comandos válidos APENAS se começarem com palavras-chave específicas (apenas se for explícito):
                - "mude cargo", "altere cargo", "modifique cargo" → role_change
                - "mude humor", "altere humor", "estou (HUMOR AQUI)" → mood_change
            
                Responda estritamente em JSON no formato:
                {
                "intent": "chat" | "role_change" | "mood_change" | "other_command",
                "extracted_data": { ... }
                }

                - Para SAUDAÇÕES e CONVERSA normal → "chat"
                - Para role_change: extraia {"target_name": "...", "new_role": "..."}
                - Para mood_change: extraia {"target_name": "...", "new_mood": "good"|"bad"|"neutral"}
                - Para outras: {"raw": "mensagem original"}"""
            },
            {"role": "user", "content": message}
        ],
        temperature=0,
        max_completion_tokens=150,
        response_format={"type": "json_object"}
    )

    try:
        response = completion.choices[0].message.content
        return json.loads(response) if response else {"intent": "chat"}
    except Exception:
        return {"intent": "chat"}

def extract_user_id_from_mention(mention: str) -> int | None:
    """Extract numeric user ID from a Discord mention string."""
    # Remove characters extras
    mention = mention.strip().replace('!', '').replace('<', '').replace('>', '').replace('@', '')
    
    # Verify if it's all digits
    if mention.isdigit():
        return int(mention)
    
    return None

def handle_role_change(new_role: str, requester_id: int, target_name: str | None = None, target_id: int | None = None) -> str:
    """ 
    Handle role change requests. Either target_name or target_id must be provided.
    """
    
    # First, if target_name looks like a mention, extract the ID
    if target_name:
        user_id_from_mention = extract_user_id_from_mention(target_name)
        if user_id_from_mention:
            # If it's a mention, use the ID instead
            target_id = user_id_from_mention
            target_name = None  # Clear name to avoid confusion
    
    # Now proceed with either name or ID
    if target_name:
        target_user = user_manager.find_user_by_name(target_name)
        if not target_user:
            return f"Não encontrei nenhum usuário chamado {target_name}."
        
        success = user_manager.change_role(
            requester_id=requester_id,
            new_role=new_role.capitalize(),
            target_id=target_user["id"]
        )
        
        if success:
            return f"O cargo de **{target_user['name']}** foi alterado para **{new_role.capitalize()}**."
        else:
            return f"Você não tem permissão para alterar o cargo de {target_user['name']}."
    
    elif target_id:
        # Find the user by ID
        target_user = user_manager.get_user(target_id)
        if not target_user:
            return f"Não encontrei nenhum usuário com ID {target_id}."
        
        success = user_manager.change_role(
            requester_id=requester_id,
            new_role=new_role.capitalize(),
            target_id=target_id
        )
        
        if success:
            return f"O cargo de **{target_user['name']}** foi alterado para **{new_role.capitalize()}**."
        else:
            return f"Você não tem permissão para alterar o cargo de {target_user['name']}."
    
    else:
        return "Erro: Nenhum usuário fornecido."
    
def handle_mood_change(requester_id: int, target_name: str, new_mood: str) -> str:
    """
    Handle mood change requests with permission check.
    Returns success message or error.
    """
    # Verify the requester has permission
    requester = user_manager.get_user(requester_id)
    if not requester:
        return "Erro: usuário requisitante não encontrado."
    
    if requester.get("role") not in ["Developer", "Tester"]:
        return "Você não tem permissão para alterar humores."
    
    # If target_name is a self-reference, clear it
    if target_name.lower() in ["eu", "me", "mim", "você", "vc", "voce"]:
        target_name = ""

    # If no target, change requester's mood
    if not target_name:
        user_manager.update_user_mood(requester_id, new_mood)
        return f"Seu humor foi atualizado para {new_mood}."
    
    # Extract ID if it's a mention
    user_id_from_mention = extract_user_id_from_mention(target_name)
    
    if user_id_from_mention:
        # Search by ID
        target_user = user_manager.get_user(user_id_from_mention)
        if not target_user:
            return f"Usuário com ID {user_id_from_mention} não encontrado."
    else:
        # Search by name
        target_user = user_manager.find_user_by_name(target_name)
        if not target_user:
            return f"Usuário '{target_name}' não encontrado."
    
    # Upadate the target's mood
    user_manager.update_user_mood(target_user["id"], new_mood)
    return f"Humor de {target_user['name']} atualizado para {new_mood}."