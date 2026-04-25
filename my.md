## 发布

### Hermes 通知

GitHub Actions 会拆成两个 Hermes 通知：

- `.github/workflows/notify-hermes.yml`：`skills/**` 变更推送到 `main` 后通知 Hermes 更新 skills。
- `.github/workflows/notify-hermes-pypi.yml`：`Publish PyPI` 成功后，读取发布 workflow 记录的实际发布包，等待这些包的新版本能查到，再通知 Hermes 更新 CLI。

GitHub 仓库 Secrets：

```text
HERMES_WEBHOOK_URL=https://...
HERMES_WEBHOOK_SECRET=你的 webhook secret
```

如果暂时还用旧的 `HERMES_WEBHOOK_TOKEN`，workflow 会把它作为 HMAC secret 回退使用。

请求会带 `X-GitHub-Event`、`X-GitHub-Delivery` 和 `X-Hub-Signature-256`。skills 通知会带 `changed_files`、`skills` 和 `run_url`；PyPI 通知会带 `packages`、`cli`、`workflow_run_url` 和 `run_url`。

### GitHub Actions

PyPI 自动发布走 `.github/workflows/publish-pypi.yml`。

- 推送到 `main` 且 `agent-harness/ms/setup.py` 或 `agent-harness/cliproxyapi/setup.py` 变化时触发
- 读取 `setup.py` 的 `version`，PyPI 上没有该版本才发布
- GitHub 仓库 Secrets 需要配置：
  - `TWINE_USERNAME=__token__`
  - `TWINE_PASSWORD=pypi-xxx`

### 手动发布

```shell
cd agent-harness/ms
rm -rf build dist ./*.egg-info(N)
uvx --from build pyproject-build
uvx twine check dist/*
uvx twine upload dist/*
```

## 安装 cli

```shell
pip install cli-anything-ms
```

## 卸载 cli

```shell
pipx uninstall cli-anything-ms
# 或者
python3 -m pipx uninstall cli-anything-ms
```
