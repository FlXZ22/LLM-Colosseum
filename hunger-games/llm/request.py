import os
import requests
import json
from dotenv import load_dotenv

# load all the local enviorment variable
load_dotenv()


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def ask(prompt):
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

        if responce.status_code != 200:
            return None
        else:
            try: 
                message = json.loads(responce.text)
                return message.get("choices")[0].get("message").get("content")
            except (IndexError, AttributeError, TypeError, ValueError):
                return None


responce = ask("Give me a fully valid JSON")

print(responce)
