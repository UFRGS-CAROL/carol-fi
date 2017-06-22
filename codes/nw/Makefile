# C compiler
CC = g++ -g
CC_FLAGS = -fopenmp

destDir = /tmp/nw

all: gen_bin gen_data mv_bin

gen_bin: needle_gen.cpp needle.cpp
	$(CC) $(CC_FLAGS) needle_gen.cpp -o needle_gen 
	$(CC) $(CC_FLAGS) needle.cpp -o needle

gen_data: gen_bin
	./needle_gen 16384 10 4
	./needle 16384 10 4 input_16384_th_4_pen_10 gold_16384_th_4_pen_10

mv_bin: gen_data
	mkdir -p $(destDir)
	mv needle_gen needle input_16384_th_4_pen_10 gold_16384_th_4_pen_10 $(destDir)
	@echo "All Done, executables should be in the $(destDir)"
