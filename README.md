# carol-fi

CAROL-FI GDB Fault Injector should work on any recent machine with gdb.


# How to run a simple test

To test quicksort run the make into the quicksort folder '/codes/quicksort'. A folder into /tmp directory will be created with the binaries and files needed.

Then, to run the fault injector use the following command:
```{r, engine='bash', code_block_name} 
$ ./fault_injector.py -c ./codes/quicksort/quicksort.conf -i 10
```

The fault injector will run quicksort 10 times and, the logs will be stored in the *logs* folder

# How to write conf files

Available soon.
