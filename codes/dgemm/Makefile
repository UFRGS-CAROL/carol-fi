# C compiler
CC = gcc -g
C++ = g++
CC_FLAGS = -fopenmp -DBOFFSET=12

destDir = /tmp/dgemm

all: gen_bin gen_data mv_bin


gen_bin: dgemm.c generateMatrices.cpp
	$(CC) dgemm.c -o dgemm $(CC_FLAGS)
	$(C++) generateMatrices.cpp -o genMatrices

gen_data: gen_bin
	./dgemm 4 2048 32 dgemm_a_8192 dgemm_b_8192 gold_2048

mv_bin: gen_data
	mkdir -p $(destDir)
	mv dgemm genMatrices dgemm_a_8192 dgemm_b_8192 gold_2048 $(destDir)
	@echo "All Done, executables should be in the $(destDir)"

