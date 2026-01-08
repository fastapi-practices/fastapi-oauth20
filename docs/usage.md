from fastapi_oauth20 import FastAPIOAuth20

# 使用指南

本指南介绍如何将 FastAPI OAuth2.0 库与各种 OAuth2 提供程序一起使用。

## 基本用法

### 1. 选择 OAuth2 提供商并初始化客户端

```python
from fastapi_oauth20 import GitHubOAuth20, GoogleOAuth20, FastAPIOAuth20
from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse
import secrets

app = FastAPI()

# 初始化 GitHub OAuth2 客户端
github_client = GitHubOAuth20(
    client_id="your_github_client_id",
    client_secret="your_github_client_secret"
)
```

### 2. 创建 FastAPI OAuth2 依赖

```python
# 创建 FastAPI OAuth2 依赖
github_oauth = FastAPIOAuth20(
    client=github_client,
    redirect_uri="http://localhost:8000/auth/github/callback"
)
```

### 3. 定义授权端点

```python
@app.get("/oauth2/github")
async def oauth2_github():
    """重定向用户到 OAuth2 提供商进行授权"""

    # 生成安全的 state 参数用于 CSRF 保护
    state = secrets.token_urlsafe(32)

    auth_url = await github_client.get_authorization_url(
        redirect_uri="http://localhost:8000/auth/github/callback",
        state=state
    )

    return RedirectResponse(url=auth_url)
```

### 4. 处理 OAuth 回调

```python
@app.get("/oauth2/github/callback")
async def oauth2_github_callback(
        oauth_result: Annotated[
            FastAPIOAuth20,
            Depends(github_oauth),
        ],
):
    """处理 GitHub OAuth 回调"""
    token_data, state = oauth_result

    # 获取用户信息
    user_info = await github_client.get_userinfo(token_data["access_token"])

    return {
        "user": user_info,
        "access_token": token_data["access_token"],
        "state": state
    }
```

## 令牌刷新

某些提供商支持刷新令牌来延长会话：

```python
@app.post("/oauth2/refresh")
async def oauth2_refresh_token(refresh_token: str):
    """使用刷新令牌获取新的访问令牌"""
    try:
        new_tokens = await google_client.refresh_token(refresh_token)
        return {"access_token": new_tokens["access_token"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## 令牌撤销

用户登出时撤销令牌：

```python
@app.post("/oauth2/revoke")
async def oauth2_revoke_token(access_token: str):
    """撤销访问令牌"""
    try:
        await google_client.revoke_token(access_token)
        return {"message": "令牌撤销成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## 错误处理

如果回调逻辑内部发生错误（用户拒绝访问、授权代码无效......），依赖关系将引发 `OAuth20AuthorizeCallbackError` 错误

它继承自 FastAPI 的 [HTTPException](https://fastapi.tiangolo.com/reference/exceptions/#fastapi.HTTPException)，因此默认的
FastAPI 异常处理程序会自动对其进行处理。您可以通过为 `OAuth20AuthorizeCallbackError` 实现自己的异常处理程序来自定义此行为

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi_oauth20 import OAuth20AuthorizeCallbackError

app = FastAPI()


@app.exception_handler(OAuth20AuthorizeCallbackError)
async def oauth2_authorize_callback_error_handler(request: Request, exc: OAuth20AuthorizeCallbackError):
    detail = exc.detail
    status_code = exc.status_code
    return JSONResponse(
        status_code=status_code,
        content={"message": "The OAuth2 callback failed", "detail": detail},
    )
```

## 完整示例

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


# 错误处理
@app.exception_handler(OAuth20AuthorizeCallbackError)
async def oauth_error_handler(request, exc):
    return {"error": "授权失败", "detail": exc.detail}
```

## 注意事项

1. **安全性**: 始终使用 HTTPS 端点
2. **状态管理**: 使用安全的 state 参数防止 CSRF 攻击
3. **令牌存储**: 安全地存储访问令牌和刷新令牌
4. **错误处理**: 妥善处理各种 OAuth2 错误场景
5. **作用域**: 只请求必要的作用域，遵循最小权限原则
