#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include <sys/time.h>
#include <unistd.h>

#define BLOCK_SIZE 16
#define BLOCK_SIZE_C BLOCK_SIZE
#define BLOCK_SIZE_R BLOCK_SIZE

#define STR_SIZE	256

/* maximum power density possible (say 300W for a 10mm x 10mm chip)	*/
#define MAX_PD	(3.0e6)
/* required precision in degrees	*/
#define PRECISION	0.001
#define SPEC_HEAT_SI 1.75e6
#define K_SI 100
/* capacitance fitting factor	*/
#define FACTOR_CHIP	0.5
#define OPEN
//#define NUM_THREAD 4


typedef float FLOAT;

/* chip parameters	*/
const FLOAT t_chip = 0.0005;
const FLOAT chip_height = 0.016;
const FLOAT chip_width = 0.016;

/* ambient temperature, assuming no package at all	*/
const FLOAT amb_temp = 80.0;

int num_omp_threads;

void fatal(char *s)
{
    fprintf(stderr, "error: %s\n", s);
    exit(1);
}

void read_input(FLOAT *vect, int grid_rows, int grid_cols, char *file)
{
    int i, index;
    FILE *fp;
    char str[STR_SIZE];
    FLOAT val;

    fp = fopen (file, "r");
    if (!fp)
        fatal ("file could not be opened for reading");

    for (i=0; i < grid_rows * grid_cols; i++) {
        if (fgets(str, STR_SIZE, fp) == NULL) {
            fatal("fgets error");
        }
        if (feof(fp))
            fatal("not enough lines in file");
        if ((sscanf(str, "%f", &val) != 1) )
            fatal("invalid file format");
        vect[i] = val;
    }

    fclose(fp);
}

void usage(int argc, char **argv)
{
    fprintf(stderr, "Usage: %s <grid_rows> <grid_cols> <sim_time> <no. of threads> <output_file> <gold_file>\n", argv[0]);
    fprintf(stderr, "\t<grid_rows>  - number of rows in the grid (positive integer)\n");
    fprintf(stderr, "\t<grid_cols>  - number of columns in the grid (positive integer)\n");
    fprintf(stderr, "\t<sim_time>   - number of iterations\n");
    fprintf(stderr, "\t<no. of threads>   - number of threads\n");
    //fprintf(stderr, "\t<temp_file>  - name of the file containing the initial temperature values of each cell\n");
    //fprintf(stderr, "\t<power_file> - name of the file containing the dissipated power values of each cell\n");
    fprintf(stderr, "\t<output_file> - name of the output file\n");
    fprintf(stderr, "\t<gold_file> - name of the output file with gold results\n");
    exit(1);
}

int main(int argc, char **argv)
{
    int grid_rows, grid_cols, sim_time, i;
    FLOAT *result, *final_result, *gold;
    char *tfile, *pfile, *ofile;
    int tot_iterations = 1;

    /* check validity of inputs	*/
    if (argc != 7)
        usage(argc, argv);
    if ((grid_rows = atoi(argv[1])) <= 0 ||
            (grid_cols = atoi(argv[2])) <= 0 ||
            (sim_time = atoi(argv[3])) <= 0 ||
            (num_omp_threads = atoi(argv[4])) <= 0
       )
        usage(argc, argv);

    omp_set_num_threads(num_omp_threads);

    /* allocate memory for the temperature and power arrays	*/
    result = (FLOAT *) calloc (grid_rows * grid_cols, sizeof(FLOAT));
    gold = (FLOAT *) calloc (grid_rows * grid_cols, sizeof(FLOAT));
    if(!result || !gold)
        fatal("unable to allocate memory");

    printf("#HEADER simIter:%d gridSize:%dx%d\n",sim_time, grid_rows, grid_cols);

    /* read initial temperatures and input power	*/
    tfile = argv[5];
    ofile = argv[6];

    read_input(result, grid_rows, grid_cols, tfile);
    read_input(gold, grid_rows, grid_cols, ofile);


    final_result = result;
    int errors=0;
    for (i=0; i < grid_rows; i++) {
        int j;
        for (j=0; j < grid_cols; j++) {
            if ((fabs((final_result[i*grid_cols+j] - gold[i*grid_cols+j]) / final_result[i*grid_cols+j]) > 0.0000000001) || (fabs((final_result[i*grid_cols+j] - gold[i*grid_cols+j]) / gold[i*grid_cols+j]) > 0.0000000001)) {
                errors++;
                char error_detail[150];
                snprintf(error_detail, 150, "r:%f e:%f [%d,%d]", final_result[i*grid_cols+j], gold[i*grid_cols+j], i, j);
                printf("#ERR %s\n",error_detail);
            }
        }
    }
    printf("#SDC Ite:1 KerTime:0.0 AccTime:0.0 KerErr:%d AccErr:%d\n#END",errors, errors);

    return 0;
}

