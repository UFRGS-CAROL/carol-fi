#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include <unistd.h>
#include <omp.h>



void qsort_parallel(unsigned *a,int l,int r) {
    if(r>l) {

        int pivot=a[r],tmp;
        int less=l-1,more;
        for(more=l; more<=r; more++) {
            if(a[more]<=pivot) {
                less++;
                tmp=a[less];
                a[less]=a[more];
                a[more]=tmp;
            }
        }
        #pragma omp task
        qsort_parallel(a, l,less-1);
        #pragma omp task
        qsort_parallel(a, less+1,r);
        #pragma omp taskwait
    }
}

void readFileUnsigned(unsigned *input, char *filename, int size) {
    FILE *finput;
    if (finput = fopen(filename, "rb")) {
        fread(input, size * sizeof(unsigned), 1, finput);
    } else {
        printf("Error reading input file");
        exit(1);
    }
}

unsigned * quick_wrapper(int size, char * inputFile) {

    unsigned *data = (unsigned *)malloc(size*sizeof(unsigned));

    readFileUnsigned(data, inputFile, size);

    #pragma omp parallel
    #pragma omp single
    qsort_parallel(data, 0,size-1);

    return data;
}

void save_output(int size, unsigned *data, char * outputFile) {

    FILE *fp;
    if (fp = fopen(outputFile, "wb")) {
        fwrite(data, size * sizeof(unsigned), 1, fp);
    } else {
        printf("Error writing output file");
        exit(1);
    }
    fclose(fp);
}

void compare_output(int size, unsigned *data1, unsigned *data2, char *detectLog) {
    int i;
    FILE *fp;
    for(i=0; i<size; i++) {
        if(data1[i] != data2[i]) {
            if (fp = fopen(detectLog, "a")) {
                fprintf(fp, "[%d]: %u %u\n",i,data1[i],data2[i]);
                fclose(fp);
            }

        }
    }
}

int main(int argc, char** argv)
{
    int size, omp_num_threads, iterations;
    char * inputFile, *outputFile, *detectLog;
    unsigned *data1, *data2;

    if (argc == 6) {
        size = atoi(argv[1]);
        omp_num_threads = atoi(argv[2]);
        inputFile = argv[3];
        outputFile = argv[4];
        detectLog = argv[5];
    } else {
        fprintf(stderr, "Usage: %s <input size> <num_threads> <input file> <output file> <detectLog>\n", argv[0]);
        exit(1);
    }

    omp_set_num_threads(omp_num_threads);

    // Execute quicksort and save the result at data1
    data1 = quick_wrapper(size, inputFile);
    // Execute quicksort and save the result at data2
    data2 = quick_wrapper(size, inputFile);

    // Compare outputs to check for SDCs
    compare_output(size, data1, data2, detectLog);

    // Save one of the outputs to disk
    save_output(size, data1, outputFile);

    free(data1);
    free(data2);
    printf("Done\n");

    return 0;
}
