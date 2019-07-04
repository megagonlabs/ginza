# coding: utf8
import sys


def main():
    edit_map = {
        "        install_requires=list_requirements(meta),":
            "        install_requires=list_requirements(meta) + "
            "['SudachiPy @ https://github.com/megagonlabs/SudachiPy/releases/download/v0.1.3-dict/SudachiPy-0.1.3.tar.gz'],"
            "        entry_points={"
            '"spacy_factories": ["JapaneseCorrector = spacy.lang.ja:JapaneseCorrector"],'
            "},",
    }
    setup_path = sys.argv[1]
    with open(setup_path, 'r') as f:
        lines = f.readlines()
    with open(setup_path, 'w') as f:
        for line in lines:
            line = line.rstrip()
            if line in edit_map:
                line = edit_map.pop(line)
            print(line, file=f)
    if len(edit_map) > 0:
        print('Following lines are not replaced on {}'.format(setup_path), file=sys.stderr)
        for key in edit_map.keys():
            print(key, file=sys.stderr)
        raise Exception('Edit failed')


if __name__ == '__main__':
    main()
