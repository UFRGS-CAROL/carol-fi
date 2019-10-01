# CAROL-FI CUDA-GDB based fault injector


CAROL-FI is an open-source fault injector created with CUDA-GDB (GNU Project Debugger) and Python.
An interrupt procedure injects faults in registers as the application is executed on real hardware. It supports both Intel
and NVIDIA CUDA platforms. This branch is the CUDA version of CAROL-FI, to be executed on NVIDIA GPUs.
CAROL-FI GDB Fault Injector should work on any modern machine with CUDA-gdb.


# Cite

If you use CAROL-FI in your research please cite it:

- Original CAROL-FI paper (For Intel Xeon Phi)
```bibtex
@INPROCEEDINGS{carolfixeon,
    author = {Oliveira, Daniel and Pilla, La{\'e}rcio and DeBardeleben, 
        Nathan and Blanchard, Sean and Quinn, Heather and Koren, 
        Israel and Navaux, Philippe and Rech, Paolo},
    title = {Experimental and Analytical Study of Xeon Phi Reliability},
    booktitle = {Proceedings of the International Conference for High Performance Computing, 
                    Networking, Storage and Analysis},
    series = {SC '17},
    year = {2017},
    isbn = {978-1-4503-5114-0},
    location = {Denver, Colorado},
    pages = {28:1--28:12},
    articleno = {28},
    numpages = {12},
    url = {http://doi.acm.org/10.1145/3126908.3126960},
    doi = {10.1145/3126908.3126960},
    acmid = {3126960},
    publisher = {ACM},
    address = {New York, NY, USA},
} 
```

- CAROL-FI CUDA
```bibtex
@INPROCEEDINGS{carolficuda,
    author={F. {Fernandes dos Santos} and C. {Lunardi} 
    and D. {Oliveira} and F. {Libano} and P. {Rech}},
    booktitle={2019 IEEE International Symposium on High Performance Computer Architecture (HPCA)},
    title={Reliability Evaluation of Mixed-Precision Architectures},
    year={2019},
    pages={238-249},
    doi={10.1109/HPCA.2019.00041},
    month={Feb}
}
```

# Questions and contributions

If you have a question about the CAROL-FI CUDA branch or found a bug in the code,
 you can send me an e-mail to ffsantos@inf.ufrgs.br
 
# Requirements

- Ubuntu operating system tested with 16.04 and 18.04
- NVIDIA GPU, tested with Kepler, Maxwell, Pascal, and Volta architectures 
- CUDA GDB (installed with CUDA drivers)
- Python 2.7
- Libpython2.7 sudo apt install libpython2.7


# Getting started

CAROL-FI has two big stages: profiler and fault injection.

1. In the profiler stage, the execution time, and the golden copies of STDOUT and STDERR of the application will be extracted. They will be stored in the /tmp/ folder on the operating system.

2.  On the fault injection stage, CAROL-FI will inject faults simulating transient faults on the application. The fault_injector.py script starts a session of the GDB running the app with a 
python script (flip_value.py). In parallel a thread that sends a SIGINT to the application to interrupt it. 
On the flip_value.py script, an event will simulate the fault injection. The subsections 1 to 4 explain the parameters that must be set to make CAROL-FI works.


## 1 Configuration files

A configuration file will define the parameters that CAROL-FI will use for the fault injection. In the following subsections, the examples are related to the matrix multiplication benchmark stored in codes/matrixMul/matrixMul folder.

### 1.1 Configuration file parameters

The DEFAULT section contains the following keys:

* debug - Print additional information in the log files generated by CAROL-FI

* gdbExecName - How to run gdb, you can use the absolute path or execute a specific version of gdb. Usually, you can set the value to 'gdb'

* faultModel - Which fault model to use: 0 -> Single; 1 -> Double; 2 -> Random; 3 -> Zero; 4 -> Least Significant Bits (LSB)

* injectionSite - Where fault will be injected, only RF (Regsiter File) currently working

* maxWaitTimes - This value will be multiplied by the average program execution time to determine if the app hanged or not.

* benchmarkBinary - Where the binary file is located, generally at the same folder of the sources

* benchmarkArgs - The args of your program must be  in one line only

* csvFile - CSV output file. It will be overwritten at each injection

* goldenCheckScript - Compare script path. You should create a script to verify the gold output vs. injection output.

