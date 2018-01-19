#define LIMIT -999
//#define TRACE
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <sys/time.h>
#include <omp.h>
#include <unistd.h>


#define OPENMP

#define BLOCK_SIZE 16

////////////////////////////////////////////////////////////////////////////////
// declaration, forward
void runTest( int argc, char** argv);


void ReadArrayFromFile(int* input_itemsets, int max_rows, char * filenameinput) {
    int n = max_rows;

    FILE *f_a;
    f_a = fopen(filenameinput, "rb");

    if (f_a == NULL) {
        printf("Error opening INPUT files\n");
        exit(-3);
    }

    fread(input_itemsets, sizeof(int) * n * n, 1, f_a);
    fclose(f_a);
}

void ReadGoldFromFile(int* gold_itemsets, int max_rows, char * filenamegold) {
    int n = max_rows;

    FILE *f_gold;
    f_gold = fopen(filenamegold, "rb");

    if (f_gold == NULL) {
        printf("Error opening GOLD file\n");
        exit(-3);
    }

    fread(gold_itemsets, sizeof(int) * n * n, 1, f_gold);
    fclose(f_gold);
}


////////////////////////////////////////////////////////////////////////////////
// Program main
////////////////////////////////////////////////////////////////////////////////
int
main( int argc, char** argv)
{
    runTest( argc, argv);

    return EXIT_SUCCESS;
}

void usage(int argc, char **argv)
{
    fprintf(stderr, "Usage: %s <max_rows/max_cols> <penalty> <num_threads> <input_array> <gold_array>\n", argv[0]);
    fprintf(stderr, "\t<dimension>      - x and y dimensions\n");
    fprintf(stderr, "\t<penalty>        - penalty(positive integer)\n");
    fprintf(stderr, "\t<num_threads>    - no. of threads\n");
    exit(1);
}


void
runTest( int argc, char** argv)
{

    int max_rows, max_cols, penalty;
    int *input_itemsets,  *gold_itemsets;
    char * array_path, * gold_path;
    int omp_num_threads;


    // the lengths of the two sequences should be able to divided by 16.
    // And at current stage  max_rows needs to equal max_cols
    if (argc == 6)
    {
        max_rows = atoi(argv[1]);
        max_cols = atoi(argv[1]);
        penalty = atoi(argv[2]);
        omp_num_threads = atoi(argv[3]);
        array_path = argv[4];
        gold_path =  argv[5];
    }
    else {
        usage(argc, argv);
    }

    omp_set_num_threads(omp_num_threads);

    printf("#HEADER max_rows:%d max_cols:%d penalty:%d omp_num_threads:%d\n", max_rows, max_cols, penalty, omp_num_threads);


    input_itemsets = (int *)malloc( max_rows * max_cols * sizeof(int) );
    gold_itemsets = (int *)malloc( max_rows * max_cols * sizeof(int) );


    if (!input_itemsets || !gold_itemsets)
        fprintf(stderr, "error: can not allocate memory");

    ReadArrayFromFile(input_itemsets, max_rows, array_path);
    ReadGoldFromFile(gold_itemsets, max_rows, gold_path);



#ifdef TIMING
        check_start = timing_get_time();
#endif
        int host_errors = 0;
        #pragma omp parallel for reduction(+:host_errors)
        for (int i = 0; i < max_rows; i++) {
            for (int j = 0; j < max_rows; j++) {
                if (input_itemsets[i + max_rows * j] != gold_itemsets[i + max_rows * j]) {
                    char error_detail[200];
                    sprintf(error_detail," p: [%d, %d], r: %i, e: %i", i, j, input_itemsets[i + max_rows * j], gold_itemsets[i + max_rows * j]);
                    host_errors++;
                    if(host_errors < 1000){
                        printf("#ERR %s\n",error_detail);
                    }
                }
            }
        }
    printf("#SDC Ite:1 KerTime:0.0 AccTime:0.0 KerErr:%d AccErr:%d\n#END",host_errors, host_errors);
    free(input_itemsets);

}



