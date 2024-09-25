#!/usr/bin/python3


import argparse
from generator import genmain


def main():

    parser = argparse.ArgumentParser(
        description='Program to generate code from an idl file.')
    parser.add_argument(
        'sources',
        type=str,
        nargs='+',
        help='Source idls to process (single file, list, or glob pattern)')
    parser.add_argument(
        '-t', '--template-name',
        action='append',
        help='Template to process')
    parser.add_argument(
        '-d', '--template-dir',
        action='append',
        help='Directory to recursively search for templates all *.mako '
        'templates in dir will be processed)')
    parser.add_argument(
        '-o', '--output-root',
        type=str,
        required=True,
        help='Root directory to place all output. Output will be placed at '
        '<output_root>/<pkg_name>')
    parser.add_argument(
        '-p', '--pkg-name',
        type=str,
        required=True,
        help='Package name for generated code')
    parser.add_argument(
        '-I', '--include-dir',
        action='append',
        required=False,
        help='-I<dir> Add the directory dir to the head of the list of '
        'directories to be searched for included idl files')
    parser.add_argument(
        '-s', '--pkg-spec',
        type=str,
        required=True,
        help='-D<pkg_spec.json> The path and name of the pkg_spec.json '
        'file for this package')
    parser.add_argument(
        '--json',
        default=False,
        action='store_true',
        help='Dump json representation of parsed file to json '
        'output file')
    parser.add_argument(
        '--replace',
        default=False,
        action='store_true',
        help='Overwrite any existing output files')
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        default=False,
        help='Enable verbose parsing')
    parser.add_argument(
        '-c', '--copy-idl',
        action='store_true',
        default=False,
        help='Copy idl to subdirectory of odir for later processing')
    parser.add_argument(
        '--types-path',
        type=str,
        required=True,
        help="--types-path<path> The path to project_types.py")
    parser.add_argument(
        '--ns_prefix',
        type=str,
        default='internal',
        help='Namespace prefix for generated messages'
    )
    args = parser.parse_args()
    genmain(args)


if __name__ == '__main__':
    main()
