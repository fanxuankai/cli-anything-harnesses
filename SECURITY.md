# Security Policy

## 报告安全问题

请不要在公开 issue 中提交 token、cookie、管理密钥、服务地址或完整日志。

如果发现安全问题，请通过 GitHub 私有安全报告入口提交：

<https://github.com/fanxuankai/cli-anything-harnesses/security/advisories/new>

## 敏感信息

提交 issue 或 PR 前，请检查并移除：

- API key、management key、token、cookie
- 内网地址、私有域名、真实用户数据
- 带有认证头的请求日志
- 本地配置文件内容

## 支持范围

当前仓库主要维护：

- `cli-anything-ms`
- `cli-anything-cliproxyapi`
- `skills/*`
