# 用法

本页用 GitHub 登录演示完整流程。其他平台的用法类似：替换客户端类、回调地址和平台后台配置即可。

## 完整流程

```python
from typing import Annotated, Any

from fastapi import Depends, FastAPI
from fastapi.responses import RedirectResponse

from fastapi_oauth20 import FastAPIOAuth20, GitHubOAuth20

app = FastAPI()
redirect_uri = "http://localhost:8000/auth/github/callback"

github_client = GitHubOAuth20(
    client_id="your_github_client_id",
    client_secret="your_github_client_secret",
)
github_callback = FastAPIOAuth20(github_client, redirect_uri=redirect_uri)


@app.get("/auth/github")
async def login_with_github():
    auth_url = await github_client.get_authorization_url(
        redirect_uri=redirect_uri,
        state="random_state",
    )
    return RedirectResponse(url=auth_url)


@app.get("/auth/github/callback")
async def github_callback_handler(
    oauth_result: Annotated[
        tuple[dict[str, Any], str | None],
        Depends(github_callback),
    ],
):
    token_data, state = oauth_result
    user_info = await github_client.get_userinfo(token_data["access_token"])
    return {"user": user_info, "state": state}
```

流程说明：

1. `/auth/github` 生成第三方授权地址，并把用户重定向到 GitHub。
2. 用户确认授权后，GitHub 回调 `/auth/github/callback`。
3. `FastAPIOAuth20` 自动用 `code` 换取 `access_token`。
4. 你拿到 `access_token` 后调用 `get_userinfo()` 获取用户信息。

## 常用能力

### 自定义授权参数

`get_authorization_url()` 支持 `state`、`scope`、PKCE 和额外查询参数：

```python
async def build_custom_auth_url() -> str:
    return await github_client.get_authorization_url(
        redirect_uri="http://localhost:8000/auth/github/callback",
        state="random_state",
        scope=["user", "user:email"],
    )
```

### 刷新令牌

部分平台支持 `refresh_token`，例如 Google、Gitee、OSChina、LinuxDo、微信等：

```python
from typing import Any

from fastapi import HTTPException

from fastapi_oauth20 import GoogleOAuth20

google_client = GoogleOAuth20(
    client_id="your_google_client_id",
    client_secret="your_google_client_secret",
)


async def refresh_google_token(refresh_token: str) -> dict[str, Any]:
    try:
        return await google_client.refresh_token(refresh_token)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
```

### 撤销令牌

如果平台提供撤销接口，可以在用户退出登录时调用：

```python
async def revoke_google_token(access_token: str) -> dict[str, str]:
    try:
        await google_client.revoke_token(access_token)
        return {"message": "令牌已撤销"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
```

## 错误处理

授权回调失败时，`FastAPIOAuth20` 会抛出 `OAuth20AuthorizeCallbackError`。它继承自 FastAPI 的 `HTTPException`，可以直接交给默认异常处理器，也可以自定义返回结构：

```python
from fastapi import Request
from fastapi.responses import JSONResponse

from fastapi_oauth20 import OAuth20AuthorizeCallbackError


@app.exception_handler(OAuth20AuthorizeCallbackError)
async def oauth_error_handler(request: Request, exc: OAuth20AuthorizeCallbackError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": "OAuth2 授权失败", "detail": exc.detail},
    )
```

## 接入建议

- `redirect_uri` 必须和第三方平台后台配置完全一致。
- 生产环境请使用 HTTPS。
- 每次发起授权时生成随机 `state`，回调时校验它。
- 只申请必要的 `scope`，避免过度授权。
- 不要把 `client_secret`、`access_token`、`refresh_token` 暴露给前端。
- 用户绑定建议使用 `source + sid`，不要只依赖第三方用户 ID。

## 演示项目

完整项目可参考：[fastapi-oauth20-demo](https://github.com/fastapi-practices/fastapi-oauth20-demo)。
