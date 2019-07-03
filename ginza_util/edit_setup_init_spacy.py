# coding: utf8
import sys


def main():
    edit_map = {
        "    requirements = [parent_package + meta['spacy_version']]":
            '    requirements = [parent_package + "==" + ('
            "meta['spacy_version'][2:] if meta['spacy_version'].startswith('>=') else meta['spacy_version'])]",
        "        packages=[model_name],":
            "        packages = [model_name, "
            "'sudachidict', "
            "],",
        "        package_data={model_name: list_files(model_dir)},":
            "        package_data={" +
            "model_name: list_files(model_dir), "
            "'sudachidict': "
            "list_files(path.relpath('sudachidict')) + "
            "list_files(path.relpath('sudachidict/resources')),"
            "},\n"
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
