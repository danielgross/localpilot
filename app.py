import json
import rumps
import requests
import threading
import subprocess
import os
import sys

import config


ICON = "resources/icon.png"
ICON_INSTALLED = "resources/installed.png"
ICON_INSTALLING = "resources/installing.png"
ICON_UNINSTALLED = "resources/uninstalled.png"


def setup():
    if not os.path.exists(config.model_folder):
        if input(f"Model folder {config.model_folder} does not exist. Create it? (y/n) ").lower() == 'y':
            os.mkdir(config.model_folder)
    for model in config.models:
        if is_installed(model):
            print(f"Model {model} found in {config.model_folder}.")   
        else:
            if input(f'Model {model} not found in {config.model_folder}. Would you like to download it? (y/n) ').lower() == 'y':
                    install_model(model, True)
                

def is_installed(model):
    if config.models[model]['type'] == 'local':
        return os.path.exists(config.model_folder + "/" + config.models[model]['filename'])
    else:
        try:
            response = requests.get("http://google.com", timeout=1.0)
            return response.status_code == 200
        except requests.RequestException as e:
            return False
                

def install_model(model, verbose = False, app = None):
    url = config.models[model]['url']
    if verbose:
        print(f"Downloading {model} from {url}...")

    if app is not None:
        lock_model(model)
        subprocess.run([
            'osascript',
            '-e',
            # install the model in a new terminal window, then delete the lock file
            f'tell application "Terminal" to do script "curl -L {url} -o {os.path.join(config.model_folder, config.models[model]["filename"])} && rm {config.model_folder}/{model}.lock"'])
        return
    else:
        subprocess.run(['curl', '-L', url, '-o', os.path.join(
            config.model_folder, config.models[model]['filename'])])
        
def lock_model(model):
    with open(f"{config.model_folder}/{model}.lock", 'w') as f:
        f.write("")
        
def is_installing(model):
    if config.models[model]['type'] == 'local':
        return os.path.exists(f"{config.model_folder}/{model}.lock")
    else:
        return False
    
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

class ModelPickerApp(rumps.App):
    def __init__(self):
        super(ModelPickerApp, self).__init__("ModelPickerApp")

        # Dynamically create menu items from the MENUBAR_OPTIONS
        self.menu_items = {}
        for option in config.models:
            self.menu_items[option] = rumps.MenuItem(
                title=option, callback=self.pick_model, icon=None)
            
        self.menu_items['Settings'] = rumps.MenuItem(
            title='Settings', icon=None)
        
        self.add_settings_menu('Switch', ['Automatic', 'Trigger Offline', 'Manual'])
        self.add_settings_menu('Default Online', filter(lambda x: config.models[x]['type'] == 'remote', config.models))
        self.add_settings_menu('Default Offline', filter(lambda x: config.models[x]['type'] == 'local', config.models))
        
        self.menu = list(self.menu_items.values())
        self.menu_items[get_settings('Default Online')].state = True
        self.title = get_settings('Default Online')
        self.icon = ICON
        rumps.Timer(self.update_menu, 5).start()

    def add_settings_menu(self, name, options):
        self.menu_items["Settings"].add(rumps.MenuItem(title=name, icon=None))
        selected_option = get_settings(name)
        for option in options:
            self.menu_items["Settings"][name].add(
                rumps.MenuItem(title=option, callback=lambda sender: self.set_setting(sender, name), icon=None))
            if option == selected_option:
                self.menu_items["Settings"][name][option].state = True

    def set_setting(self, sender, setting):
        if sender.state:
            return
        
        set_settings(setting, sender.title)

        for item in self.menu['Settings'][setting]:
            self.menu_items['Settings'][setting][item].state = item == sender.title


    def update_menu(self, sender):
        for option in self.menu_items:
            if not option in config.models:
                continue
            if is_installing(option):
                self.menu_items[option].icon = ICON_INSTALLING
            elif is_installed(option):
                self.menu_items[option].icon = ICON_INSTALLED
            else:
                self.menu_items[option].icon = ICON_UNINSTALLED

        currently_online = config.models[self.title]['type'] == 'remote'

        if currently_online and get_settings('Switch') == 'Automatic' or get_settings('Switch') == 'Trigger Offline':
            try:
                response = requests.get("http://google.com", timeout=1.0)
                if response.status_code != 200:
                    self.pick_model(self.menu_items[get_settings('Default Offline')])
            except requests.RequestException as e:
                self.pick_model(self.menu_items[get_settings('Default Offline')])
        
        if not currently_online and get_settings('Switch') == 'Automatic':
            try:
                response = requests.get("http://google.com", timeout=1.0)
                if response.status_code == 200:
                    self.pick_model(self.menu_items[get_settings('Default Online')])
            except requests.RequestException as e:
                pass

    def pick_model(self, sender):
        if (sender.state):
            return
        
        # check if the model is installed
        if is_installing(sender.title):
            rumps.alert("Model Installing", f"{sender.title} is currently installing.")
            return
        elif not is_installed(sender.title):
            if config.models[sender.title]['type'] == 'remote':
                return
            if (rumps.alert("Install Model", f"Install {sender.title}?", cancel = True) == 1):
                install_model(sender.title, app = self)
                return
            else:
                return

        # Send the choice to the local proxy app
        if sender.state:
            choice = sender.title
            try:
                response = requests.post(
                    "http://localhost:5001/set_target", json={"target": choice}, timeout=1.0)
                if response.status_code == 200:
                    print(f"Successfully sent selection: {choice}.")
                else:
                    rumps.alert(
                        "Error", f"Failed to send selection. Server responded with: {response.status_code}.")
            except requests.RequestException as e:
                rumps.alert("Error", f"Failed to send selection. Error: {e}.")
                return
        
        # Toggle the checked status of the clicked menu item
        self.title = sender.title

        # If other options were previously selected, deselect them
        for item in self.menu:
            if item == 'Quit':
                continue
            self.menu_items[item].state = item == sender.title

    def run_server(self):
        subprocess.run(['python', 'proxy.py'])


if __name__ == '__main__':
    if '--setup' in sys.argv:
        setup()
    app = ModelPickerApp()
    print("Running server...")
    server_thread = threading.Thread(target=app.run_server)
    server_thread.start()
    app.run()
