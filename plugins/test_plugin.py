"""
Example plugin for Stitch RAT
Place this file in the 'plugins' directory
"""

PLUGIN_INFO = {
    'name': 'Test_plugin',
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
    print("[Test_plugin] Loaded!")

def on_unload(manager):
    """Called when plugin is unloaded"""
    print("[Test_plugin] Unloaded!")

def example_command(args):
    """Example command handler"""
    return f"Example plugin executed with args: {args}"

def example_help(args):
    """Command help"""
    return "example - Demonstrates plugin system"

def on_connect(client_id):
    """Hook triggered when client connects"""
    print(f"[Test_plugin] Client {client_id} connected")

def on_command(cmd, args):
    """Hook triggered before command execution"""
    print(f"[Test_plugin] Command: {cmd} {args}")
