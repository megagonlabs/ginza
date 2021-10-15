from setuptools import setup, find_packages


setup(
    author="Megagon Labs, Tokyo.",
    author_email="ginza@megagon.ai",
    description="GiNZA, An Open Source Japanese NLP Library, based on Universal Dependencies",
    entry_points={
        "spacy_factories": [
            "bunsetu_recognizer = ginza:make_bunsetu_recognizer",
            "compound_splitter = ginza:make_compound_splitter",
            "disable_sentencizer = ginza:disable_sentencizer",
        ],
        "console_scripts": [
            "ginza = ginza.command_line:main_ginza",
            "ginzame = ginza.command_line:main_ginzame",
        ],
    },
    install_requires=[
        "spacy>=3.0.6,<3.2.0",
        "plac>=1.3.3",
        "SudachiPy>=0.5.2,<0.6.0",
        "SudachiDict-core>=20210608",
    ],
    license="MIT",
    name="ginza",
    packages=find_packages(include=["ginza"]),
    url="https://github.com/megagonlabs/ginza",
    version='5.0.3',
)
