#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <assert.h>
#include <unistd.h>
#include <omp.h>
#include <time.h>

#ifndef MAXTHREADS
#define MAX_THREADS 1024
#else
#define MAX_THREADS MAXTHREADS
#endif

#ifndef BOFFSET
#define BOFFSET 12
#endif

#define AA_arr(i,j) AA[(i)+(block+BOFFSET)*(j)]
#define BB_arr(i,j) BB[(i)+(block+BOFFSET)*(j)]
#define CC_arr(i,j) CC[(i)+(block+BOFFSET)*(j)]
#define  A_arr(i,j)  A[(i)+(order)*(j)]
#define  B_arr(i,j)  B[(i)+(order)*(j)]
#define  C_arr(i,j)  C[(i)+(order)*(j)]

#define forder (1.0*order)

#ifndef MIN
#define MIN(x,y) ((x)<(y)?(x):(y))
#endif
#ifndef MAX
#define MAX(x,y) ((x)>(y)?(x):(y))
#endif
#ifndef ABS
#define ABS(a) ((a) >= 0 ? (a) : -(a))
#endif


static inline void prk_free(void* p)
{
#if defined(__INTEL_COMPILER) && !defined(PRK_USE_POSIX_MEMALIGN)
    _mm_free(p);
#else
    free(p);
#endif
}

/* This function is separate from prk_malloc() because
 * we need it when calling prk_shmem_align(..)           */
static inline int prk_get_alignment(void)
{
    /* a := alignment */
# ifdef PRK_ALIGNMENT
    int a = PRK_ALIGNMENT;
# else
    char* temp = getenv("PRK_ALIGNMENT");
    int a = (temp!=NULL) ? atoi(temp) : 64;
    if (a < 8) a = 8;
    assert( (a & (~a+1)) == a );
#endif
    return a;
}

/* There are a variety of reasons why this function is not declared by stdlib.h. */
#if defined(__UPC__)
int posix_memalign(void **memptr, size_t alignment, size_t size);
#endif

static inline void* prk_malloc(size_t bytes)
{
#ifndef PRK_USE_MALLOC
    int alignment = prk_get_alignment();
#endif

    /* Berkeley UPC throws warnings related to this function for no obvious reason... */
#if !defined(__UPC__) && defined(__INTEL_COMPILER) && !defined(PRK_USE_POSIX_MEMALIGN)
    return (void*)_mm_malloc(bytes,alignment);
#elif defined(PRK_HAS_C11)
    /* From ISO C11:
     *
     * "The aligned_alloc function allocates space for an object
     *  whose alignment is specified by alignment, whose size is
     *  specified by size, and whose value is indeterminate.
     *  The value of alignment shall be a valid alignment supported
     *  by the implementation and the value of size shall be an
     *  integral multiple of alignment."
     *
     *  Thus, if we do not round up the bytes to be a multiple
     *  of the alignment, we violate ISO C.
     */
    size_t padded = bytes;
    size_t excess = bytes % alignment;
    if (excess>0) padded += (alignment - excess);
    return aligned_alloc(alignment,padded);
#elif defined(PRK_USE_MALLOC)
#warning PRK_USE_MALLOC prevents the use of alignmed memory.
    return prk_malloc(bytes);
#else /* if defined(PRK_USE_POSIX_MEMALIGN) */
    void * ptr = NULL;
    int ret;
    ret = posix_memalign(&ptr,alignment,bytes);
    if (ret) ptr = NULL;
    return ptr;
#endif
}


void read_matrix(double *M,char * fileM, long int order) {
    FILE *file;
    int i, j;

    if( (file = fopen(fileM, "rb" )) == 0 ) {
        printf( "The gold file was not opened\n" );
        exit(1);
    }

    for(j = 0; j < order; j++) for(i = 0; i < order; i++) {
            fread(&M[(i)+(order)*(j)], 1, sizeof(double), file);
        }
    fclose(file);
}

int main(int argc, char **argv) {


    int     i, j;
    int     nthread_input;        /* thread parameters                              */
    static
    double  *A, *B, *C, *gold;  /* input (A,B) and output (C) matrices            */
    long    order;                /* number of rows and columns of matrices         */
    int     block;                /* tile size of matrices                          */
    char *inputC, *fileGold;
    int iterations = 100000;

    printf("OpenMP Dense matrix-matrix multiplication\n");

    if (argc != 6) {
        printf("Usage: %s <# threads> <matrix order> <tile size> <matrix result C> <GOLD>\n",*argv);
        exit(1);
    }

    /* Take number of threads to request from command line                          */
    nthread_input = atoi(*++argv);

    if ((nthread_input < 1) || (nthread_input > MAX_THREADS)) {
        printf("ERROR: Invalid number of threads: %d\n", nthread_input);
        exit(1);
    }

    omp_set_num_threads(nthread_input);

    order = atol(*++argv);
    if (order < 0) {
        order    = -order;
    }
    if (order < 1) {
        printf("ERROR: Matrix order must be positive: %ld\n", order);
        exit(1);
    }

    block = atoi(*++argv);
    inputC = *++argv;
    fileGold = *++argv;

    C = (double *) prk_malloc(order*order*sizeof(double));
    gold = (double *) prk_malloc(order*order*sizeof(double));
    if (!C || !gold) {
        printf("ERROR: Could not allocate space for global matrices\n");
        exit(1);
    }


    read_matrix(gold, fileGold, order);
    read_matrix(C, inputC, order);

    printf("#HEADER matrix_dim:%ld threads:%d block_size:%d block_offset:%d\n", order, nthread_input, block, BOFFSET);

    int errors=0;
    #pragma omp parallel for reduction(+:errors) private(i,j)
    for(j = 0; j < order; j++) for(i = 0; i < order; i++) {
            if ((fabs((C[(i)+(order)*(j)] - gold[(i)+(order)*(j)]) / C[(i)+(order)*(j)]) > 0.0000000001) || (fabs((C[(i)+(order)*(j)] - gold[(i)+(order)*(j)]) / gold[(i)+(order)*(j)]) > 0.0000000001)) {
                errors++;
                char error_detail[200];
                sprintf(error_detail," p: [%d, %d], r: %1.16e, e: %1.16e", i, j, C[i + order * j], gold[i + order * j]);
                printf("#ERR %s\n",error_detail);
            }
        }
    printf("#SDC Ite:1 KerTime:0.0 AccTime:0.0 KerErr:%d AccErr:%d\n#END",errors, errors);

    exit(0);
}

