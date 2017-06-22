# C compiler
CC = gcc -g
CC_FLAGS = -fopenmp

destDir = /tmp/quicksort

all: quick_gen gen_data mv_tmp

quick_gen: quicksort.c generateInput.c
	$(CC) $(CC_FLAGS) quicksort.c -o quicksort
	$(CC) $(CC_FLAGS) generateInput.c -o genInput 

gen_data: quick_gen
	./genInput
	./quicksort 5000000 4 inputsort_134217728 gold_5000000

mv_tmp: gen_data
	mkdir -p $(destDir)
	mv genInput quicksort inputsort_134217728 gold_5000000 $(destDir)

