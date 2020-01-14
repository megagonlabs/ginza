import sys

REPLACEMENTS = {
    '    setup(':
        '''    import sys
    if sys.argv[1] == 'install':
        from importlib import import_module
        import os
        from pathlib import Path
        from io import BytesIO
        from zipfile import ZipFile
        from urllib.request import urlopen
        data_dir = str(Path(import_module('spacy').__file__).parent.parent / model_name)
        for url in [
            'https://github.com/megagonlabs/ginza/releases/download/v3.0.0/SudachiDict_core-20191224.zip',
        ]:
            resp = urlopen(url)
            with ZipFile(BytesIO(resp.read())) as zip_file:
                zip_file.extractall(data_dir)

    setup(''',
    "        package_data={model_name: list_files(model_dir)},":
        "        package_data={model_name: list_files(model_dir) + list_files(path.join(model_name, 'sudachidict'))},"
}


def main():
    with open(sys.argv[1], 'r') as f:
        lines = [l.rstrip('\n') for l in f]
    replaced = set()
    for idx, l in enumerate(lines):
        if l in REPLACEMENTS:
            if l in replaced:
                raise Exception('pattern matched to multiple lines:\n' + l)
            replaced.add(l)
            lines[idx] = REPLACEMENTS[l]
    assert len(replaced) == len(REPLACEMENTS), '\n'.join([
        'pattern match not completed:'
    ] + list(REPLACEMENTS.keys() - replaced))
    with open(sys.argv[1], 'w') as f:
        for l in lines:
            print(l, file=f)
    print('setup.py updated successfully')


if __name__ == '__main__':
    main()
