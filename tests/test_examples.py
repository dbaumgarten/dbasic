from dbc.cli import main
import os.path
import pytest
from itertools import product

examples = ["square", "age", "functions", "fib", "io"]
outputs = ["asm", "c", "binary"]


@pytest.mark.parametrize("example,output", product(examples, outputs))
def test_compile(example, output):
    prog = os.path.join("examples", example)
    out = prog
    if output != "binary":
        out += "." + output
    try:
        os.remove(out)
    except IOError:
        pass
    source = prog + ".basic"
    if output != "binary":
        main([source, "-t", output])
    else:
        main([source])
    assert os.path.isfile(out)
    try:
        os.remove(out)
    except IOError:
        pass
