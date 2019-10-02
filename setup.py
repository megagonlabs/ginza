from setuptools import setup, find_packages

setup(
    author="Megagon Labs, Tokyo.",
    author_email="ginza@megagon.ai",
    description="GiNZA, An Open Source Japanese NLP Library, based on Universal Dependencies",
    entry_points={
        "spacy_factories": ["JapaneseCorrector = ginza:JapaneseCorrector"],
        "spacy_languages": ["ja = ginza:Japanese"],
        "console_scripts": ["ginza = ginza.command_line:main"],
    },
    install_requires=[
        "spacy>=2.1.8",
        "SudachiPy>=0.4.0 ; python_version >= '3.5'",
        "SudachiDict_core @ https://github.com/megagonlabs/ginza/releases/download/v2.1.1/SudachiDict_core-20190927.tar.gz ; python_version >= '3.5'",
        "ja_ginza @ https://github.com/megagonlabs/ginza/releases/download/v2.1.1/ja_ginza-2.1.1.tar.gz",
    ],
    license="MIT",
    name="ginza",
    packages=find_packages(include=["ginza"]),
    url="https://github.com/megagonlabs/ginza",
    version="2.1.1",
)
