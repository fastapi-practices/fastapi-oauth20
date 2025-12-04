## 注册账号

地址：[feishu](https://www.feishu.cn/accounts/page/ug_register)

如果已有则忽略该步骤，直接进入第二步

## 创建第三方应用

### 登录

登录[飞书开放平台](https://open.feishu.cn/)，通过主页右上角进入个人设置页

![dev.png](../public/images/feishu/dev.png)

### 创建应用

![new.png](../public/images/feishu/new.png)

配置回调地址

![callback.png](../public/images/feishu/callback.png)

配置应用权限

![permission.png](../public/images/feishu/permission.png)

### 获取密钥

![secrets.png](../public/images/feishu/secrets.png)

记录 `Client ID`、`Client Secret`、`重定向 URL`，这三个东西在我们集成的时候都用得到，请妥善保管 `Client ID` 和
`Client Secret`
