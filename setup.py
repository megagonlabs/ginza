from setuptools import setup, find_packages


setup(
    author="Megagon Labs, Tokyo.",
    author_email="ginza@megagon.ai",
    description="GiNZA, An Open Source Japanese NLP Library, based on Universal Dependencies",
    entry_points={
        "spacy_factories": ["JapaneseCorrector = ginza:JapaneseCorrector"],
        "spacy_languages": ["ja = ginza:Japanese"],
        "console_scripts": [
            "ginza = ginza.command_line:main_ginza",
            "ginzame = ginza.command_line:main_ginzame",
        ],
    },
    install_requires=[
        "spacy>=2.2.3",
        "SudachiPy>=0.4.2 ; python_version >= '3.5'",
        "ja_ginza<3.2.0,>=3.1.0",
    ],
    license="MIT",
    name="ginza",
    packages=find_packages(include=["ginza"]),
    url="https://github.com/megagonlabs/ginza",
    version='3.1.2',
)