* seqSignals - How many SIGINT signals to send to the application, your application cannot use this signal

* initSleep - Wait time to start sending signals. Generally, wait time for memory allocation and cudaMemcpy (in seconds).

You can see an example of a DEFAULT section below:

```

[DEFAULT]

debug = False

gdbExecName = /usr/local/cuda/bin/cuda-gdb

faultModel = 0

injectionSite = RF

maxWaitTimes = 5

benchmarkBinary = /home/carol/carol-fi/codes/matrixMul/matrixMul

benchmarkArgs =  -wA=16384 -hA=16384 -hB=16384 -wB=16384

csvFile = ./fi_matrix_mul_bit.csv

goldenCheckScript = codes/matrixMul/sdc_check.sh

seqSignals = 20

initSleep = 0

```

### 1.2 SDC and DUE check script (goldenCheckScript)
To make CAROL-FI able to compare the outputs of your benchmark, you have to create a shell script that compares the output files within the files generated in the profile process. 
The following environment variables will be available at the moment of the execution of the shell script. The environment variables are previously set in the common_parameters.py. I strongly suggest using the default parameters.

* GOLD_OUTPUT_PATH - The Gold file that contains the golden stdout output from the profiler process;

* INJ_OUTPUT_PATH - The injection file that contains the current injection stdout output;

* GOLD_ERR_PATH - The Gold file that contains the golden stderr output from the profiler process;

* INJ_ERR_PATH - The injection file that contains the current injection stderr output;

* DIFF_LOG - The diff output between GOLD_OUTPUT_PATH and INJ_OUTPUT_PATH. 
CAROL-FI will use this file to check if the app returned SDC or not. 
It is good to keep in mind that things that vary in each execution like execution time must be removed from DIFF_LOG
 since it can lead to a false SDC;

* DIFF_ERR_LOG - The diff output between GOLD_ERR_PATH and INJ_ERR_PATH. 
CAROL-FI will use this file to check if the app returned DUE or not. 
It is good to keep in mind that things that vary in each execution like execution time must be removed from DIFF_ERR_LOG 
since it can lead to a false DUE;

### 1.3 Golden Check script example:

```{r, engine='bash', code_block_name} 
#!/usr/bin/sh
# SDC checking diff
# Must compare all things here
# Any particular output comparison must be made here
# To be considered as an SDC or CRASH the
# DIFF_LOG and DIFF_ERR_LOG files must not be empty

# INJ_OUTPUT_PATH, INJ_ERR_PATH, GOLD_OUTPUT_PATH, GOLD_ERR_PATH
# are environment variables defined by the fault_injector.py

# diff stdout
diff -B ${INJ_OUTPUT_PATH} ${GOLD_OUTPUT_PATH} > ${DIFF_LOG}

# Special comparison like the following one can be done in this script
grep -q "Result = FAIL" ${INJ_OUTPUT_PATH} >> ${DIFF_LOG}

# diff stderr
diff -B ${INJ_ERR_PATH} ${GOLD_ERR_PATH} > ${DIFF_ERR_LOG}

# Must exit 0
exit 0
```

## 2 Fault Models
Currently, we have five fault models implemented:

* (0) Single - flips only one bit from all the bits that compose the data
* (1) Double - flips two bits from all the bits that form the data
* (2) Random - replaces all the bits from the data by a random bit
* (3) Zero - replaces all the bits by zero
* (4) Least Significant Bits (LSB) - flips one bit from the first byte of the data

## 3 Injection sites
Currently, we have only RF injection site implemented:

* RF - Register File
* INST_OUT - Instruction Output (NOT IMPLEMENTED YET)
* INST_composed -> Instruction Adress (NOT IMPLEMENTED YET)


## 4 How to run matrix multiplication test

To test matrixMul run the make into the matrixMul folder 'codes/matrixMul'. See codes/matrixMul/README.md for more info.

<ol>
<li>First step is the profiler</li>

```{r, engine='bash', code_block_name} 
$ ./app_profiler.py -c codes/matrixMul/matrixmul.conf
```

</ol>


 A folder into /tmp directory will be created with the binaries and files needed.
 
 

Then, to run the fault injector use the following command:

```{r, engine='bash', code_block_name} 
$ ./fault_injector.py -c ./codes/matrixMul/matrixmul.conf -i 10
```

The fault injector will run matrix multiplication ten times and, the logs will be stored in the *logs* folder.
