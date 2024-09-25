#!/bin/bash

function gen_examples() {( set -e
    if [ -d tmp_output/ ] ; then rm -rf tmp_output ; fi
    mkdir -p tmp_output
    local cmd="python3 src/gen.py"
    local args="--json "         # produce json debugging output
    args+="--replace "           # replace any existing files w/ the same name (be careful)
    args+="--copy-idl "          # copy the idl used to the output folder (might be useful for other tools like rtiddsgen)
    args+="-Iexamples/idl/ "     # include path to search
    args+="-Iexamples/idl/sub/ " # include path to search
    args+="-o tmp_output/ "      # output folder
    args+="-p example_package "  # package name
    args+="--types-path examples/"

    local template_dir=examples/templates/   # location of code generation templates you want to use
    local pkg_name="examples"                # name of the message package
    local pkg_spec="examples/pkg_spec.json"  # the package spec file

    # invoke generator per file just like c compiler
    $cmd ${args} -d ${template_dir} -s ${pkg_spec} -p ${pkg_name} examples/idl/simple.idl
    $cmd ${args} -d ${template_dir} -s ${pkg_spec} -p ${pkg_name} examples/idl/sample.idl
    $cmd ${args} -d ${template_dir} -s ${pkg_spec} -p ${pkg_name} examples/idl/sample4.idl
    $cmd ${args} -d ${template_dir} -s ${pkg_spec} -p ${pkg_name} examples/idl/sample5.idl
    $cmd ${args} -d ${template_dir} -s ${pkg_spec} -p ${pkg_name} examples/idl/sample5.idl
    $cmd ${args} -d ${template_dir} -s ${pkg_spec} -p ${pkg_name} examples/idl/sub/sample2.idl
    $cmd ${args} -d ${template_dir} -s ${pkg_spec} -p ${pkg_name} examples/idl/sub/sample3.idl
)}
gen_examples $@
