CC = gcc -g
CC_FLAGS = -fopenmp

destDir = /tmp/slavamd

all: gen_bin gen_data mv_bin

gen_bin: main_gen.c main.c main.h
	$(CC) main_gen.c kernel/kernel_cpu.c -lm $(CC_FLAGS) -o slavamd_gen
	$(CC) main.c kernel/kernel_cpu.c -lm $(CC_FLAGS) -o slavamd

gen_data: gen_bin
	./slavamd_gen 4 12
	./slavamd 4 12 input_distance_4_12 input_charges_4_12 output_4_12

mv_bin: gen_data
	mkdir -p $(destDir)
	mv slavamd_gen slavamd input_distance_4_12 input_charges_4_12 output_4_12 output_gold_4_12 $(destDir)
	@echo "All Done, executables should be in the $(destDir)"


