# C compiler
CC = gcc
CC_FLAGS = -fopenmp -O3 -lm


gen_bin:  nn.c nn_gold_check.c 
	$(CC)  $(CC_FLAGS) nn.c -o nn
	$(CC)  $(CC_FLAGS)  nn_gold_check.c -DLOGS -o nn_gold_check
 
clean:
	rm -f *.o *~ nn nn_gold_check
