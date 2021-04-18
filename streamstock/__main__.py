from streamstock.const import *
import streamstock
import argparse


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION,
                                     prog=PROG)
    subparsers = parser.add_subparsers(help='list of commands', dest='command')

    run_parser = subparsers.add_parser('run', help=RUN_COMMAND_HELP)

    args = parser.parse_args()

    if args.command == 'run':
        streamstock.init()


if __name__ == '__main__':
    main()
