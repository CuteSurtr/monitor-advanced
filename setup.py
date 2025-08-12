#!/usr/bin/env python3
"""
Setup script for Stock Market Monitoring System.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Stock Market Monitoring System"

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="stock-monitor",
    version="1.0.0",
    description="Advanced Stock Market Monitoring and Analytics System",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Stock Monitor Team",
    author_email="team@stockmonitor.com",
    url="https://github.com/stockmonitor/stock-monitor",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
        ],
        "desktop": [
            "psutil>=5.9.6",
            "rich>=13.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "stock-monitor=src.main:main",
            "stock-monitor-worker=src.celery_app:celery_app",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    keywords="stock market, monitoring, analytics, portfolio, trading, finance",
    project_urls={
        "Bug Reports": "https://github.com/stockmonitor/stock-monitor/issues",
        "Source": "https://github.com/stockmonitor/stock-monitor",
        "Documentation": "https://github.com/stockmonitor/stock-monitor/docs",
    },
)
