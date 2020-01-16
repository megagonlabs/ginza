from importlib import import_module
import os
from pathlib import Path
from setuptools import setup
import sys
import tarfile

PACKAGE_NAME = "ja_ginza_dict"

dict_package = import_module(PACKAGE_NAME)
dict_dir = Path(dict_package.__file__).parent / 'sudachidict'
xz_path = dict_dir / 'system.dic.tar.xz'
if xz_path.exists() and sys.argv[1] != 'sdist':
    print('extracting', xz_path)
    with tarfile.open(str(xz_path), 'r:xz') as xz:
        xz.extractall(str(dict_dir))
    print('extracted', dict_dir / 'system.dic')
    os.remove(str(xz_path))
    print('deleted', xz_path)

setup(
    author="Megagon Labs, Tokyo.",
    author_email="ginza@megagon.ai",
    description="SudachiDict for ja_ginza (SudachiDict is originally developed by Works Applications Tokushima Laboratory of AI and NLP)",
    license="MIT",
    name=PACKAGE_NAME,
    packages=[PACKAGE_NAME],
    package_data={PACKAGE_NAME: ['sudachidict/*']},
    url="https://github.com/megagonlabs/ginza",
    version='3.1.0',
)
