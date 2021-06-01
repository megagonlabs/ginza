from setuptools import setup, find_packages


setup(
    author="Megagon Labs, Tokyo.",
    author_email="ginza@megagon.ai",
    description="GiNZA, An Open Source Japanese NLP Library, based on Universal Dependencies",
    entry_points={
        "spacy_factories": [
            "BunsetuRecognizer = ginza:BunsetuRecognizer",
            "CompoundSplitter = ginza:CompoundSplitter",
        ],
        "console_scripts": [
            "ginza = ginza.command_line:main_ginza",
            "ginzame = ginza.command_line:main_ginzame",
        ],
    },
    install_requires=[
        "spacy>=2.3.2,<3.0.0",
        "SudachiPy>=0.4.9 ; python_version >= '3.5'",
        "SudachiDict-core>=20200330 ; python_version >= '3.5'",
        "ja_ginza>=4.0.0,<4.1.0",
    ],
    license="MIT",
    name="ginza",
    packages=find_packages(include=["ginza"]),
    url="https://github.com/megagonlabs/ginza",
    version='4.0.6',
)
