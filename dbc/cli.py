#!/usr/bin/python3

import dbc.tokenize as tokenize
import dbc.parse as parse
import dbc.generateasm as generateasm
import dbc.generatec as generatec

import sys
import argparse
import subprocess
import os.path


def main():

    parser = argparse.ArgumentParser(description='Compile DBASIC file')
    parser.add_argument('infile', type=str, help='The file to compile')
    parser.add_argument('-o', "--outfile", type=str,
                        help="The file to write to")
    parser.add_argument('-t', "--type", type=str, default="binary",
                        help="Type of output to generate. Can be asm, c, binary. Default: binary")
    parser.add_argument('--debug', type=bool, help="Enable debugging output")
    parser.add_argument('-g', "--gccargs", type=str,
                        help="Additional args for gcc")

    args = parser.parse_args()

    if not args.outfile:
        if not "." in args.infile:
            print("infile needs to have a file-extension")
            sys.exit(1)
        fname, _ = os.path.splitext(args.infile)
        if args.type == "binary":
            args.outfile = fname
        else:
            args.outfile = fname + "." + args.type

    with open(args.infile, "r") as f:

        if args.debug:
            parse.debug = True

        t = tokenize.Tokenizer(f.read())
        t.newtokenize()
        try:
            tree = parse.parse(t)
        except parse.ParserError as e:
            print(e)
            sys.exit(1)

        if args.type == "c":
            result = generatec.generateCode(tree)
        if args.type == "asm" or args.type == "binary":
            result = generateasm.generateCode(tree)
        if args.type == "c" or args.type == "asm":
            with open(args.outfile, "w") as of:
                of.write(result)
            return

        if args.type == "binary":
            cmds = ["gcc", "-o", args.outfile, "-xassembler", "-"]
            if args.gccargs:
                cmds = cmds + args.gccargs.split(" ")
            subprocess.run(cmds, input=result.encode())


main()
