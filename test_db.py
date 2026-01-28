from database import Database


def assign_role(email, role):
    """Assign a role to a user email."""
    role_map = {
        "technical support": "Technical Support",
        "technical_support": "Technical Support",
        "student": "Student",
    }
    normalized_role = role_map.get(role.strip().lower(), role)
    updated = database.update_user_role(email, normalized_role)
    if updated:
        print(f"Role '{normalized_role}' assigned to {email}")
        return True
    print(f"Failed to assign role '{normalized_role}' to {email}")
    return False


database = Database()

assign_role("v@gmail.com", "Technical Support")