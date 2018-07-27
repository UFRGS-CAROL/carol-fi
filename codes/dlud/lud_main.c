/*
 * =====================================================================================
 *
 *       Filename:  suite.c
 *
 *    Description:  The main wrapper for the suite
 *
 *        Version:  1.0
 *        Created:  10/22/2009 08:40:34 PM
 *       Revision:  none
 *       Compiler:  gcc
 *
 *         Author:  Liang Wang (lw2aw), lw2aw@virginia.edu
 *        Company:  CS@UVa
 *
 * =====================================================================================
 */

#include <stdio.h>
#include <unistd.h>
#include <getopt.h>
#include <stdlib.h>
#include <assert.h>
#include <math.h>

#include "common.h"

static int do_verify = 0;
int omp_num_threads = 228;

static struct option long_options[] = {
  /* name, has_arg, flag, val */
  {"input", 1, NULL, 'i'},
  {"output", 1, NULL, 'o'},
  {"size", 1, NULL, 's'},
  {0,0,0,0}
};

extern void
lud_omp(double *m, int matrix_dim);

int
main ( int argc, char *argv[] )
{
  int matrix_dim = 0; /* default size */
  int opt, option_index=0;
  func_ret_t ret;
  const char *input_file = NULL;
  const char *output_file = NULL;
  double *m;
  stopwatch sw;

	
  while ((opt = getopt_long(argc, argv, "::s:n:i:o:", 
                            long_options, &option_index)) != -1 ) {
    switch(opt){
    case 'i':
      input_file = optarg;
      break;
    case 'o':
      output_file = optarg;
      break;
    case 'v':
      do_verify = 1;
      break;
    case 'n':
      omp_num_threads = atoi(optarg);
      break;
    case 's':
      matrix_dim = atoi(optarg);
      break;
    case '?':
      fprintf(stderr, "invalid option\n");
      break;
    case ':':
      fprintf(stderr, "missing argument\n");
      break;
    default:
      fprintf(stderr, "Usage: %s [-v] [-s matrix_size|-i input_file]\n",
	      argv[0]);
      exit(EXIT_FAILURE);
    }
  }
  
  if ( (optind < argc) || (optind == 1)) {
    fprintf(stderr, "Usage: %s [-n no. of threads] [-s matrix_size] [-i input_file] [-o output_file]\n", argv[0]);
    exit(EXIT_FAILURE);
  }

  if (input_file && output_file && matrix_dim>0) {
	int n = matrix_dim;
	FILE *f_a;
	f_a = fopen(input_file, "rb");

	if (f_a == NULL) {
		printf("Error opening files\n");
    		exit(EXIT_FAILURE);
	}

        m = (double*) malloc(sizeof(double)*n*n);
	fread(m, sizeof(double) * n * n, 1, f_a);
	fclose(f_a);
  }
  else {
    printf("No input, output, or matrix_dim specified!\n");
    exit(EXIT_FAILURE);
  } 

  lud_omp(m, matrix_dim);

  FILE *f_out;
  f_out = fopen(output_file, "wb");
  
  if (f_out == NULL) {
  	printf("Error opening files\n");
  	exit(EXIT_FAILURE);
  }
  
  fwrite(m, sizeof(double) * matrix_dim * matrix_dim, 1, f_out);
  fclose(f_out);
  
  free(m);

  return EXIT_SUCCESS;
}				/* ----------  end of function main  ---------- */
