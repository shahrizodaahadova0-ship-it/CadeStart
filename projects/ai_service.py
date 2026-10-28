"""Small Responses API adapter. Credentials never leave the server."""
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


class AIUnavailable(Exception):
    pass


def available():
    return bool(settings.OPENAI_API_KEY and settings.OPENAI_MODEL)


def answer(question, history, role, language):
    if not available():
        raise AIUnavailable('not_configured')
    instruction = (
        'You are the CodeStart educational mentor. Explain programming concepts, ask '
        'guiding questions and offer small examples. Never claim to run code or verify '
        'repositories. Do not change grades, task status, or account data. '
    )
    if role == 'manager':
        instruction += 'Act as a virtual project manager: help clarify requirements, priorities and estimates. Do not promise real approvals. '
    instruction += 'Respond in Uzbek.' if language == 'uz' else 'Respond in Russian.'
    inputs = [{'role': message['role'], 'content': message['content'][:4000]} for message in history[-10:]]
    inputs.append({'role': 'user', 'content': question})
    body = {'model': settings.OPENAI_MODEL, 'instructions': instruction,
            'input': inputs, 'store': False, 'max_output_tokens': 1200}
    request = Request('https://api.openai.com/v1/responses', data=json.dumps(body).encode('utf-8'),
                      headers={'Authorization': f'Bearer {settings.OPENAI_API_KEY}', 'Content-Type': 'application/json'}, method='POST')
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read(2_000_000))
        parts = []
        for output in payload.get('output', []):
            if output.get('type') == 'message':
                for content in output.get('content', []):
                    if content.get('type') == 'output_text':
                        parts.append(content.get('text', ''))
                    elif content.get('type') == 'refusal':
                        parts.append(content.get('refusal', ''))
        text = '\n'.join(parts).strip()
        if not text:
            raise AIUnavailable('empty_response')
        return text[:20000]
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError, AttributeError) as exc:
        raise AIUnavailable('provider_error') from exc
