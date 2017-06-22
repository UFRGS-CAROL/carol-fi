# C compiler
CC = gcc -g
CC_FLAGS = -fopenmp

destDir = /tmp/mergesort

all: gen_bin gen_data mv_bin

gen_bin: mergesort.c generateInput.c
	$(CC) $(CC_FLAGS) mergesort.c -o mergesort
	$(CC) $(CC_FLAGS) generateInput.c -o genInput 

gen_data: gen_bin
	./genInput
	./mergesort 5000000 4 inputsort_134217728 gold_5000000

mv_bin: gen_data
	mkdir -p $(destDir)
	mv genInput mergesort inputsort_134217728 gold_5000000 $(destDir)
	@echo "All Done, executables should be in the $(destDir)"


