def format(code):
    """ Small helper method that applies minimal formatting to given assembler code """
    newcode = ""
    for line in code.splitlines():
        stripped = line.strip()
        # indent everything that is not a label
        if not (stripped.startswith(".") or stripped.endswith(":")):
            line = "    "+line
        newcode += line + "\n"
    return newcode
