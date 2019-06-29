import argparse
import fileinput
import json
import os
import sys
import time

from . import config
from . import dictionary
from . import tokenizer
from .dictionarylib.dictionarybuilder import DictionaryBuilder
from .dictionarylib.dictionaryheader import DictionaryHeader
from .dictionarylib.dictionaryversion import DictionaryVersion
from .dictionarylib.userdictionarybuilder import UserDictionaryBuilder


def run(tokenizer, mode, input, output, print_all):
    for line in input:
        line = line.rstrip('\n')
        for m in tokenizer.tokenize(mode, line):
            list_info = [
                m.surface(),
                ",".join(m.part_of_speech()),
                m.normalized_form()]
            if print_all:
                list_info += [
                    m.dictionary_form(),
                    m.reading_form(),
                    str(m.dictionary_id())]
                if m.is_oov():
                    list_info.append("(OOV)")
            print("\t".join(list_info), file=output)
        print("EOS", file=output)


def _system_dic_checker(args, print_usage):
    if not args.system_dic:
        args.system_dic = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), os.pardir, 'resources/system.dic')
    if not os.path.exists(args.system_dic):
        print_usage()
        print('{}: error: {} doesn\'t exist'.format(__name__, args.system_dic))
        exit()


def _input_files_checker(args, print_usage):
    if not args.in_files:
        print_usage()
        print('{}: error: no input files'.format(__name__))
        exit()
    for file in args.in_files:
        if not os.path.exists(file):
            print_usage()
            print('{}: error: {} doesn\'t exist'.format(__name__, file))
            exit()


def _matrix_file_checker(args, print_usage):
    if not os.path.exists(args.matrix_file):
        print_usage()
        print('{}: error: {} doesn\'t exist'.format(__name__, args.matrix_file))
        exit()


def _command_user_build(args, print_usage):
    _system_dic_checker(args, print_usage)
    _input_files_checker(args, print_usage)
    header = DictionaryHeader(
        DictionaryVersion.USER_DICT_VERSION_2, int(time.time()), args.description)
    _, _, grammar, system_lexicon = _read_system_dictionary(args.system_dic)
    with open(args.out_file, 'wb') as wf:
        wf.write(header.to_bytes())
        builder = UserDictionaryBuilder(grammar, system_lexicon)
        builder.build(args.in_files, None, wf)


def _command_build(args, print_usage):
    _matrix_file_checker(args, print_usage)
    _input_files_checker(args, print_usage)
    header = DictionaryHeader(
        DictionaryVersion.SYSTEM_DICT_VERSION, int(time.time()), args.description)
    with open(args.out_file, 'wb') as wf, open(args.matrix_file, 'r') as rf:
        wf.write(header.to_bytes())
        builder = DictionaryBuilder()
        builder.build(args.in_files, rf, wf)


def _command_tokenize(args, print_usage):

    with open(args.fpath_setting, "r", encoding="utf-8") as f:
        settings = json.load(f)

    if args.mode == "A":
        mode = tokenizer.Tokenizer.SplitMode.A
    elif args.mode == "B":
        mode = tokenizer.Tokenizer.SplitMode.B
    else:
        mode = tokenizer.Tokenizer.SplitMode.C

    output = sys.stdout
    if args.fpath_out:
        output = open(args.fpath_out, "w", encoding="utf-8")

    print_all = args.a

    is_enable_dump = args.d

    dict_ = dictionary.Dictionary(settings)
    tokenizer_obj = dict_.create()
    if is_enable_dump:
        tokenizer_obj.set_dump_output(output)

    input_ = fileinput.input(args.input_files, openhook=fileinput.hook_encoded("utf-8"))
    run(tokenizer_obj, mode, input_, output, print_all)

    output.close()


