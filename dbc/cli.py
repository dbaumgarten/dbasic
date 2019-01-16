""" This is the entry-point for the compiler console application. After installation it can be invoked by typing 'dbc' to the console """
import dbc.tokenize as tokenize
import dbc.parse as parse
from dbc.visit import VisitorError
from dbc.formatasm import format
import dbc.generateasm as generateasm
import dbc.generatec as generatec
from dbc.checkvariables import VariableChecker
from dbc.checktypes import TypeChecker
from dbc.errors import CheckError

import sys
import argparse
import subprocess
import os.path


def main(args=None):
    """ Main entrypoint for the DBASIC compiler CLI application 

        :params args: Optional command line arguments (mainly used for testing). If None, sys.argv is used.
    """
    # setup CLI-Arguments
    parser = argparse.ArgumentParser(description='Compile DBASIC file')
    parser.add_argument('infile', type=str, help='The file to compile')
    parser.add_argument('-o', "--outfile", type=str,
                        help="The file to write to")
    parser.add_argument('-t', "--type", type=str, default="binary",
                        help="Type of output to generate. Can be asm, c, binary. Default: binary")
    parser.add_argument('--debug', type=bool, help="Enable debugging output")
    parser.add_argument('-g', "--gccargs", type=str,
                        help="Additional args for gcc")

    args = parser.parse_args(args)

    # generate the output filename if not explicitly given
    if not args.outfile:
        if not "." in args.infile:
            print("infile needs to have a file-extension")
            sys.exit(1)
        fname, _ = os.path.splitext(args.infile)
        if args.type == "binary":
            args.outfile = fname
        else:
            args.outfile = fname + "." + args.type

    # open the source file
    with open(args.infile, "r") as f:

        # enable debug-logging if the user wants to
        if args.debug:
            parse.debug = True

        try:
            # tokenize the input
            tokenizer = tokenize.Tokenizer(f.read())
            if args.debug:
                print(tokenizer.tokens)
            # parse tokens into AST
            syntaxtree = parse.parse(tokenizer)
            # annotate the tree with variable information and check for variable-relatet semantic errors
            VariableChecker().check(syntaxtree)
            # check for type-errors
            TypeChecker().check(syntaxtree)

            # choose a code-generator based on the users wanted output-format
            if args.type == "c":
                generator = generatec.CGenerator()
            elif args.type == "asm" or args.type == "binary":
                generator = generateasm.ASMGenerator()
            else:
                print("Unknown target type")
                sys.exit(1)

            # generate code from the ast
            code = generator.generate(syntaxtree)

            # format the asm-code a little to make it more readable
            if args.type == "asm":
                code = format(code)

        except (parse.ParserError, VisitorError, CheckError) as e:
            # catch errors that may occur during parsing, checking and code-generation
            print(e)
            sys.exit(1)

        if args.type == "c" or args.type == "asm":
            # if the users does not want a binary as output we are done now. Just write the code to a file
            with open(args.outfile, "w") as of:
                of.write(code)
            return

        if args.type == "binary":
            # if the user wants a binary we use gcc to assemble and link the generated assembly-code
            cmds = ["gcc", "-o", args.outfile, "-xassembler", "-"]
            if args.gccargs:
                cmds = cmds + args.gccargs.split(" ")
            subprocess.run(cmds, input=code.encode())
