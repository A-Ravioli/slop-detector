from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="slop-detector",
    version="0.1.0",
    author="Slop Detector Team",
    description="A codebase visualizer and code quality analyzer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/slop-detector",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.1.0",
        "networkx>=3.0",
        "esprima>=4.0.1",
        "pathspec>=0.11.0",
        "jinja2>=3.1.0",
        "colorama>=0.4.6",
        "pygments>=2.15.0",
    ],
    entry_points={
        "console_scripts": [
            "slop-detector=slop_detector.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "slop_detector": ["visualizer/templates/*.html"],
    },
)

