# carol-fi_cuda is not working, use carol-fi_cuda-parallel instead 

CAROL-FI CUDA is an cuda-gdb based fault injector. 
CAROL-FI GDB Fault Injector should work on any recent machine with cuda-gdb.

# Requeriments

- NVIDIA GPU, tested with Kepler, Maxwell, Pascal, and Volta architectures 
- CUDA GDB (installed with CUDA drivers)
- Python 2.7
- Libpython2.7 sudo apt install libpython2.7


# How to run a simple test

To test simple_add run the make into the simple_add folder '/codes/simple_add'.

<ol>
<li>First step is the profiler</li>

```{r, engine='bash', code_block_name} 
$ ./app_profiler.py -c codes/simple_add.conf
```
<li>McHale</li>
<li>Parish</li>
</ol>


 A folder into /tmp directory will be created with the binaries and files needed.
 
 

Then, to run the fault injector use the following command:

```{r, engine='bash', code_block_name} 
$ ./fault_injector.py -c ./codes/simple_add/simple_add.conf -i 10
```

The fault injector will run quicksort 10 times and, the logs will be stored in the *logs* folder

# How to write conf files

Available soon.
