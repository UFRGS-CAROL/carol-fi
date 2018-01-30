#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>
#include <omp.h>
//#define NUM_THREAD 4
#define OPEN


FILE *fp;

//Structure to hold a node information
struct Node
{
    int starting;
    int no_of_edges;
};

void BFSGraph(int argc, char** argv);

void Usage(int argc, char**argv) {

    fprintf(stderr,"Usage: %s <num_threads> <input_file> <out file> <gold file>\n", argv[0]);

}
////////////////////////////////////////////////////////////////////////////////
// Main Program
////////////////////////////////////////////////////////////////////////////////
int main( int argc, char** argv)
{
    BFSGraph( argc, argv);
}



////////////////////////////////////////////////////////////////////////////////
//Apply BFS on a Graph using CUDA
////////////////////////////////////////////////////////////////////////////////
void BFSGraph( int argc, char** argv)
{
#ifdef TIMING
    setup_start = timing_get_time();
#endif
    int no_of_nodes = 0;
    int edge_list_size = 0;
    char *input_f, *out_f, *gold_f;
    int	 num_omp_threads, loop_iterations=1;

    if(argc!=5) {
        Usage(argc, argv);
        exit(0);
    }

    num_omp_threads = atoi(argv[1]);
    input_f = argv[2];
    out_f = argv[3];
    gold_f = argv[4];

    printf("#HEADER filename:%s threads:%d\n", input_f, num_omp_threads);


    //Read in Graph from a file
    fp = fopen(input_f,"r");
    if(!fp)
    {
        printf("Error Reading graph file\n");
        return;
    }
    int source = 0;
    fscanf(fp,"%d",&no_of_nodes);


    // read gold
    int* h_cost_gold = (int*) malloc( sizeof(int)*no_of_nodes);
    FILE *fpo = fopen(gold_f,"rb");
    for(int i=0; i<no_of_nodes; i++) {
        fread(&h_cost_gold[i], sizeof(int), 1, fpo);
    }
    fclose(fpo);
    
    // allocate mem for the result on host side
    int* h_cost = (int*) malloc( sizeof(int)*no_of_nodes);
    fpo = fopen(out_f,"rb");
    for(int i=0; i<no_of_nodes; i++) {
        fread(&h_cost[i], sizeof(int), 1, fpo);
    }
    fclose(fpo);

    // check output with gold
    int errors = 0;
    char error_detail[200];
    for(int i=0; i<no_of_nodes; i++) {
        if(h_cost[i] != h_cost_gold[i]) {
            errors++;
            if(errors < 1000){
                sprintf(error_detail," p: [%d], r: %d, e: %d", i, h_cost[i], h_cost_gold[i]);
                printf("%s\n",error_detail);
            }
        }
    }
    printf("#SDC Ite:1 KerTime:0.0 AccTime:0.0 KerErr:%d AccErr:%d\n#END",errors, errors);
    // cleanup memory
    free( h_cost);
    free( h_cost_gold);

}

