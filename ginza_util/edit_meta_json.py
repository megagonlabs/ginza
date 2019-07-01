# coding: utf8
import json
import sys


def main():
    json_path = sys.argv[1]
    with open(json_path, 'r') as f:
        meta = json.load(f)
    pipeline = meta['pipeline']
    if 'JapaneseCorrector' not in pipeline:
        pipeline.append('JapaneseCorrector')
    with open(json_path, 'w') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
