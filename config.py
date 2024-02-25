import os
import json

ICON = "resources/icon.png"
ICON_INSTALLED = "resources/installed.png"
ICON_INSTALLING = "resources/installing.png"
ICON_UNINSTALLED = "resources/uninstalled.png"

SETTINGS_CURRENT_MODEL = "Current Model"
SETTINGS_SHOW_UNINSTALLED = "Show Uninstalled"
SETTINGS_SHOW_STATUS_ICONS = "Show Status Icons"
SETTINGS_SHOW_CURRENT_MODEL = "Show Current Model"
SETTINGS_DEFAULT_ONLINE = "Default Online"
SETTINGS_DEFAULT_OFFLINE = "Default Offline"
SETTINGS_SWITCH = "Switch"

SWITCH_AUTOMATIC = "Automatic"
SWITCH_TRIGGER_OFFLINE = "Trigger Offline"
SWITCH_MANUAL = "Manual"

models = {
    'GitHub': {
        'domain': 'https://copilot-proxy.githubusercontent.com',
        'type': 'remote',
    },
    'CodeLlama-7b': {
        'url': 'https://huggingface.co/TheBloke/CodeLlama-7B-GGUF/resolve/main/codellama-7b.Q5_K_S.gguf',
        'type': 'local',
        'filename': 'codellama-7b.Q5_K_S.gguf',
    },
    'Mistral-7b': {
        'url': 'https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q5_K_M.gguf',
        'type': 'local',
        'filename': 'mistral-7b-instruct-v0.1.Q5_K_M.gguf',
    },
    "stable-code-3b": {
        "url": "https://huggingface.co/stabilityai/stable-code-3b/resolve/main/stable-code-3b-Q5_K_M.gguf",
        "type": "local",
        "filename": "stable-code-3b-Q5_K_M.gguf",
    },
    'CodeLlama-34b': {
        'url': 'https://huggingface.co/TheBloke/CodeLlama-34B-Instruct-GGUF/resolve/main/codellama-34b-instruct.Q4_K_M.gguf',
        'type': 'local',
        'filename': 'codellama-34b-instruct.Q4_K_M.gguf',
    }
}

model_folder = os.path.expanduser('~/models')
    
def set_settings(setting, value):
    with open('settings.json', 'r') as f:
        settings = json.load(f)

    settings[setting] = value

    with open('settings.json', 'w') as f:
        json.dump(settings, f, indent=4)

def get_settings(setting):
    with open('settings.json', 'r') as f:
        settings = json.load(f)

    return settings[setting]
