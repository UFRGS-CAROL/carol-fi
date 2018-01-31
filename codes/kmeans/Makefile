# C compiler
CC = gcc
CC_FLAGS = -fopenmp -O3

gen_bin: kmeans_clustering.c cluster.c getopt.c kmeans.c kmeans_gold_check.c 
	$(CC)  $(CC_FLAGS) kmeans_clustering.c cluster.c getopt.c kmeans.c -o kmeans
	$(CC)  $(CC_FLAGS) kmeans_clustering.c cluster.c getopt.c kmeans_gold_check.c -DLOGS -o kmeans_gold_check
 
clean:
	rm -f *.o *~ kmeans kmeans_gold_check
