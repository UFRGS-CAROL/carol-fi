# Matrix multiplication sample

* To measure the memory allocation/copy time, kernel execution time, and error checking time you must build with the flag BUILD_TIMER=1. Like as follow

```bash
make BUILD_TIMER=1
make SIZE=8192 run
```

The output should be like the following:

```bash
[Matrix Multiply Using CUDA] - Starting...
GPU Device 0: "Tesla K20c" with compute capability 3.5

MatrixA(8192,8192), MatrixB(8192,8192)
Computing result using CUDA Kernel...
BEFORE START KERNEL 1.327205
KERNEL EXECUTION TIME 4.003808
Performance= 274.63 GFlop/s, Time= 4003.644 msec, Size= 1099511627776 Ops, WorkgroupSize= 1024 threads/block
Checking computed result for correctness: CMP TIME 0.166009
Result = PASS

NOTE: The CUDA Samples are not meant for performance measurements. Results may vary when GPU Boost is enabled.

```

* To build for fault injection, BUILD_TIMER must be 0

```bash
make BUILD_TIMER=0
make SIZE=8192 run
```

The output should not contain the measured timers.

```bash
./matrixMul -wA=8192 -hA=8192 -hB=8192 -wB=8192
[Matrix Multiply Using CUDA] - Starting...
GPU Device 0: "Tesla K20c" with compute capability 3.5

MatrixA(8192,8192), MatrixB(8192,8192)
Computing result using CUDA Kernel...
Checking computed result for correctness: Result = PASS

NOTE: The CUDA Samples are not meant for performance measurements. Results may vary when GPU Boost is enabled.
```