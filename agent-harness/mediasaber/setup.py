from setuptools import find_namespace_packages, setup


setup(
    name="cli-anything-mediasaber",
    version="1.0.1",
    description="CLI harness for Media Saber",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    include_package_data=True,
    package_data={
        "cli_anything.mediasaber": ["skills/SKILL.md"],
    },
    python_requires=">=3.9",
    install_requires=[
        "click>=8.0",
        "requests>=2.28",
        "PyYAML>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "cli-anything-mediasaber=cli_anything.mediasaber.mediasaber_cli:main",
        ],
    },
)
