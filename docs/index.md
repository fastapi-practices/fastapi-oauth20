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

```bash
pip install fastapi-oauth20
```

### Basic Usage

```python
from fastapi import FastAPI, Depends
from fastapi_oauth20 import GitHubOAuth20, FastAPIOAuth20
from fastapi.responses import RedirectResponse
import secrets

app = FastAPI()

# 定义重定向地址
redirect_uri = "http://localhost:8000/auth/github/callback"

# 初始化 GitHub OAuth2 客户端
github_client = GitHubOAuth20(
    client_id="your_github_client_id",
    client_secret="your_github_client_secret"
)

# 创建 FastAPI OAuth2 依赖项
github_oauth = FastAPIOAuth20(
    client=github_client,
    redirect_uri=redirect_uri
)


@app.get("/auth/github")
async def github_auth():
    auth_url = await github_client.get_authorization_url(redirect_uri=redirect_uri)
    return RedirectResponse(url=auth_url)


@app.get("/auth/github/callback")
async def github_callback(oauth_result: tuple = Depends(github_oauth)):
    token_data, state = oauth_result
    user_info = await github_client.get_userinfo(token_data["access_token"])
    return {"user": user_info}
```

## 互动

[TG / Discord](https://wu-clan.github.io/homepage/)

## 赞助

如果此项目能够帮助到你，你可以赞助作者一些咖啡豆表示鼓励：[Sponsor](https://wu-clan.github.io/sponsor/)
