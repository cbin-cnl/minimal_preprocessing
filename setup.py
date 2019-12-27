from setuptools import setup

setup(
    name="MinimalPreprocessing",
    version="0.0.1",
    packages=["minimal_preprocessing"],
    entry_points={"console_scripts": ["preprocess_peer = minimal_preprocessing.run_minimal_preprocessing:main"]},
)