def main():
    parser = argparse.ArgumentParser(description="Japanese Morphological Analyzer")
    subparsers = parser.add_subparsers()

    # root parser
    parser.add_argument("-v", "--version", action="version", version="%(prog)s v0.1.1")

    # tokenize parser
    parser_tk = subparsers.add_parser('tokenize', help='see `tokenize -h`', description='Japanese Morphological Analyze')
    parser_tk.add_argument("-r", dest="fpath_setting", metavar="file",
                           default=config.SETTINGFILE, help="the setting file in JSON format")
    parser_tk.add_argument("-m", dest="mode", choices=["A", "B", "C"], default="C", help="the mode of splitting")
    parser_tk.add_argument("-o", dest="fpath_out", metavar="file", help="the output file")
    parser_tk.add_argument("-a", action="store_true", help="print all of the fields")
    parser_tk.add_argument("-d", action="store_true", help="print the debug information")
    parser_tk.add_argument("input_files", metavar="input file(s)", nargs=argparse.REMAINDER)
    parser_tk.set_defaults(handler=_command_tokenize, print_usage=parser_tk.print_usage)

    # build dictionary parser
    parser_bd = subparsers.add_parser('build', help='see `build -h`', description='Build Sudachi Dictionary')
    parser_bd.add_argument('-o', dest='out_file', metavar='file', default='system.dic',
                           help='output file (default: system.dic)')
    parser_bd.add_argument('-d', dest='description', default='', metavar='string', required=False,
                           help='description comment to be embedded on dictionary')
    required_named_bd = parser_bd.add_argument_group('required named arguments')
    required_named_bd.add_argument('-m', dest='matrix_file', metavar='file', required=True,
                                   help='connection matrix file with MeCab\'s matrix.def format')
    parser_bd.add_argument("in_files", metavar="file", nargs=argparse.ONE_OR_MORE,
                           help='source files with CSV format (one of more)')
    parser_bd.set_defaults(handler=_command_build, print_usage=parser_bd.print_usage)

    # build user-dictionary parser
    parser_ubd = subparsers.add_parser('ubuild', help='see `ubuild -h`', description='Build User Dictionary')
    parser_ubd.add_argument('-d', dest='description', default='', metavar='string', required=False,
                            help='description comment to be embedded on dictionary')
    parser_ubd.add_argument('-o', dest='out_file', metavar='file', default='user.dic',
                            help='output file (default: user.dic)')
    parser_ubd.add_argument('-s', dest='system_dic', metavar='file', required=False,
                            help='system dictionary (default: ${SUDACHIPY}/resouces/system.dic)')
    parser_ubd.add_argument("in_files", metavar="file", nargs=argparse.ONE_OR_MORE,
                            help='source files with CSV format (one or more)')
    parser_ubd.set_defaults(handler=_command_user_build, print_usage=parser_ubd.print_usage)

    args = parser.parse_args()

    if hasattr(args, 'handler'):
        args.handler(args, args.print_usage)
    else:
        parser.print_help()


# Todo: delete this function in the future
def _read_system_dictionary(filename):
    from .dictionarylib.dictionaryversion import DictionaryVersion
    from .dictionarylib.dictionaryheader import DictionaryHeader
    from . import dictionarylib
    """
    Copy of sudachipy.dictionary.Dictionary.read_system_dictionary
    :param filename:
    :return:
    """
    import mmap
    buffers = []
    if filename is None:
        raise AttributeError("system dictionary is not specified")
    with open(filename, 'r+b') as system_dic:
        bytes_ = mmap.mmap(system_dic.fileno(), 0, access=mmap.ACCESS_READ)
    buffers.append(bytes_)

    offset = 0
    header = DictionaryHeader.from_bytes(bytes_, offset)
    if header.version != DictionaryVersion.SYSTEM_DICT_VERSION:
        raise Exception("invalid system dictionary")
    offset += header.storage_size()

    grammar = dictionarylib.grammar.Grammar(bytes_, offset)
    offset += grammar.get_storage_size()

    lexicon = dictionarylib.lexiconset.LexiconSet(dictionarylib.doublearraylexicon.DoubleArrayLexicon(bytes_, offset))
    return buffers, header, grammar, lexicon


if __name__ == '__main__':
    main()
