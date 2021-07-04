from setuptools import setup, find_packages


setup(
    author="Megagon Labs, Tokyo.",
    author_email="ginza@megagon.ai",
    description="GiNZA, An Open Source Japanese NLP Library, based on Universal Dependencies",
    entry_points={
        "spacy_factories": [
            "bunsetu_recognizer = ginza:make_bunsetu_recognizer",
            "compound_splitter = ginza:make_compound_splitter",
        ],
        "console_scripts": [
            "ginza = ginza.command_line:main_ginza",
            "ginzame = ginza.command_line:main_ginzame",
        ],
    },
    install_requires=[
        "spacy>=3.0.6,<3.1.0",
        "SudachiPy>=0.5.2",
        "SudachiDict-core>=20210608",
        "ja_ginza>=5.0.0,<5.1.0",
    ],
    license="MIT",
    name="ginza",
    packages=find_packages(include=["ginza"]),
    url="https://github.com/megagonlabs/ginza",
    version='5.0.0-alpha',
)
