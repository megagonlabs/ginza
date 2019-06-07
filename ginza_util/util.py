# encoding: utf8
from ja_ginza import Japanese


def create_model_path(output_dir, model_name, model_version):
    return output_dir / '{}_{}-{}'.format(Japanese.lang, model_name, model_version)
