import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DATA_FILE = os.path.join(BASE_DIR, "..", "..", "data", "users.json")
USER_DATA_FILE = os.path.abspath(USER_DATA_FILE)

with open(USER_DATA_FILE, "r") as f:
    users = json.load(f)

def find_user_by_name(username: str) -> dict | None:
    """Find a user by their name."""
    global users
    for user in users["users"]:
        if user["name"].lower() == username.lower():
            return user
    return None
    


def update_role(user_id: int, new_role: str) -> bool:
    """Update a user's role and save to file."""
    global users
    
    allowed_roles = {"Developer", "Tester", "User"}
    new_role = new_role.capitalize()
    
    if new_role not in allowed_roles:
        return False  # Invalid role
    
    return update_user(user_id= user_id, role= new_role)

def change_role(requester_id: int, new_role: str, target_id: int | None = None, target_name: str | None = None) -> bool:
    """
    Check if requester has permission to change target's role.
    Returns True if allowed, False otherwise.
    """
    # Primeiro, encontra o usuário alvo
    if target_id is not None:
        target_user = get_user(target_id)
    elif target_name is not None:
        target_user = find_user_by_name(target_name)
    else:
        print("Please give either target_id or target_name.")
        return False
    
    # Encontra o usuário requisitante
    requester = get_user(requester_id)
    
    # Verifica se os usuários existem
    if not requester:
        print(f"Requester ID {requester_id} not found")
        return False
    
    if not target_user:
        target_identifier = target_name if target_name else target_id
        print(f"Target '{target_identifier}' not found")
        return False
    
    # Define the role hierarchy
    role_hierarchy = {
        "Developer": 3,
        "Tester": 2,
        "User": 1
    }
    
    # Verify if new_role is valid
    if new_role not in role_hierarchy:
        print(f"Role '{new_role}' não é válida")
        return False
    
    if requester["role"] not in role_hierarchy:
        print(f"Role do requester '{requester['role']}' não é reconhecida")
        return False
    
    if target_user["role"] not in role_hierarchy:
        print(f"Role do target '{target_user['role']}' não é reconhecida")
        return False
    
    # Get role levels
    requester_level = role_hierarchy[requester["role"]]
    target_level = role_hierarchy[target_user["role"]]
    new_role_level = role_hierarchy[new_role]
    
    # Rules:
    # 1. Dev can change anyone's role
    # 2. Requester must have higher role than target
    # 3. Requester can only assign roles equal to or lower than their own
    
    if requester["role"] == "developer".capitalize():
        # Dev have all permissions
        return update_role(target_user["id"], new_role)
    
    elif (requester_level > target_level and 
          new_role_level <= requester_level):
        # Requester has higher role than target and can assign the new role
        return update_role(target_user["id"], new_role)
    
    else:
        print(f"Permissão negada: {requester['role']} → {new_role}")
        return False
    
 
def update_user_mood(user_id: int, new_mood: str) -> bool:
    """
    Update a user's mood and save to file.
    """
    global users
    
    allowed_moods = {"good", "bad", "neutral"}
    new_mood = new_mood.lower()
    
    if new_mood not in allowed_moods:
        return False  # Invalid mood
    
    return update_user(user_id=user_id, mood=new_mood)
    
def is_trustable(user_id: int) -> bool:
    """Check if a user is trusted."""
    return user_id in [user["id"] for user in users["users"] if user["trustable"] == True]

def get_role(user_id: int) -> str:
    """Get the role of a user."""
    for user in users["users"]:
        if user["id"] == user_id:
            return user["role"]
    return "user"  # Default role if user not found

def get_mood(user_id: int) -> str:
    """Get the mood of a user."""
    for user in users["users"]:
        if user["id"] == user_id:
            return user["mood"]
    return "neutral"  # Default mood if user not found

def create_user(name: str, user_id: int, role: str = "user", mood: str = "neutral", permissions: list[str] = None, trustable: bool = False) -> None: # type: ignore
    """Create a new user."""
    
    global users
    if permissions is None:
        permissions = []
    
    new_user = {
        "name": name,
        "id": user_id,
        "role": role,
        "mood": mood,
        "permissions": permissions,
        "trustable": trustable
    }
    
    users["users"].append(new_user)
    
    with open(USER_DATA_FILE, "w") as f:
        json.dump(users, f, indent=4)

def get_user(user_id: int) -> dict | None:
    
    global users
    """Retrieve a user by ID."""
    if user_id not in [user["id"] for user in users["users"]]:
        return None
    else:
        # Return the user if found
        for user in users["users"]:
            if user["id"] == user_id:
                return user
            
    # Return None if user not found   
    return None

def update_user(user_id: int, name: str = None, role: str = None, mood: str = None, permissions: list[str] = None, trustable: bool = None) -> bool: # type: ignore
    """Update an existing user. Only provided fields will be updated."""
    
    global users
    user_found = False
    
    for user in users["users"]:
        if user["id"] == user_id:
            if name is not None:
                user["name"] = name
            if role is not None:
                user["role"] = role
            if mood is not None:
                user["mood"] = mood
            if permissions is not None:
                user["permissions"] = permissions
            if trustable is not None:
                user["trustable"] = trustable
            
            user_found = True
            break
    
    if user_found:
        try:
            with open(USER_DATA_FILE, "w") as f:
                json.dump(users, f, indent=4)
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    return False  # User not found
        
def delete_user(user_id: int)-> None:
    """Delete a user by ID."""
    global users
    users["users"] = [user for user in users["users"] if user["id"] != user_id]
    
    with open(USER_DATA_FILE, "w") as f:
        json.dump(users, f, indent=4)
        
def list_users() -> None:
    """List all users."""
    global users
    print("=== TODOS OS USUÁRIOS ===")
    for usuario in users["users"]:
        print(f"\nNome: {usuario['name']}\n")
        print(f"ID: {usuario['id']}\n")
        print(f"Cargo: {usuario['role']}\n")
        print(f"Mood: {usuario['mood']}\n")
        print(f"Permissões: {', '.join(usuario['permissions']) if usuario['permissions'] else 'Nenhuma'}")
        print(f"Confiável: {'Sim' if usuario['trustable'] else 'Não'}\n")
    


if __name__ == "__main__":
    
    update_role(679783021687078938, "user")