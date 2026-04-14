"""Wrapper thin sobre Anthropic SDK"""

from anthropic import Anthropic
from config import CLAUDE_MODEL, MAX_TOKENS

client = Anthropic()


def call_claude(system_prompt: str, messages: list) -> str:
    """
    Llama a Claude y devuelve la respuesta como string.

    Args:
        system_prompt: instrucciones para Claude
        messages: lista de dicts {role: "user"|"assistant", content: "..."}

    Returns:
        string con la respuesta de Claude
    """
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=messages
        )
        return response.content[0].text
    except Exception as e:
        print(f"Error llamando a Claude: {e}")
        raise
