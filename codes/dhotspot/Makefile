# C compiler
CC = gcc -g
CC_FLAGS = -fopenmp -lm

destDir = /tmp/dhotspot

all: gen_bin gen_data mv_bin

gen_bin: dhotspot.c
	$(CC) $(CC_FLAGS) dhotspot.c -o dhotspot

gen_data: gen_bin
	./dhotspot 1024 1024 1000 4 temp_1024 power_1024 gold_1024

mv_bin: gen_data
	mkdir -p $(destDir)
	mv dhotspot gold_1024 $(destDir)
	cp temp_1024 power_1024 $(destDir)
	@echo "All Done, executables should be in the $(destDir)"

