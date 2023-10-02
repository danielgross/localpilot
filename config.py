import os

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
    'CodeLlama-34b': {
        'url': 'https://huggingface.co/TheBloke/CodeLlama-34B-Instruct-GGUF/resolve/main/codellama-34b-instruct.Q4_K_M.gguf',
        'type': 'local',
        'filename': 'codellama-34b-instruct.Q4_K_M.gguf',
    },
    'default': 'GitHub',
}

model_folder = os.path.expanduser('~/models')
