# C compiler
CC = g++
CC_FLAGS = -fopenmp -O3 -fpermissive

folder="bfs-knl-files"

all: gen_bin gen_data

gen_bin: bfs.cpp bfs_gold_check.cpp
	$(CC) $(CC_FLAGS) bfs.cpp -o bfs
	$(CC) $(CC_FLAGS) bfs_gold_check.cpp -o bfs_gold_check
	$(CC) -std=c++0x -fopenmp graphgen.cpp -o graphgen 

gen_data: gen_bin
	./graphgen 4194304
	./bfs 272 graph4194304.txt gold4194304
	mkdir -p $(folder)
	mv bfs bfs_gold_check graphgen graph4194304.txt gold4194304 $(folder)
	@echo "All Done"
	@echo "Gold and executables copy are stored in $(folder)"

clean:
	rm -f bfs_gold_check bfs graphgen

