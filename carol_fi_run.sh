#!/usr/bin/env bash


        os.environ['GDB_EXE'] = self.__gdb_exe_name
        os.environ['GDB_CAROLFI_FLAGS'] = '-n -batch -x'
        os.environ['PYTHON_SCRIPT'] = self.__flip_script
$GDB_EXE $GDB_CAROLFI_FLAGS $PYTHON_SCRIPT > out.txt 2> err.txt

