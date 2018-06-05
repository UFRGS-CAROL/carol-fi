# C compiler
CC = gcc -g
CC_FLAGS = -fopenmp

destDir = /tmp/quicksort-fulldup-threads

all: gen_bin gen_data mv_bin

gen_bin: quicksort-fulldup-threads.c generateInput.c
	$(CC) $(CC_FLAGS) quicksort-fulldup-threads.c -o quicksort-fulldup-threads
	$(CC) $(CC_FLAGS) generateInput.c -o genInput 

gen_data: gen_bin
	./genInput
	./quicksort-fulldup-threads 5000000 4 inputsort_134217728 gold_5000000 /tmp/quick-fulldup-detection.log

mv_bin: gen_data
	mkdir -p $(destDir)
	mv genInput quicksort-fulldup-threads inputsort_134217728 gold_5000000 $(destDir)
	@echo "All Done, executables should be in the $(destDir)"


