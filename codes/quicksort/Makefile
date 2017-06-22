# C compiler
CC = gcc -g
CC_FLAGS = -fopenmp

destDir = /tmp/quicksort

all: gen_bin gen_data mv_bin

gen_bin: quicksort.c generateInput.c
	$(CC) $(CC_FLAGS) quicksort.c -o quicksort
	$(CC) $(CC_FLAGS) generateInput.c -o genInput 

gen_data: gen_bin
	./genInput
	./quicksort 5000000 4 inputsort_134217728 gold_5000000

mv_bin: gen_data
	mkdir -p $(destDir)
	mv genInput quicksort inputsort_134217728 gold_5000000 $(destDir)
	@echo "All Done, executables should be in the $(destDir)"


