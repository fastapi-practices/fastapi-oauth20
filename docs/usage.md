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

# 初始化 Google OAuth2 客户端
google_client = GoogleOAuth20(
    client_id="your_google_client_id",
    client_secret="your_google_client_secret"
)
```

### 2. 创建 FastAPI OAuth2 依赖

```python
# 创建 FastAPI OAuth2 依赖
github_oauth = FastAPIOAuth20(
    client=github_client,
    redirect_uri="http://localhost:8000/auth/github/callback"
)

google_oauth = FastAPIOAuth20(
    client=google_client,
    redirect_uri="http://localhost:8000/auth/google/callback"
)
```

### 3. 定义授权端点

```python
@app.get("/auth/{provider}")
async def auth_provider(provider: str):
    """重定向用户到 OAuth2 提供商进行授权"""

    # 生成安全的 state 参数用于 CSRF 保护
    state = secrets.token_urlsafe(32)

    if provider == "github":
        auth_url = await github_client.get_authorization_url(
            redirect_uri="http://localhost:8000/auth/github/callback",
            state=state
        )
    elif provider == "google":
        auth_url = await google_client.get_authorization_url(
            redirect_uri="http://localhost:8000/auth/google/callback",
            state=state
        )
    else:
        raise HTTPException(status_code=404, detail="不支持的提供商")

    return RedirectResponse(url=auth_url)
```

### 4. 处理 OAuth 回调

```python
from typing import Tuple, Dict, Any


@app.get("/auth/github/callback")
async def github_callback(
        oauth_result: Tuple[Dict[str, Any], str] = Depends(github_oauth)
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


@app.get("/auth/google/callback")
async def google_callback(
        oauth_result: Tuple[Dict[str, Any], str] = Depends(google_oauth)
):
    """处理 Google OAuth 回调"""
    token_data, state = oauth_result

    # 获取用户信息
    user_info = await google_client.get_userinfo(token_data["access_token"])

    return {
        "user": user_info,
        "access_token": token_data["access_token"],
        "state": state
    }
```

## 高级用法

### PKCE (Proof Key for Code Exchange)

对于公共客户端（移动应用、SPA），使用 PKCE 增强安全性：

```python
import base64
import hashlib
import secrets


def generate_pkce_challenge():
    """生成 PKCE 代码验证器和挑战码"""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge


@app.get("/auth/github/pkce")
async def github_auth_pkce():
    """GitHub OAuth with PKCE"""
    code_verifier, code_challenge = generate_pkce_challenge()
    state = secrets.token_urlsafe(32)

    # 在实际应用中，应该将 code_verifier 和 state 存储在会话或数据库中
    # 这里为了演示目的简化处理

    auth_url = await github_client.get_authorization_url(
        redirect_uri="http://localhost:8000/auth/github/callback",
        state=state,
        code_challenge=code_challenge,
        code_challenge_method="S256"
    )

    return RedirectResponse(url=auth_url)
```

### 令牌刷新

某些提供商支持刷新令牌来延长会话：

```python
@app.post("/auth/refresh")
async def refresh_token(refresh_token: str, provider: str):
    """使用刷新令牌获取新的访问令牌"""

    if provider == "github":
        # GitHub 不支持 OAuth 刷新令牌
        raise HTTPException(status_code=400, detail="GitHub 不支持令牌刷新")
    elif provider == "google":
        try:
            new_tokens = await google_client.refresh_token(refresh_token)
            return {"access_token": new_tokens["access_token"]}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
```

### 令牌撤销

用户登出时撤销令牌：

```python
@app.post("/auth/revoke")
async def revoke_token(access_token: str, provider: str):
    """撤销访问令牌"""

    if provider == "google":
        try:
            await google_client.revoke_token(access_token)
            return {"message": "令牌撤销成功"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        raise HTTPException(status_code=400, detail="该提供商不支持令牌撤销")
```

## 错误处理

库提供了全面的错误处理：

```python
from fastapi_oauth20.errors import (
    OAuth20AuthorizeCallbackError,
    AccessTokenError,
    GetUserInfoError
)


@app.exception_handler(OAuth20AuthorizeCallbackError)
async def oauth_callback_error_handler(request: Request, exc: OAuth20AuthorizeCallbackError):
    """处理 OAuth 回调错误"""
    return {
        "error": "OAuth 授权失败",
        "detail": exc.detail,
        "status_code": exc.status_code
    }


@app.exception_handler(AccessTokenError)
async def access_token_error_handler(request: Request, exc: AccessTokenError):
    """处理访问令牌错误"""
    return {
        "error": "访问令牌交换失败",
        "detail": exc.msg
    }
```

## 完整示例

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi_oauth20 import GitHubOAuth20, FastAPIOAuth20
from fastapi_oauth20.errors import OAuth20AuthorizeCallbackError
import secrets

app = FastAPI()

# 初始化客户端
github_client = GitHubOAuth20(
    client_id="your_client_id",
    client_secret="your_client_secret"
)

# 创建依赖
github_oauth = FastAPIOAuth20(
    client=github_client,
    redirect_uri="http://localhost:8000/auth/github/callback"
)


@app.get("/auth/github")
async def github_auth():
    """GitHub 授权入口"""
    state = secrets.token_urlsafe(32)
    auth_url = await github_client.get_authorization_url(
        redirect_uri="http://localhost:8000/auth/github/callback",
        state=state
    )
    return RedirectResponse(url=auth_url)


@app.get("/auth/github/callback")
async def github_callback(
        oauth_result: tuple = Depends(github_oauth)
):
    """GitHub 授权回调"""
    token_data, state = oauth_result
    user_info = await github_client.get_userinfo(token_data["access_token"])
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
