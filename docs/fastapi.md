提供的实用程序可简化 FastAPI 中 OAuth2 流程的集成

## `FastAPIOAuth20`

依赖关系可调用，用于处理授权回调，它读取查询参数并返回访问令牌和状态

```python
from fastapi import FastAPI, Depends
from fastapi_oauth20 import FastAPIOAuth20, LinuxDoOAuth20

client = LinuxDoOAuth20("CLIENT_ID", "CLIENT_SECRET")
linuxdo_oauth2_callback = FastAPIOAuth20(client, "oauth2-callback")

app = FastAPI()


@app.get("/oauth2-callback", name="oauth-callback")
async def oauth2_callback(access_token_state=Depends(linuxdo_oauth2_callback)):
    token, state = access_token_state
    # Do something useful
```

## 自定义异常

如果回调逻辑内部发生错误（用户拒绝访问、授权代码无效......），依赖关系将引发 `OAuth20AuthorizeCallbackError` 错误

它继承自 FastAPI 的 [HTTPException](https://fastapi.tiangolo.com/reference/exceptions/#fastapi.HTTPException)，因此默认的
FastAPI 异常处理程序会自动对其进行处理。您可以通过为 `OAuth20AuthorizeCallbackError` 实现自己的异常处理程序来自定义此行为

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi_oauth20.integrations.fastapi import OAuth20AuthorizeCallbackError

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
