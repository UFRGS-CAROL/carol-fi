CC = gcc -g
CC_FLAGS = -fopenmp

destDir = /tmp/lavamd

all: gen_bin gen_data mv_bin

gen_bin: main_gen.c main.c main.h
	$(CC) main_gen.c kernel/kernel_cpu.c -lm $(CC_FLAGS) -o lavamd_gen
	$(CC) main.c kernel/kernel_cpu.c -lm $(CC_FLAGS) -o lavamd

gen_data: gen_bin
	./lavamd_gen 4 12
	./lavamd 4 12 input_distance_4_12 input_charges_4_12 output_4_12

mv_bin: gen_data
	mkdir -p $(destDir)
	mv lavamd_gen lavamd input_distance_4_12 input_charges_4_12 output_4_12 output_gold_4_12 $(destDir)
	@echo "All Done, executables should be in the $(destDir)"


