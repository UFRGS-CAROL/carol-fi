CC=g++
NVCC=/usr/local/cuda-8.0/bin/nvcc

ARCH= -gencode arch=compute_30,code=sm_30 \
      -gencode arch=compute_35,code=sm_35 \
      -gencode arch=compute_50,code=[sm_50,compute_50] \
      -gencode arch=compute_52,code=[sm_52,compute_52] \
      -gencode arch=compute_60,code=[sm_60,compute_60] \
#      -gencode arch=compute_62,code=[sm_62,compute_62]



NVIDIA_INC=/usr/local/cuda-8.0/include/
NVIDIA_LIB=/usr/local/cuda-8.0/lib64/
LOGHELPER_INC=../include/
LOGHELPER_LIB=../include/

ifeq ($(dbg), 1)
DEBUG = -g -G
endif


RUN_EXEC=lava
GEN_EXEC=lava_generate

MATRIX_NAMES=output_gold_* input_distances_* input_charges_*

ifeq ($(dbg), 1)
NVCC_FLAGS+= $(ARCH) -g -G
endif

NVCC_FLAGS+= $(ARCH) -I$(NVIDIA_INC) -L$(NVIDIA_LIB)

ALL: lava

lava: lava.cu
	$(NVCC) $(NVCC_FLAGS) -DLOGS lava.cu -I$(LOGHELPER_INC) -L$(LOGHELPER_LIB) -lLogHelper -Xcompiler " -fopenmp" -o lava

clean:
	rm -f lava_generate lava $(MATRIX_NAMES)

generate:
	./lava -boxes=10 -generate -output_gold=gold_10 -iterations=1 -streams=1

test:
	./lava -boxes=10 -input_distances=input_distances_double_10 -input_charges=input_charges_double_10 -output_gold=gold_10 -iterations=1 -streams=1
