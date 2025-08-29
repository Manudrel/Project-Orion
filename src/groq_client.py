from services.logger import parser_logger, logger
from services.user_manager import *
from agents.command_parser import classify_and_extract, handle_role_change, handle_mood_change
from groq import Groq, APIConnectionError, APIStatusError
from dotenv import load_dotenv
import os

load_dotenv()
# Get Groq API key from environment variable
api_key = os.getenv('GROQ_API_KEY')

if not api_key:
    raise ValueError("GROQ_API_KEY environment variable not set.")

# Initialize Groq client
client = Groq(api_key=api_key)

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")


def role_catcher(user_id: int) -> str:
    
    """Load role-specific prompt based on user's role."""
    role = get_role(user_id).lower()

    match role:
        case "developer":
            with open(os.path.join(PROMPTS_DIR, "roles", "developer_elara.txt"), "r", encoding="utf-8") as file:
                return file.read()
        case "tester":
            with open(os.path.join(PROMPTS_DIR, "roles", "tester_elara.txt"), "r", encoding="utf-8") as file:
                return file.read()
        case "user":
            with open(os.path.join(PROMPTS_DIR, "roles", "user_elara.txt"), "r", encoding="utf-8") as file:
                return file.read()
        case _:
            with open(os.path.join(PROMPTS_DIR, "roles", "user_elara.txt"), "r", encoding="utf-8") as file:
                return file.read()
        

def load_system_prompt(user_id: int) -> str:
    
    """Load and customize the system prompt based on user's mood and role."""
    
    try:
        if get_mood(user_id) == "good":
            with open(os.path.join(PROMPTS_DIR, "good_elara.txt"), "r", encoding="utf-8") as file:
                base_personality = file.read()
            
        elif get_mood(user_id) == "bad":
            with open(os.path.join(PROMPTS_DIR, "bad_elara.txt"), "r", encoding="utf-8") as file:
                base_personality = file.read()
        else:
            with open(os.path.join(PROMPTS_DIR, "neutral_elara.txt"), "r", encoding="utf-8") as file:
                base_personality = file.read()
            
        role_prompt = role_catcher(user_id)
        
        full_prompt = f"""{base_personality}

        # CONFIGURAÇÃO DE ACESSO (sobrescreve apenas aspectos técnicos):
        {role_prompt}

        # REGRA FINAL: Mantenha sempre sua personalidade base de Elara, independentemente das configurações técnicas acima."""
        
        return full_prompt
            
    except FileNotFoundError:
        return "Você é um assistente útil chamado Elara. Responda de forma clara e concisa."



async def get_response(prompt: str, user_id: int, context_window: list) -> str:
    
    """Get response from Groq API based on the prompt and user context."""
    try:
        
        system_prompt = load_system_prompt(user_id)
        
        # Prepare the messages for the chat completion
        messages: list= [
            {
                "role": "system", 
                "content": f"{system_prompt}"
            }
        ]
        
        # Add context window messages
        messages.extend(context_window)
        
        # Adds the actual user prompt at the end
        messages.append({"role": "user", "content": prompt})
        
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages= messages, 
            temperature=0.5,
            max_completion_tokens = 1000,
            top_p=0.5,
        )
        return completion.choices[0].message.content or ""
    
    
    except APIConnectionError as e:
        return f"Connection Error: {e}"
    except APIStatusError as e:
        return f"API Error: {e.status_code}"
    except Exception as e:
        return f"Unexpected Error: {e}"


async def process_message(prompt: str, user_id: int, context_window: list) -> str:
    try:
        parser_logger.debug(f"Received message: '{prompt}' from user: {user_id}")
    
        parsed = classify_and_extract(prompt)
        parser_logger.debug(f"Parsed result: {parsed}")
        
        intent = parsed.get("intent", "chat")
        data = parsed.get("extracted_data", {})
        parser_logger.debug(f"Intent: {intent}, Data: {data}")

        parser_logger.debug(f"Processing intent: {intent} with data: {data}")

        if intent == "role_change":
            target_name = data.get("target_name", "")
            new_role = data.get("new_role", "")
            
            if not target_name or not new_role:
                return "Dados insuficientes para mudança de cargo."
            
            return handle_role_change(
                new_role=new_role,
                requester_id=user_id,
                target_name=target_name
            )


        elif intent == "mood_change":
            target_name = data.get("target_name", "")
            new_mood = data.get("new_mood", "neutral")
            
            # Execute mood change
            mood_result = handle_mood_change(user_id, target_name, new_mood)
            
            # If error, return directly
            if any(phrase in mood_result.lower() for phrase in ["não tem permissão", "não encontrado", "erro"]):
                chat_response = await get_response(f"[{mood_result}] {prompt}", user_id, context_window)
                return chat_response
            
            # If successful, proceed to chat response with mood context
            chat_response = await get_response(f"[{mood_result}] {prompt}", user_id, context_window)
            return chat_response

        else:
            # Fallback to the chat model for general conversation
            try:
                response = await get_response(prompt, user_id, context_window)
                return response
            except Exception as e:
                logger.error(f"Error in get_response: {e}")
                return "Desculpe, estou com problemas para responder agora."

    except Exception as e:
        logger.error(f"Error in process_message: {e}")
        return "Ocorreu um erro ao processar sua mensagem."


