import threading
from typing import Dict, List, Any

class ContextManager:

    """
    Context Manager by User and Chat
    """

    def __init__(self, max_size: int = 20):
        self.max_size = max_size
        self.contexts: Dict[str, List[Dict]] = {} 
        self.lock = threading.RLock()
        
    def _get_key(self, user_id: int, chat_id: int | None = None):
        """
        Generate a unique key for each user
        """
        
        if chat_id:
            return f"user_{user_id}_chat_{chat_id}"
        return f"user_{user_id}"
    
    def update_context(self, user_id: int, message: str, username: str, chat_id: int | None = None) -> List[Dict[str, str]]:  
        """
        Updates the context for a specific user/chat
        """
        # Get and save the key of each user
        ctx_key = self._get_key(user_id, chat_id)   
        
        
        with self.lock: # Thread-safe
            # Initialize if not exists
            if ctx_key not in self.contexts:
                self.contexts[ctx_key] = []
                
            ctx_window = self.contexts[ctx_key]
        
        # Remove oldest message if it exceeds maximum size  
        if len(ctx_window) >= self.max_size:
            ctx_window.pop(0)    
        
        # Add new message
        ctx_window.append({
         'role': 'user' if username != "Elara" else 'assistant',
         'content': f'${username} says: $' + message,
        })    
        
        return ctx_window.copy()
    
    def get_context(self, user_id: int, chat_id: int | None = None) -> List[Dict[str, str]]:
        """
        Retorna o contexto atual para o usuário/chat
        """
        context_key = self._get_key(user_id, chat_id)
        with self.lock:
            return self.contexts.get(context_key, []).copy()
    
    
    def get_all_contexts(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Retorna todos os contextos (para debug)
        """
        with self.lock:
            return self.contexts.copy()
            

if __name__ == "__main__":
    ctx_manager = ContextManager()
    
    # Adiciona contextos
    ctx_manager.update_context(
        user_id=10,
        message="BlaBlaBla",
        username="Manudrel",
        chat_id=1
    )
    
    ctx_manager.update_context(
        user_id=20,
        message="BlaBlaBla22", 
        username="Manudrel15",
        chat_id=1
    )
    
    ctx_manager.update_context(
        user_id=1,
        message="BlaBlaBla33",
        username="Goat", 
        chat_id=1
    )
    
    
    all_contexts = ctx_manager.get_all_contexts()
    print("Todos os contextos:")
    print(all_contexts)
    
    
    print("\nContextos formatados:")
    for key, messages in all_contexts.items():
        print(f"\n{key}:")
        for msg in messages:
            print(f"  {msg['role']}: {msg['content']}")