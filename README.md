# DBASIC
A minimal programming language (and compiler), for learning to write a compiler.

## Why?
I wanted to learn how to write some rudimentary compiler. The best way to learn someting is to just do it! 

## What kind of language is it?
TinyBASIC served as a starting point, as it is such a small language and easy to implement. Over time I added new features and tweaked existing ones. Now it is some independent dialect of BASIC.

## What is it good for?
Honestly the practical use of DBASIC is somewhat limited, but I think it is great to learn about compiler design. It helped me a lot to understand the subject and I think it might be of great use for others too.
The code is super heavily commented (especially the tricky parts) and should be easy to understand.

## The language
Detailed specifications for the language can be found [here](docs/language.md).  
Here is an example for recursively calculationg and printing fibonacci numbers:
```
FUNC main() INT
    print("How many?:")
    INT dest = input()
    INT x = 0
    WHILE x < dest DO
        print("%d,",fib(x))
        x = x+1
    END
    print("\n")
    RETURN 0
END

FUNC fib(INT n) INT
    IF n < 2 THEN
        RETURN 1
    ELSE
        RETURN fib(n-1)+fib(n-2)
    END
    RETURN 0
END
```
More examples can be found in the examples folder.

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


Now compile your first programm:  
```
dbc yourfile.basic
```
This will result in an executable called "yoourfile" in the same directory.  
For additional options (outputting c/asm, input-files, output-files etc.) see ```dbc --help```

## Limitations
As the language and the compiler needed to stay quite simple there are some limitations:
- INT and BOOL are the only variable types (But calls to print() or C-functions can still use string-constants as arguments)
- Currently no stdlib
- The generated assembly-code is 100% unoptimized.
- Only linux is supported and valid compilation targets are C and x86-64 assembly

## Stability guarantees
None. 
I am still playing around with this, adding and changing features without caring for backwards compatibility.
Even significant changes to the language itself may suddenly appear.
If you need (for whatever reason) a stable version, just fork the repo.

