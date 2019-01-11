# DBASIC
A minimal programming language (and compiler), for learning to write a compiler.

## Why?
I wanted to learn how to write some rudimentary compiler. The best way to learn someting is to just do it! 

## What kind of language is it?
TinyBASIC served as a starting point, as it is such a small language and easy to implement. Over time I added new features and tweaked existing ones. Now it is some independent dialect of BASIC.

## What is it good for?
Honestly the practical use of DBASIC is somewhat limited, but I think it is great to learn about compiler design. It helped me a lot to understand the subject and I think it might be of great use for others too.

## How to use it?
First you need to install the compiler:  
```
pip3 install git+https://github.com/dbaumgarten/dbasic.git
```  

You can also install it in development mode so you can easily modify the compiler. 

```
git clone https://github.com/dbaumgarten/dbasic.git
pip install -e dbasic
```  

You will also need to have GCC installed as it is used to assemble and link the generated assembly code.


Have a look at the examples in the examples directory. They show the usage of tha langage features. A detailed language specification might follow.

Now compile your first programm:  
```
dbc yourfile.basic
```
This will result in an executable called "yoourfile" in the same directory.  
For additional options (outputting c/asm, input-files, output-files etc.) see ```dbc --help```

## Limitations
As the language and the compiler needed to stay quite simple there are some limitations:
- No global variables
- All variables are of type signed int (but the PRINT command can still output string constants)
- Currently no stdlib
- The generated assembly-code is 100% unoptimized.
- Only linux is supported and valid compilation targets are C and x86-64 assembly

