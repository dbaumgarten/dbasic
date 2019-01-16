# DBASIC Language specification

## Design principles
- All keywords are written in UPPERCASE.
- Statements and Declarations are terminated with newlines (note with ';' like in many other languages)
- Special keywords are used the specify code-blocks (instead of {}). For example THEN and END for the blocks of IF-Statements
- Variables are statically typed and type-checking is strickt. No implicit type conversions happen.
- As the language is intended as an easy target for practicing compiler design only basic features exist.

## Programm structure
On the top-level all DBASIC programms consist of functions and global variables. All programms MUST contain a function called "main" without arguments and with return-type INT.

## Global variables
Global variables are declared using the global keyword.  
```
GLOBAL INT i = 5
```

## Functions
Functions are declared using the FUNC keyword.  
```
FUNC funcname(INT arg1, BOOL arg2) INT
//body
RETURN 0
END
```
Functions can have 0 to 6 arguments. The return type-is optional. Functions without return-type return nothing. Each function-body MUST end with a RETURN statement before the END.  

External functions (like the ones from glibc) can be called. No type-checking happens for such functions. 

Variables can not be of type string, but string-constants can be used as arguments to builtin and C functions. The following call is completely valid.
```
puts("HELLO WORLD")
```

## Builtin functions
There are some special builtin functions available.
- input() reads a number from stdin and returns it as INT
- print("format",arg0,argn) functions exactly like C's printf. The first argument is a fromat string and all following arguments fill the placeholders in the format-string.

```
FUNC main() INT
INT x = input()
print("Your entered %d\n",x)
END

```

## Control-Flow
If statements:
```
IF condition THEN
//code
ELSE
//code
END
```
The else-block is optional. The condition must be an expression of type BOOL.  
For example, if x is of type INT: ```IF x == 3 THEN``` is valid, but ```IF x THEN``` is not.

While-loops are the only supported kind of loops.
```
WHILE condition DO
//code
END
```
Like for if-statements condition must be of type BOOL.

## Variables
Variables can be of type INT (signed) or BOOL.
Variables must be declared before use. A default value MUST be assigned during declaration. The type is only specified during the inital declaration. Variable types are checked at compile time. For example trying to assign a boolean value to an INT variable will fail with a compiler error.
```
INT i = 0
INT q = i+3
i = 10
```

## Arithmetics
The following operations are defined for INTs and also return INTs:
- i+j Addition
- i-j Subtraction
- i*j Multiplication
- i/j Division
- -i  Negation
- i|j bitwise or
- i&j bitwise and  

Comparisons are defined for INTs and return BOOLs
- ==
- !=
- \>=
- <=
- \>
- \<  

Equal and not equal are also defined for BOOLs.  

Normal order of operations is honored. Also brackets can be used to clarify operation order.  
```
INT i = 1
INT j = 2
INT q = i+j*i+(2*i)
BOOL f = i==j
BOOL z = TRUE
```
Function calls to non-external functions with a return-type other then None can also be used in calculations. The special keywords TRUE and FALSE can be used to initialize BOOL variables.
