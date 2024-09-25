#!/bin/bash

function compile_grammar() {

    if [ -d out/ ] ; then rm -rf out/ ; fi
    mkdir out
    cmd='java -jar antlr-4.9.1-complete.jar -Dlanguage=Python3 -o out/ IDL.g4'
    echo $cmd
    $cmd
}
compile_grammar $@
