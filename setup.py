from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="intelligent-file-search",
    version="1.0.0",
    author="Prabhu",
    description="A cross-platform intelligent file system indexer and search application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/intelligent-file-search",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Desktop Environment :: File Managers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "sentence-transformers>=2.2.2",
        "numpy>=1.24.3",
        "torch>=2.0.1",
        "transformers>=4.30.2",
    ],
    entry_points={
        "console_scripts": [
            "file-search=main:main",
        ],
    },
    include_package_data=True,
)
