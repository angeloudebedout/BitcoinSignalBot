from setuptools import setup, find_packages

setup(
    name="signalbot",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.39.0",
        "streamlit-autorefresh>=1.0.1",
        "plotly>=5.24.1",
        "pandas>=2.2.3",
        "numpy>=1.26.4",
        "matplotlib>=3.9.2",
        "requests>=2.32.3",
        "pycoingecko>=3.1.0",
        "openpyxl>=3.1.5",
    ],
)
