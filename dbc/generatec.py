import dbc.ast as ast

variables = dict()


def generateCode(ast):
    code = """
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
char inputbuffer[60];
int main(){
"""

    for statement in ast.statements:
        code += generateStatement(statement)
    code += "}"
    return code


def generateStatement(st):
    code = ""
    if type(st) == ast.Print:
        for exp in st.expressions:
            if type(exp) == ast.Str:
                code += "printf(\"%s\",\""+exp.value+"\");\n"
            else:
                code += "printf(\"%i\","+generateExpression(exp)+");\n"
        return code

    if type(st) == ast.Assign:
        if not st.name in variables:
            code += "int {};\n".format(st.name)
            variables[st.name] = True
        code += "{} = {};\n".format(st.name, generateExpression(st.value))
        return code

    if type(st) == ast.If:
        code += "if ({}) {{\n".format(generateExpression(st.exp))
        for statement in st.statements:
            code += generateStatement(statement)
        code += "}"
        if st.elsestatements:
            code += "else{\n"
            for statement in st.elsestatements:
                code += generateStatement(statement)
            code += "}"
        code += "\n"
        return code

    if type(st) == ast.While:
        code += "while ({}) {{\n".format(generateExpression(st.exp))
        for statement in st.statements:
            code += generateStatement(statement)
        code += "}\n"
        return code

    if type(st) == ast.Input:
        if not st.name in variables:
            code += "int {};\n".format(st.name)
            variables[st.name] = True
        code += "fgets(inputbuffer,60,stdin);if(inputbuffer[strlen(inputbuffer) - 1] == '\\n'){inputbuffer[strlen(inputbuffer) - 1] = '\\0';}\n"
        code += "{} = atoi(inputbuffer);\n".format(st.name)
        return code

    if type(st) == ast.Return:
        code += "return {};".format(generateExpression(st.expression))
        return code


def generateExpression(exp):
    if type(exp) == ast.Const:
        return str(exp.value)

    if type(exp) == ast.Str:
        return "\""+exp.value+"\""

    if type(exp) == ast.Var:
        return str(exp.name)

    if type(exp) == ast.Binary:
        return "("+generateExpression(exp.val1)+exp.op+generateExpression(exp.val2)+")"

    if type(exp) == ast.Unary:
        return "("+exp.op+generateExpression(exp.val)+")"
