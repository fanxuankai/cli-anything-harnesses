## 发布

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