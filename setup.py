"""
Setup script for DRMS - Documentation RAG MCP Server
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = requirements_path.read_text().strip().split('\n')
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

setup(
    name="drms",
    version="1.0.0",
    author="DRMS Team",
    author_email="team@drms.dev",
    description="Documentation RAG MCP Server for AI Coding Tools",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/drms",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Documentation",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
        ],
        "openai": [
            "openai>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "drms-server=mcp_server:main",
            "drms-api=drms_api:main",
            "drms-demo=examples.demo_search:main",
        ],
    },
    include_package_data=True,
    package_data={
        "drms": ["config/*.json", "data/*.json"],
    },
    keywords="documentation rag mcp ai coding tools vector search embeddings",
    project_urls={
        "Bug Reports": "https://github.com/your-org/drms/issues",
        "Source": "https://github.com/your-org/drms",
        "Documentation": "https://drms.readthedocs.io/",
    },
)