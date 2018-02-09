# C compiler
CC = gcc -g
CC_FLAGS = -fopenmp

folder="kmeans-knl-files"

all: gen_bin gen_data

gen_bin: kmeans_clustering.c cluster.c getopt.c kmeans.c kmeans_gold_check.c 
	$(CC)  $(CC_FLAGS) kmeans_clustering.c cluster.c getopt.c kmeans.c -o kmeans
	$(CC)  $(CC_FLAGS) kmeans_clustering.c cluster.c getopt.c kmeans_gold_check.c -DLOGS -o kmeans_gold_check
	g++ inpuGen/datagen.cpp -o datagen

gen_data: 
	./datagen 1000000
	./kmeans -i 1000000_34.txt -o gold1000000_34 -n 272
	mkdir -p $(folder)
	mv kmeans kmeans_gold_check datagen 1000000_34.txt gold1000000_34 $(folder)
	@echo "All Done"
	@echo "Gold and executables copy are stored in $(folder)"

