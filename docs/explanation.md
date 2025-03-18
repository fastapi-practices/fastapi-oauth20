!!! note

    - `开发者` 指使用JustAuth的开发者
    - `第三方` 指开发者对接的第三方客户端，比如：Google、GitHub、Gitee 等
    - `用户` 指最终服务的真实用户

- ==client_id== 客户端身份标识符（应用id），一般在申请完 `OAuth` 应用后，由第三方客户端颁发
- ==client_secret== 客户端密钥，一般在申请完 `OAuth` 应用后，由第三方客户端颁发
- ==redirect_uri== 开发者项目中真实有效的 API 地址。用户在确认第三方客户端授权（登录）后，第三方客户端会自动重定向到该地址，并携带
  code 等参数
- ==state== 用于在请求和回调之间维护状态，主要用于防止跨站请求伪造（CSRF）攻击
- ==source== 支持的第三方客户端，比如：GitHub、LinuxDo 等
- ==sid== 第三方客户端的用户 ID。以下是关于各平台的 sid 存储逻辑：

!!! warning

    建议通过 `sid` + `source` 的方式确定唯一用户，这样可以解决用户身份归属的问题。因为 单个用户ID
    在某一平台中是唯一的，但不能保证在所有平台中都是唯一的。

## 参考资料

关于 OAuth2 相关的内容、原理可以自行参阅以下资料：

- [The OAuth 2.0 Authorization Framework](https://tools.ietf.org/html/rfc6749)
- [OAuth 2.0](https://oauth.net/2/)
