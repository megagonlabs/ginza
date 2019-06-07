# coding: utf8
import sys


def main():
    edit_map = {
        "    requirements = [parent_package + meta['spacy_version']]":
            '    requirements = [parent_package + "==" + ('
            "meta['spacy_version'][2:] if meta['spacy_version'].startswith('>=') else meta['spacy_version'])]",
        "        packages=[model_name],":
            "        packages = [model_name, "
            "'ginza', "
            "'sudachipy', "
            "'sudachipy.dartsclone', "
            "'sudachipy.dictionarylib', "
            "'sudachipy.plugin', "
            "'sudachipy.plugin.input_text', "
            "'sudachipy.plugin.oov', "
            "'sudachipy.plugin.path_rewrite'"
            "],",
        "        package_data={model_name: list_files(model_dir)},":
            "        package_data={" +
            "model_name: list_files(model_dir), "
            "'ginza': "
            "list_files(path.relpath('ginza')) + "
            "list_files(path.relpath('ginza/resources')),"
            "'sudachipy': "
            "list_files(path.relpath('sudachipy')) + "
            "list_files(path.relpath('sudachipy/dartsclone')) + "
            "list_files(path.relpath('sudachipy/dictionarylib')) + "
            "list_files(path.relpath('sudachipy/plugin')) + "
            "list_files(path.relpath('sudachipy/plugin/input_text')) + "
            "list_files(path.relpath('sudachipy/plugin/oov')) + "
            "list_files(path.relpath('sudachipy/plugin/path_rewrite'))"
            "},\n"
            "        entry_points={"
            '"spacy_factories": ["JapaneseCorrector = ginza:JapaneseCorrector"],'
            '"spacy_languages": ["ja = ginza:Japanese"],'
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
