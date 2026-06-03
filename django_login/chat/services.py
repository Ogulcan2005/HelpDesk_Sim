import requests

OLLAMA_URL = "http://localhost:11434/api/chat"

SYSTEM_PROMPT = """
You are roleplaying as a real customer seeking technical support.

Rules:
- Never say you are an AI.
- Speak like a normal human customer.
- Be slightly confused sometimes.
- Stay consistent in your issue.
- Do not act as support agent.

Start as a customer reporting a problem.
"""


def create_history():
    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]


def generate_ai_response(history: list, user_message: str) -> str:

    if not user_message or not user_message.strip():
        return "Empty message received."

    history.append({
        "role": "user",
        "content": user_message.strip()
    })

    payload = {
        "model": "phi3",
        "messages": history,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9
        }
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=60
        )

        response.raise_for_status()

        data = response.json()

        ai_text = data.get("message", {}).get("content")

        if not ai_text:
            return "No valid response from model."

        ai_text = ai_text.strip()

        history.append({
            "role": "assistant",
            "content": ai_text
        })

        return ai_text

    except requests.exceptions.ConnectionError:
        return "Cannot connect to Ollama. Is 'ollama serve' running?"

    except requests.exceptions.Timeout:
        return "AI request timed out."

    except Exception as e:
        return f"Error: {str(e)}"