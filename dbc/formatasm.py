def format(code):
    newcode = ""
    for line in code.splitlines():
        stripped = line.strip()
        if not (stripped.startswith(".") or stripped.endswith(":")):
            line = "    "+line
        newcode += line + "\n"
    return newcode
