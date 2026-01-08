# FastAPI OAuth 2.0

在 FastAPI 中异步授权 OAuth 2.0 客户端

## Features

- **异步支持** - 使用 async/await 构建以获得最佳性能
- **令牌管理** - 内置令牌刷新和吊销
- **FastAPI 集成** - 用于回调处理的无缝依赖注入
- **类型安全** - 完整类型提示
- **错误处理** - OAuth2 错误的综合异常层次结构

## Quick Start

### Installation

=== "pip"

    ```bash
    pip install fastapi-oauth20
    ```

=== "uv"

    ```bash
    uv add fastapi-oauth20
    ```

### Basic Usage

```python
from typing import Annotated

from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse

from fastapi_oauth20 import GitHubOAuth20, FastAPIOAuth20

app = FastAPI()

redirect_uri = "http://localhost:8000/auth/github/callback"

github_client = GitHubOAuth20(
    client_id="your_github_client_id",
    client_secret="your_github_client_secret"
)


@app.get("/auth/github")
async def github_auth():
    auth_url = await github_client.get_authorization_url(redirect_uri=redirect_uri)
    return RedirectResponse(url=auth_url)


@app.get("/auth/github/callback")
async def github_callback(
        oauth2: Annotated[
            FastAPIOAuth20,
            Depends(FastAPIOAuth20(github_client, redirect_uri=redirect_uri)),
        ],
):
    token_data, state = oauth2
    access_token = token_data['access_token']
    user_info = await github_client.get_userinfo(access_token)
    return {"user": user_info}
```
