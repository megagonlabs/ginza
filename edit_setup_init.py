# coding: utf8
import sys
from ja_ginza import Japanese


def main():
    edit_map = {
        "        packages=[model_name],":
            "        packages = [model_name, 'spacy.lang.{}','ginza'],".format(Japanese.lang),
        "        package_data={model_name: list_files(model_dir)},":
            "        package_data={" +
            "model_name: list_files(model_dir), "
            "'spacy.lang.{0}': "
            "list_files(path.relpath('spacy/lang/{0}')) + "
            "list_files(path.relpath('spacy/lang/{0}/resources')), "
            "'sudachipy': "
            "list_files(path.relpath('sudachipy')) + "
            "list_files(path.relpath('sudachipy/dartsclone')) + "
            "list_files(path.relpath('sudachipy/dictionarylib')) + "
            "list_files(path.relpath('sudachipy/plugin')) + "
            "list_files(path.relpath('sudachipy/plugin/input_text')) + "
            "list_files(path.relpath('sudachipy/plugin/oov')) + "
            "list_files(path.relpath('sudachipy/plugin/path_rewrite'))".format(Japanese.lang) +
            "},"
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
