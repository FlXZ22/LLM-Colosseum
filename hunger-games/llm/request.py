import os
import requests
import json
from dotenv import load_dotenv
from config import balance

# load all the local enviorment variable
load_dotenv()


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def ask(prompt):
    try:
        responce = requests.post(
            # using requests config in the url
            url= balance.URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            },
            data=json.dumps(
                {
                    # here we have the model
                    "model": balance.MODEL,
                    "messages": [
                        {
                            "role": "user",
                            # the prompt
                            "content": f"{prompt}",
                        }
                    ],
                }
            ),
            # we set the timeout of the requests to 30 sec
            timeout=30,
        )
        # if the responce status_code is different than 200
        if responce.status_code != 200:
            return f"Error: {responce.status_code}", None, responce.status_code, None
        else:
            try:
                usage = None
                # we transform it into json
                message = json.loads(responce.text)

                if isinstance(message, dict):
                    usage = message.get("usage")

                # return message, status_code
                llm_responce = message.get("choices")[0].get("message").get("content")

                # if none and if empty
                if llm_responce is None or not llm_responce.strip():
                    return "NullContent", None, responce.status_code, usage

                return (
                    "Success",
                    llm_responce,
                    responce.status_code,
                    usage
                )
            # expect the massage does not convert (the KeyError is for the choices empty)
            # the choices does not exist
            except (IndexError, AttributeError, TypeError, ValueError, KeyError):
                return "JsonError", None, responce.status_code, usage

    except requests.exceptions.Timeout:
        return "Timeout", None, None, None
    except requests.exceptions.ConnectionError:
        return "ConnectionError", None, None, None
    except requests.RequestException:
        return "RequestException", None, None, None


if __name__ == "__main__":
    responce = ask("Give me a fully valid JSON")
    print(responce)
