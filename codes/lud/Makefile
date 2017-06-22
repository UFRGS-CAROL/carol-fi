# C compiler
CC = gcc -g
CC_FLAGS = -fopenmp -lm

destDir = /tmp/lud

all: gen_bin gen_data mv_bin

gen_bin: lud_gen.c common.c
	$(CC) common.c lud_omp.c lud_gen.c -o lud_gen  $(CC_FLAGS)
	$(CC) common.c lud_main.c lud_omp.c -o lud $(CC_FLAGS)

gen_data: gen_bin
	./lud_gen -s 4096 -n 4
	./lud -s 4096 -n 4 -i input_4096_th_4 -o gold_4096_th_4

mv_bin: gen_data
	mkdir -p $(destDir)
	mv lud lud_gen input_4096_th_4 gold_4096_th_4 $(destDir)
	@echo "All Done, executables should be in the $(destDir)"

