"""
Secure API key storage utility using environment variables and simple encoding.
Prevents API keys from being stored in plain text files.
"""
import os
import base64
import json
from pathlib import Path


class SecureKeyManager:
    """Manages API keys securely using environment variables and encoded local storage."""
    
    def __init__(self, app_name="Searchit"):
        self.app_name = app_name
        self.secure_config_path = Path.home() / f".{app_name.lower()}" / "secure.dat"
        self.secure_config_path.parent.mkdir(exist_ok=True)
        
    def _simple_encode(self, data: str) -> str:
        """Simple encoding to obfuscate data (not cryptographically secure, but better than plain text)."""
        # Base64 encode with some simple transformations
        encoded = base64.b64encode(data.encode()).decode()
        # Add machine-specific salt
        machine_info = f"{os.environ.get('COMPUTERNAME', 'unknown')}-{os.environ.get('USERNAME', 'user')}"
        machine_hash = str(hash(machine_info) % 10000).zfill(4)
        return f"{machine_hash}:{encoded}"
    
    def _simple_decode(self, encoded_data: str) -> str:
        """Decode the simple encoded data."""
        try:
            if ':' not in encoded_data:
                return ""
            hash_part, data_part = encoded_data.split(':', 1)
            
            # Verify machine hash matches
            machine_info = f"{os.environ.get('COMPUTERNAME', 'unknown')}-{os.environ.get('USERNAME', 'user')}"
            expected_hash = str(hash(machine_info) % 10000).zfill(4)
            
            if hash_part != expected_hash:
                print("[SecureKeyManager] Warning: Data appears to be from different machine")
                # Still try to decode but warn user
            
            decoded = base64.b64decode(data_part.encode()).decode()
            return decoded
        except Exception:
            return ""
    
    def store_api_key(self, service: str, api_key: str) -> bool:
        """
        Store API key securely.
        
        Args:
            service: Service name (e.g., 'openai')
            api_key: The API key to store
            
        Returns:
            bool: True if stored successfully
        """
        try:
            print(f"[SecureKeyManager] Storing API key for {service}")
            print(f"[SecureKeyManager] Recommendation: Set environment variable {self.app_name.upper()}_{service.upper()}_API_KEY for maximum security")
            
            # Load existing config or create new
            config = {}
            if self.secure_config_path.exists():
                try:
                    with open(self.secure_config_path, 'r') as f:
                        content = f.read().strip()
                        if content:
                            # Decode each stored value
                            raw_config = json.loads(content)
                            config = {k: self._simple_decode(v) for k, v in raw_config.items()}
                except Exception:
                    config = {}  # Start fresh if decoding fails
            
            # Add/update the API key
            config[f"{service}_api_key"] = api_key
            
            # Encode values and save
            encoded_config = {k: self._simple_encode(v) for k, v in config.items()}
            
            with open(self.secure_config_path, 'w') as f:
                json.dump(encoded_config, f, indent=2)
                
            print(f"[SecureKeyManager] API key for {service} stored in encoded format")
            return True
            
        except Exception as e:
            print(f"[SecureKeyManager] Error storing API key: {e}")
            return False
    
    def get_api_key(self, service: str) -> str:
        """
        Retrieve API key securely.
        
        Priority order:
        1. Environment variable (most secure)
        2. Encoded local file
        3. Empty string (fail safely)
        
        Args:
            service: Service name (e.g., 'openai')
            
        Returns:
            str: The API key or empty string if not found
        """
        try:
            # 1. Check environment variable first (most secure)
            env_var_name = f"{self.app_name.upper()}_{service.upper()}_API_KEY"
            env_key = os.environ.get(env_var_name, "").strip()
            if env_key:
                print(f"[SecureKeyManager] Using API key from environment variable {env_var_name}")
                return env_key
            
            # 2. Check encoded file
            return self._load_encoded(service)
            
        except Exception as e:
            print(f"[SecureKeyManager] Error retrieving API key: {e}")
            return ""
    
    def _load_encoded(self, service: str) -> str:
        """Load API key from encoded local file."""
        try:
            if not self.secure_config_path.exists():
                return ""
            
            with open(self.secure_config_path, 'r') as f:
                content = f.read().strip()
                if not content:
                    return ""
            
            # Load and decode config
            raw_config = json.loads(content)
            encoded_value = raw_config.get(f"{service}_api_key", "")
            
            if not encoded_value:
                return ""
                
            api_key = self._simple_decode(encoded_value)
            if api_key:
                print(f"[SecureKeyManager] Using API key from encoded storage")
            
            return api_key
            
        except Exception as e:
            print(f"[SecureKeyManager] Error loading encoded API key: {e}")
            return ""
    
    def remove_api_key(self, service: str) -> bool:
        """Remove API key from secure storage."""
        try:
            if not self.secure_config_path.exists():
                return True
            
            # Load current config
            with open(self.secure_config_path, 'r') as f:
                content = f.read().strip()
                if not content:
                    return True
            
            raw_config = json.loads(content)
            
            # Remove the key
            raw_config.pop(f"{service}_api_key", None)
            
            # Save updated config
            with open(self.secure_config_path, 'w') as f:
                json.dump(raw_config, f, indent=2)
                
            print(f"[SecureKeyManager] API key for {service} removed")
            return True
            
        except Exception as e:
            print(f"[SecureKeyManager] Error removing API key: {e}")
            return False


# Global instance
secure_key_manager = SecureKeyManager()


def get_openai_api_key() -> str:
    """Convenience function to get OpenAI API key."""
    return secure_key_manager.get_api_key("openai")


def store_openai_api_key(api_key: str) -> bool:
    """Convenience function to store OpenAI API key."""
    return secure_key_manager.store_api_key("openai", api_key)
