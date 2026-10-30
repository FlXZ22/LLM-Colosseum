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
            data=json.dumps(
                {
                    # here we have the model
                    "model": "xiaomi/mimo-v2.6-pro",
                    "messages": [
                        {
                            "role": "user",
                            # the prompt
                            "content": f"{prompt}",
                        }
                    ],
                }
            ),
            timeout=30,
        )
        if responce.status_code != 200:
            return None, responce.status_code
        # the network error
        else:
            try:
                message = json.loads(responce.text)
                # return message, status_code
                return (
                    message.get("choices")[0].get("message").get("content"),
                    responce.status_code,
                )
            except (IndexError, AttributeError, TypeError, ValueError):
                return None, responce.status_code
    except requests.RequestException:
        try:
            return None, responce.status_code
        except UnboundLocalError:
            return None, None


if __name__ == "__main__":
    responce = ask("Give me a fully valid JSON")
    print(responce)
