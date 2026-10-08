import os
import requests
import json
from dotenv import load_dotenv




# load all the local enviorment variable
load_dotenv()


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def ask(prompt):
    try:
        responce = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            },
            data = json.dumps({
                # here we have the model
                "model": "xiaomi/mimo-v2.6-pro",
                "messages": [
                {
                    "role": "user",
                    # the prompt
                    "content": f"{prompt}"
                }
            ]
            })
        )
    except timeout:
        # One retry
        pass

