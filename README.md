# CodeGen: _An IDL based code generator written in python_
This tool allows for source code generation from an interface definition language (IDL) file. Users can model their software interfaces in IDL and then generate resulting source code using this tool. An example use case is defining a data structure and associated serialization and deserialization code in two different programming languages. With this tool a user can define the data type in IDL and then automatically generate code in each of the target languages through the use of user-defined code generation template files. This allows the user to avoid manual development of tedious code in multiple target languages which can save substantial time as projects grow.

## Dependencies
There are several dependencies. To install them, run `pip install -r requirements.txt` from the root of this repo. In addition to the `python3` dependencies, this project requires a C-preprocessor to preprocess IDL files.


## Interface Definition Language (IDL)
IDL is a common schema used to define inter-process communications. It is not a language itself, but is instead meant to be parsed and passed to a code generation utility to produce source code from it. Syntactically, it is similar to the C programming language. You can see the full specification __[here](https://www.omg.org/spec/IDL/4.2/PDF)__. This project only supports a subset of the IDL specification that we have found to be most useful. The supported entities are listed below.


## Supported Entities
We only support a subset of the IDL specification that we have found to be most useful for generating C++ source code. The supported entities are
* Structures defined using the keyword `struct`;
* Modules or namespaces defined using the keyword `module`;
* Constants defined using the keyword `const`;
* Typedefs defined using the keyword `typedef`;
* Unions are partially supported using the keyword `union`. See notes below.
* Annotations are supported using the syntax `@<annotation>`

Additionally, we have added several features beyond the IDL specification above to maintain compatibility with RTI DDS, which is frequently used in conjunction with this tool. For example, we support the sized signed and unsigned 16, 32, and 64 bit integers (e.g. `int16` and `uint64`) in addition to the basic primitive types. We also support annotations on members and structs. Annotations can be used to indicate a struct has an optional member variable, for example. In addition, we support standard C-style include guards (`#ifndef`, `#define`, `#endif`) and macros (items that are passed to the C-preprocessor). The usage of include guards prevents multiple includes of the same file when defining IDL in a larger project and should be used similar to how they are used in the C programming language (i.e. unique on a per-file basis).

## Architecture
The code generation is split into several phases and is similar to the interface of a C compiler.
* Preprocessor phase
  * Includes are searched for and their contents pasted into the primary file
  * Preprocessor directives and macros expanded
* Parsing and Lexing phases
  * We use antlr 4 to define the IDL grammar and parse and lex the input files. This results in a series of tokens
* Intermediate Representation
  * We collapse the Antlr4 output into a compact Json representation
* Construction of a parse tree
  * The python parse tree is a tree-like structure of python objects representing the parsed contents and convenient for passing to a template engine
* Name Resolution
  * All referenced symbols are resolved using the defined IDL and any included IDL files
* Code generation
  * The fully-resolved parse tree is passed to a template engine. Template engines are common in web development, among other areas, and allow for user-defined code generation. We use the Mako template engine

## Usage
You will need to define a set of code generation templates using Mako and invoke the generator. See `run_examples.sh` for more details on how to invoke the generator on the IDL in the `examples/` folder.
