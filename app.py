from argparse import ArgumentParser
import rumps
import requests
import threading
import subprocess
import os

import config


def setup():
    if not os.path.exists(config.model_folder):
        if input(f"Model folder {config.model_folder} does not exist. Create it? (y/n) ").lower() == 'y':
            os.mkdir(config.model_folder)
    current = os.listdir(config.model_folder)
    for model in config.models:
        if model == 'default':
            continue
        if config.models[model]['type'] == 'local':
            if config.models[model]['filename'] not in current:
                if input(f'Model {model} not found in {config.model_folder}. Would you like to download it? (y/n) ').lower() == 'y':
                    url = config.models[model]['url']
                    print(f"Downloading {model} from {url}...")
                    subprocess.run(['curl', '-L', url, '-o', os.path.join(
                        config.model_folder, config.models[model]['filename'])])
            else:
                print(f"Model {model} found in {config.model_folder}.")


class ModelPickerApp(rumps.App):
    def __init__(self, proxy_port=5001, local_server_port=8000):
        super(ModelPickerApp, self).__init__("ModelPickerApp")

        self.proxy_port = proxy_port
        self.local_server_port = local_server_port

        # Dynamically create menu items from the MENUBAR_OPTIONS
        self.menu_items = {}
        for option in config.models:
            if option == 'default':
                continue
            self.menu_items[option] = rumps.MenuItem(
                title=option, callback=self.pick_model)

        self.menu = list(self.menu_items.values())
        self.menu_items[config.models['default']].state = True
        self.icon = "icon.png"

    def pick_model(self, sender):
        # Toggle the checked status of the clicked menu item
        sender.state = not sender.state

        # Send the choice to the local proxy app
        if sender.state:
            choice = sender.title
            try:
                response = requests.post(
                    f"http://localhost:{self.proxy_port}/set_target",
                    json={"target": choice})
                if response.status_code == 200:
                    print(f"Successfully sent selection: {choice}.")
                else:
                    rumps.alert(
                        "Error", f"Failed to send selection. Server responded with: {response.status_code}.")
            except requests.RequestException as e:
                rumps.alert("Error", f"Failed to send selection. Error: {e}.")

        # If other options were previously selected, deselect them
        for item in self.menu:
            if item == 'Quit':
                continue
            if item != sender.title:
                self.menu_items[item].state = False

    def run_server(self):
        subprocess.run([
            'python', 'proxy.py', '--port', str(self.proxy_port),
            '--local-server-port', str(self.local_server_port),
        ])


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--proxy-port', type=int, default=5001)
    parser.add_argument('--local-server-port', type=int, default=8000)
    parser.add_argument('--setup', action='store_true')
    args = parser.parse_args()

    if args.setup:
        setup()
    app = ModelPickerApp(
        proxy_port=args.proxy_port,
        local_server_port=args.local_server_port,
    )
    print("Running server...")
    server_thread = threading.Thread(target=app.run_server)
    server_thread.start()
    app.run()
