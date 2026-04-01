from setuptools import setup, find_packages

setup(
    name="resolve-media-tool",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyQt6",
        "torch",
        "torchvision",
        "basicsr",
        "realesrgan",
        "facexlib",
        "gfpgan",
        "numpy",
        "opencv-python-headless",
        "Pillow",
    ],
    entry_points={
        "console_scripts": [
            "resolve-media-tool=main:main",
        ],
    },
    python_requires=">=3.9",
)
