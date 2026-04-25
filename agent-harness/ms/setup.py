from setuptools import find_namespace_packages, setup


setup(
    name="cli-anything-ms",
    version="0.6.0",
    description="CLI harness for ms backend",
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
            "cli-anything-ms=cli_anything.ms.ms_cli:main",
        ],
    },
)
