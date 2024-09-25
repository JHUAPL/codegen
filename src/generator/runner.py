#!/usr/bin/python3

import argparse
import json
import idl_parser as idl


def main():
    parser = argparse.ArgumentParser(
        description='Program to dump the IR from an idl file.')
    parser.add_argument(
        'sources',
        type=str,
        nargs='+',
        help='Source file to process (single file)')
    parser.add_argument(
        '-I', '--include-dir',
        action='append',
        required=False,
        help='-I<dir> Add the directory dir to the head of the list of '
        'directories to be searched for xml files')
    args = parser.parse_args()

    processor = idl.IdlProcessor(args.include_dir)

    for src in args.sources:
        tree = processor.processFile(src)
        print(json.dumps(tree.asdict(), indent=4))


if __name__ == '__main__':
    main()
