CXX=g++
NVCC=/usr/local/cuda/bin/nvcc
LOGS?=1
USE_OMP?=1
SAFE_MALLOC?=0

ARCH=  -gencode arch=compute_35,code=[sm_35,compute_35] # K40
ARCH+= -gencode arch=compute_53,code=[sm_53,compute_53] # Tegra X1
ARCH+= -gencode arch=compute_60,code=[sm_60,compute_60] # Tesla P100
ARCH+= -gencode arch=compute_61,code=[sm_61,compute_61] # Titan X | Titan Xp
ARCH+= -gencode arch=compute_62,code=[sm_62,compute_62] # Tegra X2 
ARCH+= -gencode arch=compute_70,code=[sm_70,compute_70] # Titan V | Tesla V100


NVCC_FLAGS= $(ARCH) -O3  -lcublas -std=c++11  -Xptxas -v
INCLUDE= -I/usr/local/cuda/include #/ -I/usr/local/cuda/samples/common/inc/
LIBRARY= -L/usr/local/cuda/lib64/
CXXFLAGS= -I/usr/local/cuda/include -L/usr/local/cuda/lib64/ -lcudart  -std=c++11

NVIDIA_INC=/usr/local/cuda/include/,./
NVIDIA_LIB=/usr/local/cuda/lib64/
LOGHELPER_INC=../include/
LOGHELPER_LIB=../include/

ifeq ($(LOGS), 1)
INCLUDE+= -I$(LOGHELPER_INC)
NVCC_FLAGS+= -DLOGS -lLogHelper 
LIBRARY+= -L$(LOGHELPER_LIB) 
CXXFLAGS+= -I$(LOGHELPER_INC) -L$(LOGHELPER_LIB) -DLOGS -lLogHelper 
endif

ifeq ($(USE_OMP), 1)
NVCC_FLAGS+= -DUSE_OMP -Xcompiler " -fopenmp -O3"
endif

ifeq ($(SAFE_MALLOC), 1)
NVCC_FLAGS+= -DSAFE_MALLOC -lSafeMemory
endif

RUN_SOURCES=./slava.cu
RUN_EXEC=./slava

DEF_SIZE=12

DEF_CHARGES_INPUT=./slava_charges_$(DEF_SIZE)
DEF_DISTANCES_INPUT=./slava_distances_$(DEF_SIZE)
DEF_GOLD=./slava_gold_$(DEF_SIZE)

SAFEMEMORYDIR=../dgemm
NVCC_FLAGS+= -I$(SAFEMEMORYDIR)/
NVCC_FLAGS+= -I$(SAFEMEMORYDIR)/
INPUTS_NAMES=$(DEF_CHARGES_INPUT) $(DEF_DISTANCES_INPUT) $(DEF_GOLD) ./slava_charges_* ./slava_distances_* ./slava_gold_*

ALL: $(RUN_EXEC)

$(RUN_EXEC): $(RUN_SOURCES)
	$(NVCC) $(NVCC_FLAGS) $(INCLUDE) $(LIBRARY) $(RUN_SOURCES) -o $(RUN_EXEC)

$(GEN_EXEC): $(GEN_SOURCES)
	$(NVCC) $(INCLUDE) $(LIBRARY) $(NVCC_FLAGS) $(GEN_SOURCES) -o $(GEN_EXEC)
	

clean:
	rm -f $(RUN_EXEC) $(INPUTS_NAMES) *.o

generate: $(RUN_EXEC)
	$(RUN_EXEC) -boxes=$(DEF_SIZE) -generate -streams=1 -iterations=1 -verbose -input_distances=$(DEF_DISTANCES_INPUT) -input_charges=$(DEF_CHARGES_INPUT) -output_gold=$(DEF_GOLD)

test: $(RUN_EXEC) generate
	$(RUN_EXEC) -boxes=$(DEF_SIZE) -streams=1 -iterations=10 -verbose -input_distances=$(DEF_DISTANCES_INPUT) -input_charges=$(DEF_CHARGES_INPUT) -output_gold=$(DEF_GOLD)
