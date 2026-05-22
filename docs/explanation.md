# 名词解释

OAuth2 的流程可以理解为：用户去第三方平台确认授权，第三方平台再把用户带回你的应用，并附带一个可换取令牌的 `code`。

## 角色

- **开发者**：使用本库接入第三方登录的人
- **第三方平台**：GitHub、Google、Gitee、飞书、微信等 OAuth2 服务方
- **用户**：在你的应用中点击“第三方登录”的真实用户

## 常见字段

| 字段 | 含义 |
| --- | --- |
| `client_id` | 第三方平台颁发的应用 ID |
| `client_secret` | 第三方平台颁发的应用密钥，请勿暴露到前端 |
| `redirect_uri` | 用户授权后跳回你应用的回调地址，必须和平台后台配置一致 |
| `state` | 防止 CSRF 的随机字符串，建议每次登录都生成并校验 |
| `code` | 第三方平台回调时带回的临时代码，用来换取访问令牌 |
| `access_token` | 访问第三方用户信息接口的令牌 |
| `refresh_token` | 用来刷新 `access_token` 的令牌，不是所有平台都支持 |
| `source` | 第三方平台标识，例如 `github`、`google` |
| `sid` | 用户在第三方平台中的 ID |

!!! tip

    建议用 `source + sid` 作为第三方用户的唯一标识。单个平台内的用户 ID 通常唯一，但不同平台之间可能重复。

## 参考资料

- [The OAuth 2.0 Authorization Framework](https://tools.ietf.org/html/rfc6749)
- [OAuth 2.0](https://oauth.net/2/)
