# coding: utf8
import json
import sys


def copy_template(src, dst):
    for k, v in src.items():
        if k in dst:
            val = dst[k]
            if isinstance(val, dict):
                copy_template(v, val)
                continue
        dst[k] = v


def main():
    template_path = sys.argv[1]
    json_path = sys.argv[2]
    with open(template_path, 'r') as f:
        template = json.load(f)
    with open(json_path, 'r') as f:
        meta = json.load(f)

    pipeline = meta['pipeline']
    if 'JapaneseCorrector' not in pipeline:
        pipeline.append('JapaneseCorrector')
    copy_template(template, meta)

    with open(json_path, 'w') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2, sort_keys=True)


if __name__ == '__main__':
    main()
