## 发布

### Hermes 通知

GitHub Actions 会在 `skills/**` 变更推送到 `main` 后运行 `.github/workflows/notify-hermes.yml`。

GitHub 仓库 Secrets：

```text
HERMES_WEBHOOK_URL=https://...
HERMES_WEBHOOK_TOKEN=可选
```

payload 会带 `repository`、`ref`、`sha`、`changed_files`、`skills` 和 `run_url`。

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
