# C compiler
CC = gcc -g
C++ = g++
CC_FLAGS = -fopenmp -DBOFFSET=12

destDir = /tmp/sgemm

all: gen_bin gen_data mv_bin


gen_bin: sgemm.c generateMatrices.cpp
	$(CC) sgemm.c -o sgemm $(CC_FLAGS)
	$(C++) generateMatrices.cpp -o genMatrices

gen_data: gen_bin
	./genMatrices
	./sgemm 4 2048 32 sgemm_a_2048 sgemm_b_2048 gold_2048

mv_bin: gen_data
	mkdir -p $(destDir)
	mv sgemm genMatrices sgemm_a_2048 sgemm_b_2048 gold_2048 $(destDir)
	@echo "All Done, executables should be in the $(destDir)"

