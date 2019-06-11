from setuptools import setup

setup(
    name="ginza",
    entry_points={
        "spacy_factories": [
            "JapaneseCorrector = ginza:JapaneseCorrector"
        ],
        "spacy_languages": [
            "ja = ginza:Japanese"
        ]
    }
)
