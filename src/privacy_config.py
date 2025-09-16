import streamlit as st
from typing import Dict, List
import json
from pathlib import Path

class PrivacyConfig:
    """Advanced privacy configuration management"""
    
    def __init__(self):
        self.config_file = Path.home() / ".document_analyzer" / "privacy_config.json"
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.load_config()
    
    def load_config(self):
        """Load privacy configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = self.get_default_config()
        except Exception as e:
            st.warning(f"Could not load privacy config: {e}")
            self.config = self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Get default privacy configuration"""
        return {
            "sanitization": {
                "default_level": "medium",
                "custom_patterns": [],
                "whitelist_domains": [],
                "preserve_formatting": True
            },
            "storage": {
                "auto_save": True,
                "max_stored_analyses": 100,
                "compress_storage": False,
                "encryption_enabled": False
            },
            "processing": {
                "clear_memory_after": True,
                "delete_temp_files": True,
                "log_processing_time": False
            },
            "alerts": {
                "warn_sensitive_data": True,
                "confirm_cloud_processing": True,
                "show_privacy_reminders": True
            }
        }
    
    def save_config(self):
        """Save current configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            st.error(f"Could not save privacy config: {e}")
    
    def render_privacy_settings(self):
        """Render advanced privacy settings in Streamlit"""
        with st.expander("⚙️ Advanced Privacy Settings", expanded=False):
            
            # Sanitization Settings
            st.subheader("🛡️ Document Sanitization")
            
            self.config["sanitization"]["default_level"] = st.selectbox(
                "Default Sanitization Level",
                ["none", "low", "medium", "high"],
                index=["none", "low", "medium", "high"].index(
                    self.config["sanitization"]["default_level"]
                )
            )
            
            self.config["sanitization"]["preserve_formatting"] = st.checkbox(
                "Preserve document formatting",
                value=self.config["sanitization"]["preserve_formatting"]
            )
            
            # Custom patterns
            st.write("**Custom Sensitive Patterns:**")
            custom_pattern = st.text_input(
                "Add custom regex pattern",
                placeholder="e.g., EMPLOYEE-\\d{4} for employee IDs"
            )
            
            if st.button("Add Pattern") and custom_pattern:
                if custom_pattern not in self.config["sanitization"]["custom_patterns"]:
                    self.config["sanitization"]["custom_patterns"].append(custom_pattern)
                    st.success("Pattern added!")
            
            # Show existing patterns
            if self.config["sanitization"]["custom_patterns"]:
                for i, pattern in enumerate(self.config["sanitization"]["custom_patterns"]):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.code(pattern)
                    with col2:
                        if st.button("Remove", key=f"remove_{i}"):
                            self.config["sanitization"]["custom_patterns"].pop(i)
                            st.rerun()
            
            st.divider()
            
            # Storage Settings
            st.subheader("💾 Storage Settings")
            
            self.config["storage"]["auto_save"] = st.checkbox(
                "Automatically save analyses",
                value=self.config["storage"]["auto_save"]
            )
            
            self.config["storage"]["max_stored_analyses"] = st.number_input(
                "Maximum stored analyses",
                min_value=10,
                max_value=1000,
                value=self.config["storage"]["max_stored_analyses"]
            )
            
            self.config["storage"]["compress_storage"] = st.checkbox(
                "Compress stored files",
                value=self.config["storage"]["compress_storage"],
                help="Reduces storage space but may slow access"
            )
            
            st.divider()
            
            # Processing Settings  
            st.subheader("⚡ Processing Settings")
            
            self.config["processing"]["clear_memory_after"] = st.checkbox(
                "Clear memory after processing",
                value=self.config["processing"]["clear_memory_after"]
            )
            
            self.config["processing"]["delete_temp_files"] = st.checkbox(
                "Delete temporary files immediately",
                value=self.config["processing"]["delete_temp_files"]
            )
            
            # Save configuration
            if st.button("💾 Save Privacy Settings"):
                self.save_config()
                st.success("Privacy settings saved!")
