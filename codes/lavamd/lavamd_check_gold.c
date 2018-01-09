#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <time.h>
#include <sys/time.h>
#include <string.h>
#include <math.h>


#define fp double

#define NUMBER_PAR_PER_BOX 100							// keep this low to allow more blocks that share shared memory to run concurrently, code does not work for larger than 110, more speedup can be achieved with larger number and no shared memory used

#define NUMBER_THREADS 128								// this should be roughly equal to NUMBER_PAR_PER_BOX for best performance

#define DOT(A,B) ((A.x)*(B.x)+(A.y)*(B.y)+(A.z)*(B.z))	// STABLE

typedef struct
{
    fp x, y, z;

} THREE_VECTOR;

typedef struct
{
    fp v, x, y, z;

} FOUR_VECTOR;

typedef struct nei_str
{

    // neighbor box
    int x, y, z;
    int number;
    long offset;

} nei_str;

typedef struct box_str
{

    // home box
    int x, y, z;
    int number;
    long offset;

    // neighbor boxes
    int nn;
    nei_str nei[26];

} box_str;

typedef struct par_str
{

    fp alpha;

} par_str;

typedef struct dim_str
{

    // input arguments
    int cur_arg;
    int arch_arg;
    int cores_arg;
    int boxes1d_arg;

    // system memory
    long number_boxes;
    long box_mem;
    long space_elem;
    long space_mem;
    long space_mem2;

} dim_str;


void usage()
{
    printf("Usage: lavamd <# cores> <# boxes 1d> <output_file> <gold_file>\n");
    printf("  # cores is the number of threads that OpenMP will create\n");
    printf("  # boxes 1d is the input size, 15 is reasonable\n");
}



int main( int argc, char *argv [])
{

    char * input_file;
    char * output_gold;

    int i, j, k, l, m, n;

    par_str par_cpu;
    dim_str dim_cpu;
    box_str* box_cpu;
    FOUR_VECTOR* rv_cpu;
    fp* qv_cpu;
    FOUR_VECTOR* fv_cpu;
    FOUR_VECTOR* fv_cpu_GOLD;
    int nh;

    dim_cpu.cores_arg = 1;
    dim_cpu.boxes1d_arg = 1;

    if(argc == 5) {
        dim_cpu.cores_arg  = atoi(argv[1]);
        dim_cpu.boxes1d_arg = atoi(argv[2]);
        input_file = argv[3];
        output_gold = argv[4];
    } else {
        usage();
        exit(1);
    }



    par_cpu.alpha = 0.5;

    dim_cpu.number_boxes = dim_cpu.boxes1d_arg * dim_cpu.boxes1d_arg * dim_cpu.boxes1d_arg;

    dim_cpu.space_elem = dim_cpu.number_boxes * NUMBER_PAR_PER_BOX;
    dim_cpu.space_mem = dim_cpu.space_elem * sizeof(FOUR_VECTOR);
    dim_cpu.space_mem2 = dim_cpu.space_elem * sizeof(fp);

    dim_cpu.box_mem = dim_cpu.number_boxes * sizeof(box_str);


    FILE *file, *fileG;


    fv_cpu = (FOUR_VECTOR*)malloc(dim_cpu.space_mem);
    fv_cpu_GOLD = (FOUR_VECTOR*)malloc(dim_cpu.space_mem);
    if( (file = fopen(input_file, "rb" )) == 0 ) {
        printf( "The file 'input_file' was not opened\n" );
        exit(1);
    }
    if( (fileG = fopen(output_gold, "rb" )) == 0 ) {
        printf( "The file 'output_gold' was not opened\n" );
        exit(1);
    }
    for(i=0; i<dim_cpu.space_elem; i=i+1) {
        fread(&(fv_cpu[i].v), 1, sizeof(double), file);
        fread(&(fv_cpu[i].x), 1, sizeof(double), file);
        fread(&(fv_cpu[i].y), 1, sizeof(double), file);
        fread(&(fv_cpu[i].z), 1, sizeof(double), file);

        fread(&(fv_cpu_GOLD[i].v), 1, sizeof(double), fileG);
        fread(&(fv_cpu_GOLD[i].x), 1, sizeof(double), fileG);
        fread(&(fv_cpu_GOLD[i].y), 1, sizeof(double), fileG);
        fread(&(fv_cpu_GOLD[i].z), 1, sizeof(double), fileG);
    }

    fclose(file);
    fclose(fileG);

    printf("#HEADER box:%d spaceElem:%ld cores:%d\n", dim_cpu.boxes1d_arg,dim_cpu.space_elem,dim_cpu.cores_arg);

        int part_error=0;
        #pragma omp parallel for  reduction(+:part_error)
        for(i=0; i<dim_cpu.space_elem; i++) {
            int thread_error=0;
            if ((fabs((fv_cpu[i].v - fv_cpu_GOLD[i].v) / fv_cpu[i].v) > 0.0000000001) || (fabs((fv_cpu[i].v - fv_cpu_GOLD[i].v) / fv_cpu_GOLD[i].v) > 0.0000000001)) {
                thread_error++;
            }
            if ((fabs((fv_cpu[i].x - fv_cpu_GOLD[i].x) / fv_cpu[i].x) > 0.0000000001) || (fabs((fv_cpu[i].x - fv_cpu_GOLD[i].x) / fv_cpu_GOLD[i].x) > 0.0000000001)) {
                thread_error++;
            }
            if ((fabs((fv_cpu[i].y - fv_cpu_GOLD[i].y) / fv_cpu[i].y) > 0.0000000001) || (fabs((fv_cpu[i].y - fv_cpu_GOLD[i].y) / fv_cpu_GOLD[i].y) > 0.0000000001)) {
                thread_error++;
            }
            if ((fabs((fv_cpu[i].z - fv_cpu_GOLD[i].z) / fv_cpu[i].z) > 0.0000000001) || (fabs((fv_cpu[i].z - fv_cpu_GOLD[i].z) / fv_cpu_GOLD[i].z) > 0.0000000001)) {
                thread_error++;
            }
            if (thread_error  > 0) {
                // #pragma omp critical
                {
                    part_error++;
                    char error_detail[300];

                    snprintf(error_detail, 300, "p: [%d], ea: %d, v_r: %1.16e, v_e: %1.16e, x_r: %1.16e, x_e: %1.16e, y_r: %1.16e, y_e: %1.16e, z_r: %1.16e, z_e: %1.16e", i, thread_error, fv_cpu[i].v, fv_cpu_GOLD[i].v, fv_cpu[i].x, fv_cpu_GOLD[i].x, fv_cpu[i].y, fv_cpu_GOLD[i].y, fv_cpu[i].z, fv_cpu_GOLD[i].z);
                    printf("#ERR %s\n",error_detail);
                    thread_error = 0;
                }
            }


        }
    printf("#SDC Ite:1 KerTime:0.0 AccTime:0.0 KerErr:%d AccErr:%d\n#END",part_error, part_error);

    return 0;
}
