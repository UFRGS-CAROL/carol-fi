
OMP_NUM_THREADS = 272

all: euler3d_cpu euler3d_cpu_double pre_euler3d_cpu pre_euler3d_cpu_double 

euler3d_cpu: euler3d_cpu.cpp
	g++ -O3 -Dblock_length=$(OMP_NUM_THREADS) -fopenmp euler3d_cpu.cpp -o euler3d_cpu


euler3d_cpu_double: euler3d_cpu_double.cpp
	g++ -O3 -Dblock_length=$(OMP_NUM_THREADS) -fopenmp euler3d_cpu_double.cpp -o euler3d_cpu_double


pre_euler3d_cpu: pre_euler3d_cpu.cpp
	g++ -O3 -Dblock_length=$(OMP_NUM_THREADS) -fopenmp pre_euler3d_cpu.cpp -o pre_euler3d_cpu

pre_euler3d_cpu_double: pre_euler3d_cpu_double.cpp
	g++ -O3 -Dblock_length=$(OMP_NUM_THREADS) -fopenmp pre_euler3d_cpu_double.cpp -o pre_euler3d_cpu_double


clean:
#	rm -f euler3d
	rm -f euler3d_cpu
	rm -f euler3d_cpu_offload
#	rm -f euler3d_double
	rm -f euler3d_cpu_double

#	rm -f pre_euler3d
	rm -f pre_euler3d_cpu
#	rm -f pre_euler3d_double
	rm -f pre_euler3d_cpu_double
