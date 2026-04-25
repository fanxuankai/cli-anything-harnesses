## 发布

### GitHub Actions

PyPI 自动发布走 `.github/workflows/publish-pypi.yml`。

- 手动触发 `Publish PyPI`，选择 `all`、`ms` 或 `cliproxyapi`
- 发布 GitHub Release 时自动尝试发布两个包
- PyPI 需要配置 Trusted Publishing：
  - Owner: `fanxuankai`
  - Repository: `cli-anything-harnesses`
  - Workflow: `publish-pypi.yml`
  - Environment: `pypi`

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
