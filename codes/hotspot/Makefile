# C compiler
CC = gcc -g
CC_FLAGS = -fopenmp -lm

destDir = /tmp/hotspot

all: gen_bin gen_data mv_bin

gen_bin: hotspot.c
	$(CC) $(CC_FLAGS) hotspot.c -o hotspot

gen_data: gen_bin
	./hotspot 1024 1024 1000 4 temp_1024 power_1024 gold_1024

mv_bin: gen_data
	mkdir -p $(destDir)
	mv hotspot gold_1024 $(destDir)
	cp temp_1024 power_1024 $(destDir)
	@echo "All Done, executables should be in the $(destDir)"

