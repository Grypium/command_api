from typing import Dict, List, Set
import yaml
import os
from pathlib import Path

class UserGroups:
    """User and group management system loaded from YAML config"""
    def __init__(self, config_path: str = None):
        self._groups: Dict[str, Set[str]] = {}  # group -> set of users
        self._user_groups: Dict[str, Set[str]] = {}  # user -> set of groups
        self._group_admins: Set[str] = set()  # users who can manage groups
        self.load_config(config_path)
    
    def load_config(self, config_path: str = None) -> None:
        """Load groups configuration from YAML file"""
        if not config_path:
            # Default to config/groups.yaml relative to the project root
            config_path = str(Path(__file__).parent.parent / "config" / "groups.yaml")
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Groups configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Clear existing data
        self._groups.clear()
        self._user_groups.clear()
        self._group_admins.clear()
        
        # Load group admins
        self._group_admins.update(config.get('group_admins', []))
        
        # Load groups and their members
        for group_name, members in config.get('groups', {}).items():
            self._groups[group_name] = set(members)
            for username in members:
                if username not in self._user_groups:
                    self._user_groups[username] = set()
                self._user_groups[username].add(group_name)
    
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
    
    def is_group_admin(self, username: str) -> bool:
        """Check if a user is authorized to manage groups"""
        return username in self._group_admins

# Global instance for user/group management
user_groups = UserGroups()

def is_group_admin(username: str) -> bool:
    """Check if a user is authorized to manage groups"""
    return user_groups.is_group_admin(username)

def is_user_authorized(username: str, allowed_users: List[str] = None, allowed_groups: List[str] = None) -> bool:
    """Check if a user is authorized based on username or group membership"""
    if not allowed_users and not allowed_groups:
        return True  # No restrictions
    
    if allowed_users and username in allowed_users:
        return True
    
    if allowed_groups and user_groups.is_user_in_any_group(username, allowed_groups):
        return True
    
    return False 