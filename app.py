import rumps
import requests
import threading
import subprocess
import os
import sys

import config

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

class ModelPickerApp(rumps.App):
    def __init__(self):
        super(ModelPickerApp, self).__init__("ModelPickerApp", quit_button=None)

        self.rebuild_menu()
        self.icon = config.ICON
        rumps.Timer(self.update_menu, 5).start()

    def rebuild_menu(self):
        self.menu.clear()
        self.menu_items = {}
        show_uninstalled = config.get_settings(config.SETTINGS_SHOW_UNINSTALLED)
        for option in config.models:
            if not show_uninstalled and config.models[option]['type'] == 'local' and not is_installed(option):
                continue
            self.menu_items[option] = rumps.MenuItem(
                title=option, callback=self.pick_model, icon=None)
            
        self.menu_items['Settings'] = rumps.MenuItem(
            title='Settings', icon=None)
        
        self.add_bool_setting(config.SETTINGS_SHOW_UNINSTALLED, True)
        self.add_bool_setting(config.SETTINGS_SHOW_STATUS_ICONS, True)
        self.add_bool_setting(config.SETTINGS_SHOW_CURRENT_MODEL, True)
        self.add_settings_menu(config.SETTINGS_SWITCH, ['Automatic', 'Trigger Offline', 'Manual'])
        self.add_settings_menu(config.SETTINGS_DEFAULT_ONLINE, filter(lambda x: config.models[x]['type'] == 'remote', config.models))
        self.add_settings_menu(config.SETTINGS_DEFAULT_OFFLINE, filter(lambda x: config.models[x]['type'] == 'local' and (show_uninstalled or is_installed(x)), config.models))

        self.menu_items['Quit'] = rumps.MenuItem(title='Quit', callback=rumps.quit_application, icon=None)

        self.menu = list(self.menu_items.values())
        self.menu_items[config.get_settings(config.SETTINGS_CURRENT_MODEL)].state = True
        self.update_menu(None)

        if config.get_settings(config.SETTINGS_SHOW_CURRENT_MODEL):
            self.title = config.get_settings(config.SETTINGS_CURRENT_MODEL)
        else:
            self.title = None

    def add_settings_menu(self, name, options, triggerRebuild = False):
        self.menu_items["Settings"].add(rumps.MenuItem(title=name, icon=None))
        selected_option = config.get_settings(name)

        for option in options:
            self.menu_items["Settings"][name].add(
                rumps.MenuItem(title=option, callback=lambda sender: self.set_setting(sender, name, triggerRebuild), icon=None))
            if option == selected_option:
                self.menu_items["Settings"][name][option].state = True

    def add_bool_setting(self, name, triggerRebuild = False):
        self.menu_items["Settings"].add(
                rumps.MenuItem(title=name, callback=lambda sender: self.set_bool_setting(sender, name, triggerRebuild), icon=None))
        self.menu_items["Settings"][name].state = config.get_settings(name)

    def set_setting(self, sender, setting, triggerRebuild = False):
        if sender.state:
            return
        
        config.set_settings(setting, sender.title)

        if triggerRebuild:
            self.rebuild_menu()
        else:
            for item in self.menu['Settings'][setting]:
                self.menu_items['Settings'][setting][item].state = item == sender.title

    def set_bool_setting(self, sender, setting, triggerRebuild = False):
        config.set_settings(setting, not sender.state)

        if triggerRebuild:
            self.rebuild_menu()
        else:
            sender.state = config.get_settings(setting)


    def update_menu(self, sender):
        status_icons = config.get_settings(config.SETTINGS_SHOW_STATUS_ICONS)
        for option in self.menu_items:
            if not option in config.models:
                continue
            if status_icons:
                if is_installing(option):
                    self.menu_items[option].icon = config.ICON_INSTALLING
                elif is_installed(option):
                    self.menu_items[option].icon = config.ICON_INSTALLED
                else:
                    self.menu_items[option].icon = config.ICON_UNINSTALLED
            else:
                self.menu_items[option].icon = None

        currently_online = config.models[config.get_settings(config.SETTINGS_CURRENT_MODEL)]['type'] == 'remote'

        if currently_online and config.get_settings(config.SETTINGS_SWITCH) == 'Automatic' or config.get_settings(config.SETTINGS_SWITCH) == 'Trigger Offline':
            try:
                response = requests.get("http://google.com", timeout=1.0)
                if response.status_code != 200:
                    self.pick_model(self.menu_items[config.get_settings(config.SETTINGS_DEFAULT_OFFLINE)])
            except requests.RequestException as e:
                self.pick_model(self.menu_items[config.get_settings(config.SETTINGS_DEFAULT_OFFLINE)])
        
        if not currently_online and config.get_settings(config.SETTINGS_SWITCH) == 'Automatic':
            try:
                response = requests.get("http://google.com", timeout=1.0)
                if response.status_code == 200:
                    self.pick_model(self.menu_items[config.get_settings(config.SETTINGS_DEFAULT_ONLINE)])
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
        if config.get_settings(config.SETTINGS_SHOW_CURRENT_MODEL):
            self.title = sender.title
        config.set_settings(config.SETTINGS_CURRENT_MODEL, sender.title)

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
