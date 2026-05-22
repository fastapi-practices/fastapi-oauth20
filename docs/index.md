# FastAPI OAuth 2.0

`fastapi-oauth20` 是一个面向 FastAPI 的异步 OAuth2 客户端库，用来完成第三方登录、授权回调、令牌刷新和用户信息获取。

## 适合谁

- 想在 FastAPI 项目中接入 GitHub、Google、Gitee、飞书、微信等第三方登录
- 希望用异步方式完成 OAuth2 请求
- 希望把授权回调写成 FastAPI 依赖，少写重复代码

## 快速安装

=== "pip"

    ```bash
    pip install fastapi-oauth20
    ```

=== "uv"

    ```bash
    uv add fastapi-oauth20
    ```

## 最小示例

下面示例创建 GitHub 客户端，并生成用户登录地址：

```python
from fastapi_oauth20 import GitHubOAuth20

github_client = GitHubOAuth20(
    client_id="your_github_client_id",
    client_secret="your_github_client_secret",
)


async def build_login_url() -> str:
    return await github_client.get_authorization_url(
        redirect_uri="http://localhost:8000/auth/github/callback",
        state="random_state",
    )
```

## 下一步

- [安装](install.md)：确认环境和安装命令
- [用法](usage.md)：查看完整 FastAPI 登录流程
- [名词解释](explanation.md)：了解 `client_id`、`redirect_uri`、`state` 等概念
- [客户端状态](status.md)：查看当前支持的第三方平台
