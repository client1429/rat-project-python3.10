# core/plugin_manager.py
import os
import sys
import importlib
import inspect
import threading
import traceback
from typing import Dict, Any, Callable, List, Optional
from dataclasses import dataclass, field

@dataclass
class PluginInfo:
    """Metadata for a loaded plugin"""
    name: str
    version: str
    author: str
    description: str
    enabled: bool = True
    module: Any = None
    commands: Dict[str, Callable] = field(default_factory=dict)
    hooks: Dict[str, List[Callable]] = field(default_factory=dict)

class PluginManager:
    """Dynamic plugin system for the RAT"""
    
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, PluginInfo] = {}
        self.event_hooks: Dict[str, List[Callable]] = {}
        self.loaded = False
        
    def load_plugin(self, plugin_path: str) -> Optional[PluginInfo]:
        """Load a single plugin from file path"""
        try:
            # Get plugin name from filename
            plugin_name = os.path.splitext(os.path.basename(plugin_path))[0]
            if plugin_name in self.plugins:
                return self.plugins[plugin_name]
            
            # Import module dynamically
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            if spec is None:
                return None
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Check for plugin metadata
            if not hasattr(module, 'PLUGIN_INFO'):
                print(f"Plugin {plugin_name} missing PLUGIN_INFO dict")
                return None
            
            info_dict = module.PLUGIN_INFO
            plugin = PluginInfo(
                name=info_dict.get('name', plugin_name),
                version=info_dict.get('version', '1.0'),
                author=info_dict.get('author', 'Unknown'),
                description=info_dict.get('description', ''),
                module=module
            )
            
            # Register commands
            if hasattr(module, 'register_commands'):
                commands = module.register_commands()
                if isinstance(commands, dict):
                    plugin.commands = commands
                    
            # Register hooks
            if hasattr(module, 'register_hooks'):
                hooks = module.register_hooks()
                if isinstance(hooks, dict):
                    plugin.hooks = hooks
                    for event, callbacks in hooks.items():
                        if event not in self.event_hooks:
                            self.event_hooks[event] = []
                        if isinstance(callbacks, list):
                            self.event_hooks[event].extend(callbacks)
                        else:
                            self.event_hooks[event].append(callbacks)
            
            # Call plugin's on_load if exists
            if hasattr(module, 'on_load'):
                module.on_load(self)
                
            self.plugins[plugin_name] = plugin
            print(f"[+] Loaded plugin: {plugin.name} v{plugin.version}")
            return plugin
        except Exception as e:
            print(f"[-] Failed to load plugin {plugin_path}: {e}")
            traceback.print_exc()
            return None
    
    def load_all_plugins(self) -> List[str]:
        """Load all .py files from plugin directory"""
        loaded = []
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir, exist_ok=True)
            return loaded
            
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                plugin_path = os.path.join(self.plugin_dir, filename)
                plugin = self.load_plugin(plugin_path)
                if plugin:
                    loaded.append(plugin.name)
        self.loaded = True
        return loaded
    
    def get_command(self, cmd_name: str) -> Optional[Callable]:
        """Find a command handler across all plugins"""
        for plugin in self.plugins.values():
            if plugin.enabled and cmd_name in plugin.commands:
                return plugin.commands[cmd_name]
        return None
    
    def execute_command(self, cmd_name: str, args: str) -> str:
        """Execute a plugin command if available"""
        handler = self.get_command(cmd_name)
        if handler:
            try:
                result = handler(args)
                return str(result)
            except Exception as e:
                return f"Plugin error: {e}"
        return None
    
    def trigger_event(self, event_name: str, *args, **kwargs):
        """Trigger an event hook"""
        if event_name in self.event_hooks:
            for hook in self.event_hooks[event_name]:
                try:
                    hook(*args, **kwargs)
                except Exception as e:
                    print(f"Hook error for {event_name}: {e}")
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a disabled plugin"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = True
            # Re-register hooks if any
            if self.plugins[plugin_name].hooks:
                for event, callbacks in self.plugins[plugin_name].hooks.items():
                    if event not in self.event_hooks:
                        self.event_hooks[event] = []
                    if isinstance(callbacks, list):
                        self.event_hooks[event].extend(callbacks)
                    else:
                        self.event_hooks[event].append(callbacks)
            return True
        return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = False
            # Remove hooks (requires tracking, simplified)
            return True
        return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin completely"""
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            if hasattr(plugin.module, 'on_unload'):
                plugin.module.on_unload(self)
            # Remove hooks
            for event, callbacks in plugin.hooks.items():
                if event in self.event_hooks:
                    if isinstance(callbacks, list):
                        for cb in callbacks:
                            if cb in self.event_hooks[event]:
                                self.event_hooks[event].remove(cb)
                    else:
                        if callbacks in self.event_hooks[event]:
                            self.event_hooks[event].remove(callbacks)
            del self.plugins[plugin_name]
            return True
        return False
    
    def list_plugins(self) -> List[Dict]:
        """Return list of plugins with info"""
        return [
            {
                'name': p.name,
                'version': p.version,
                'author': p.author,
                'description': p.description,
                'enabled': p.enabled,
                'commands': list(p.commands.keys())
            }
            for p in self.plugins.values()
        ]

# Example plugin template
PLUGIN_TEMPLATE = '''"""
Example plugin for Stitch RAT
Place this file in the 'plugins' directory
"""

PLUGIN_INFO = {
    'name': 'ExamplePlugin',
    'version': '1.0',
    'author': 'Stitch Team',
    'description': 'An example plugin demonstrating the plugin system'
}

def register_commands():
    """Return dict of command_name -> handler_function"""
    return {
        'example': example_command,
        'example_help': example_help
    }

def register_hooks():
    """Return dict of event_name -> callback(s)"""
    return {
        'on_client_connect': on_connect,
        'on_command_received': on_command
    }

def on_load(manager):
    """Called when plugin is loaded"""
    print("[ExamplePlugin] Loaded!")

def on_unload(manager):
    """Called when plugin is unloaded"""
    print("[ExamplePlugin] Unloaded!")

def example_command(args):
    """Example command handler"""
    return f"Example plugin executed with args: {args}"

def example_help(args):
    """Command help"""
    return "example - Demonstrates plugin system"

def on_connect(client_id):
    """Hook triggered when client connects"""
    print(f"[ExamplePlugin] Client {client_id} connected")

def on_command(cmd, args):
    """Hook triggered before command execution"""
    print(f"[ExamplePlugin] Command: {cmd} {args}")
'''

# Helper to create a new plugin from template
def create_plugin_template(plugin_name: str, output_dir: str = "plugins"):
    """Create a new plugin from template"""
    os.makedirs(output_dir, exist_ok=True)
    plugin_path = os.path.join(output_dir, f"{plugin_name}.py")
    if os.path.exists(plugin_path):
        return f"Plugin {plugin_name} already exists"
    
    # Customize template
    template = PLUGIN_TEMPLATE.replace('ExamplePlugin', plugin_name.capitalize())
    with open(plugin_path, 'w', encoding='utf-8') as f:
        f.write(template)
    return f"Created plugin: {plugin_path}"
