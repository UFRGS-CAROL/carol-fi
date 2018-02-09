# C compiler
CC = gcc -g
CC_FLAGS = -fopenmp

folder="nn-knl-files"

path=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

all: gen_bin gen_data

gen_bin:  nn.c nn_gold_check.c 
	$(CC)  $(CC_FLAGS) nn.c -lm -o nn
	$(CC)  $(CC_FLAGS)  nn_gold_check.c -DLOGS -o nn_gold_check
	$(CC)  data/hurricane_gen.c -o hurricane_gen
 
gen_data: gen_bin
	./hurricane_gen 1368320 4
	mkdir -p $(folder)
	mv data/cane* $(folder)
	echo "$(path)/$(folder)/cane4_0.db" > filelist
	echo "$(path)/$(folder)/cane4_1.db" >> filelist
	echo "$(path)/$(folder)/cane4_2.db" >> filelist
	echo "$(path)/$(folder)/cane4_3.db" >> filelist
	./nn filelist 20 5 5 gold20_5_5
	mv ./hurricane_gen nn_gold_check nn gold20_5_5 filelist $(folder)
	@echo "All Done"
	@echo "Gold and executables copy are stored in $(folder)"

