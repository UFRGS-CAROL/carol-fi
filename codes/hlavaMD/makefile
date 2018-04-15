CC=g++
NVCC=/usr/local/cuda/bin/nvcc

ARCH= -gencode arch=compute_53,code=[sm_53,compute_53] \
      -gencode arch=compute_60,code=[sm_60,compute_60] \
      -gencode arch=compute_62,code=[sm_62,compute_62]


NVCC_FLAGS= $(ARCH) -Xptxas -v #-arch=sm_35

LOGHELPER_INC=../include/,./
LOGHELPER_LIB=../include/
NVIDIA_INC=/usr/local/cuda/include/
NVIDIA_LIB=/usr/local/cuda/lib64/

RUN_EXEC=hlava
GEN_EXEC=hlava_generate

ifeq ($(dbg), 1)
DEBUG = -g -G
endif



MATRIX_NAMES=output_gold_* input_distances_* input_charges_*

ALL: hlava

hlava: hlava.cu
	$(NVCC) $(NVCC_FLAGS) -DLOGS hlava.cu -I$(LOGHELPER_INC) -I$(NVIDIA_INC) -L$(LOGHELPER_LIB) -L$(NVIDIA_LIB) -lLogHelper $(DEBUG) -Xcompiler " -fopenmp" -o hlava

clean:
	rm -f hlava_generate hlava $(MATRIX_NAMES)

generate:
	./hlava -boxes=10 -generate -output_gold=gold_10 -iterations=1 -streams=1

test:
	./hlava -boxes=10 -input_distances=input_distances_half_10 -input_charges=input_charges_half_10 -output_gold=gold_10 -iterations=1 -streams=1
