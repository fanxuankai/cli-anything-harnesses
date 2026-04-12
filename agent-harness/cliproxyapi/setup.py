from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-cliproxyapi",
    version="1.0.0",
    description="CLI harness for CLIProxyAPI - proxy server with OpenAI/Gemini/Claude/Codex compatible APIs",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    python_requires=">=3.9",
    install_requires=[
        "click>=8.0",
        "requests>=2.28",
        "rich>=13.0",
        "PyYAML>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "cli-anything-cliproxyapi=cli_anything.cliproxyapi.cliproxyapi_cli:main",
        ],
    },
)
