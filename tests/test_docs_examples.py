import asyncio
import re

from collections.abc import Iterable
from pathlib import Path
from typing import Any

import httpx
import respx

from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from fastapi_oauth20 import FastAPIOAuth20, GitHubOAuth20, GoogleOAuth20, OAuth20AuthorizeCallbackError


FENCE_RE = re.compile(r'```(?P<lang>[^\n`]*)\n(?P<code>.*?)```', re.DOTALL)
DOCS_DIR = Path(__file__).resolve().parents[1] / 'docs'
SUPPORTED_EXAMPLE_LANGUAGES = {'bash', 'python', 'sh'}


def iter_code_fences() -> Iterable[tuple[Path, int, str, str]]:
    for path in sorted(DOCS_DIR.rglob('*.md')):
        for index, match in enumerate(FENCE_RE.finditer(path.read_text(encoding='utf-8')), 1):
            yield path, index, match.group('lang').strip(), match.group('code')


def python_blocks(path: str) -> list[str]:
    doc = DOCS_DIR / path
    return [code for item_path, _, lang, code in iter_code_fences() if item_path == doc and lang == 'python']


def exec_blocks(blocks: Iterable[str]) -> dict[str, Any]:
    namespace: dict[str, Any] = {'__name__': '__docs_example__'}
    for block in blocks:
        exec(compile(block, '<docs-example>', 'exec'), namespace)
    return namespace


def mock_github_oauth() -> None:
    respx.post('https://github.com/login/oauth/access_token').mock(
        return_value=httpx.Response(200, json={'access_token': 'doc_access_token', 'token_type': 'bearer'})
    )
    respx.get('https://api.github.com/user').mock(
        return_value=httpx.Response(200, json={'id': 1, 'login': 'docs-user', 'email': 'docs@example.com'})
    )


def test_every_fenced_code_block_has_a_docs_test_strategy():
    fences = list(iter_code_fences())
    assert fences

    unsupported = [
        f'{path.relative_to(DOCS_DIR)}#{index}:{lang or "<empty>"}'
        for path, index, lang, _ in fences
        if lang not in SUPPORTED_EXAMPLE_LANGUAGES
    ]
    assert unsupported == []


def test_shell_examples_use_current_package_name():
    shell_blocks = [(path, index, code) for path, index, lang, code in iter_code_fences() if lang in {'bash', 'sh'}]
    assert shell_blocks

    for path, index, code in shell_blocks:
        commands = [line.strip() for line in code.splitlines() if line.strip()]
        assert commands, f'{path.relative_to(DOCS_DIR)}#{index} is empty'
        for command in commands:
            assert command in {
                'pip install fastapi-oauth20',
                'uv add fastapi-oauth20',
            }


def test_python_examples_compile_and_execute():
    for path, index, lang, code in iter_code_fences():
        if lang != 'python':
            continue

        namespace = {
            '__name__': '__docs_example__',
            # A few guide snippets are intentionally incremental. These
            # sentinels keep individual snippets executable while the route
            # behavior is tested with the full incremental examples below.
            'Annotated': __import__('typing').Annotated,
            'Any': Any,
            'Depends': Depends,
            'FastAPI': FastAPI,
            'FastAPIOAuth20': FastAPIOAuth20,
            'GitHubOAuth20': GitHubOAuth20,
            'GoogleOAuth20': GoogleOAuth20,
            'HTTPException': HTTPException,
            'OAuth20AuthorizeCallbackError': OAuth20AuthorizeCallbackError,
            'app': FastAPI(),
            'github_client': GitHubOAuth20('docs_client_id', 'docs_client_secret'),
            'github_oauth': FastAPIOAuth20(
                GitHubOAuth20('docs_client_id', 'docs_client_secret'),
                redirect_uri='http://localhost:8000/auth/github/callback',
            ),
            'google_client': GoogleOAuth20('docs_client_id', 'docs_client_secret'),
        }
        exec(compile(code, f'{path.relative_to(DOCS_DIR)}#{index}', 'exec'), namespace)


def test_index_quick_start_example_generates_login_url():
    blocks = python_blocks('index.md')
    assert len(blocks) == 1
    namespace = exec_blocks(blocks)

    auth_url = asyncio.run(namespace['build_login_url']())
    assert 'github.com/login/oauth/authorize' in auth_url
    assert 'client_id=your_github_client_id' in auth_url
    assert 'state=random_state' in auth_url


@respx.mock
def test_usage_complete_flow_example_runs_end_to_end():
    blocks = python_blocks('usage.md')
    assert len(blocks) == 5
    namespace = exec_blocks([blocks[0]])
    app = namespace['app']
    client = TestClient(app)

    mock_github_oauth()
    github_auth = client.get('/auth/github', follow_redirects=False)
    assert github_auth.status_code in {302, 307}
    assert 'github.com/login/oauth/authorize' in github_auth.headers['location']

    github_callback = client.get('/auth/github/callback?code=docs_code&state=docs_state')
    assert github_callback.status_code == 200
    assert github_callback.json() == {
        'user': {'id': 1, 'login': 'docs-user', 'email': 'docs@example.com'},
        'state': 'docs_state',
    }


@respx.mock
def test_usage_token_examples_run():
    blocks = python_blocks('usage.md')
    namespace = exec_blocks([blocks[2], blocks[3]])

    respx.post('https://oauth2.googleapis.com/token').mock(
        return_value=httpx.Response(200, json={'access_token': 'refreshed_doc_access_token'})
    )
    refresh_result = asyncio.run(namespace['refresh_google_token']('docs_refresh_token'))
    assert refresh_result == {'access_token': 'refreshed_doc_access_token'}

    respx.post('https://accounts.google.com/o/oauth2/revoke').mock(return_value=httpx.Response(200, text='OK'))
    revoke_result = asyncio.run(namespace['revoke_google_token']('doc_access_token'))
    assert revoke_result == {'message': '令牌已撤销'}


def test_usage_custom_error_handler_example_returns_documented_shape():
    blocks = python_blocks('usage.md')
    namespace = exec_blocks([blocks[0], blocks[4]])
    app = namespace['app']

    @app.get('/docs-error')
    async def docs_error():
        raise OAuth20AuthorizeCallbackError(status_code=400, detail='access_denied')

    response = TestClient(app).get('/docs-error')
    assert response.status_code == 400
    assert response.json() == {'message': 'OAuth2 授权失败', 'detail': 'access_denied'}
