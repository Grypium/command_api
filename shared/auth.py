from typing import Dict, List, Set

class UserGroups:
    """User and group management system"""
    def __init__(self):
        self._groups: Dict[str, Set[str]] = {}  # group -> set of users
        self._user_groups: Dict[str, Set[str]] = {}  # user -> set of groups
    
    def add_group(self, group_name: str) -> None:
        """Add a new group"""
        if group_name not in self._groups:
            self._groups[group_name] = set()
    
    def add_user_to_group(self, username: str, group_name: str) -> None:
        """Add a user to a group"""
        if group_name not in self._groups:
            self.add_group(group_name)
        
        self._groups[group_name].add(username)
        if username not in self._user_groups:
            self._user_groups[username] = set()
        self._user_groups[username].add(group_name)
    
    def remove_user_from_group(self, username: str, group_name: str) -> None:
        """Remove a user from a group"""
        if group_name in self._groups:
            self._groups[group_name].discard(username)
        if username in self._user_groups:
            self._user_groups[username].discard(group_name)
    
    def get_user_groups(self, username: str) -> Set[str]:
        """Get all groups a user belongs to"""
        return self._user_groups.get(username, set())
    
    def is_user_in_group(self, username: str, group_name: str) -> bool:
        """Check if a user is in a specific group"""
        return group_name in self.get_user_groups(username)
    
    def is_user_in_any_group(self, username: str, groups: List[str]) -> bool:
        """Check if a user is in any of the specified groups"""
        user_groups = self.get_user_groups(username)
        return bool(user_groups.intersection(groups))

# Global instance for user/group management
user_groups = UserGroups()

# Add some default groups
user_groups.add_group("admin")
user_groups.add_group("system")
user_groups.add_group("users")

# Helper function to check user authorization
def is_user_authorized(username: str, allowed_users: List[str] = None, allowed_groups: List[str] = None) -> bool:
    """Check if a user is authorized based on username or group membership"""
    if not allowed_users and not allowed_groups:
        return True  # No restrictions
    
    if allowed_users and username in allowed_users:
        return True
    
    if allowed_groups and user_groups.is_user_in_any_group(username, allowed_groups):
        return True
    
    return False 