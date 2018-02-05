#include <climits>
#include <vector>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <time.h>
#include <sys/time.h>
#include <iostream>
#include <unistd.h>

#if _OPENMP
# include <omp.h>
#endif

#include "lulesh.h"


static void
read_solution(int nx, char *gold_filename, int *gold_meshConn,double *gold_coord,double *gold_e,double *gold_p,double *gold_v,double *gold_q,double *gold_speed)
{

    FILE *fout = fopen(gold_filename, "rb");
    int numElem = nx*nx*nx;
    int numNode = (nx+1)*(nx+1)*(nx+1);

    int i_int=0;
    /* Write out the mesh connectivity in fully unstructured format */
    for (int ei=0; ei < numElem; ++ei) {
        //Index_t *elemToNode = domain.nodelist(ei) ;
        for (int ni=0; ni < 8; ++ni) {
            fread(&gold_meshConn[i_int],sizeof(int),1,fout);
            i_int++;
        }
    }

    int i_d=0;
    /* Write out the mesh coordinates associated with the mesh */
    for (int ni=0; ni < numNode ; ++ni) {
        fread(&(gold_coord[i_d]),sizeof(double),1,fout);
        i_d++;
        fread(&(gold_coord[i_d]),sizeof(double),1,fout);
        i_d++;
        fread(&(gold_coord[i_d]),sizeof(double),1,fout);
        i_d++;
    }

    /* Write out pressure, energy, relvol, q */

    int i_d1=0;
    for (int ei=0; ei < numElem; ++ei) {
        fread(&(gold_e[i_d1]),sizeof(double),1,fout);
        i_d1++;
    }

    int i_d2=0;
    for (int ei=0; ei < numElem; ++ei) {
        fread(&(gold_p[i_d2]),sizeof(double),1,fout);
        i_d2++;
    }

    int i_d3=0;
    for (int ei=0; ei < numElem; ++ei) {
        fread(&(gold_v[i_d3]),sizeof(double),1,fout);
        i_d3++;
    }

    int i_d4=0;
    for (int ei=0; ei < numElem; ++ei) {
        fread(&(gold_q[i_d4]),sizeof(double),1,fout);
        i_d4++;
    }
    /* Write out nodal speed, velocities */
    int i_d5=0;
    for(int ni=0 ; ni < numNode ; ++ni) {
        fread(&(gold_speed[i_d5]),sizeof(double),1,fout);
        i_d5++;
        fread(&(gold_speed[i_d5]),sizeof(double),1,fout);
        i_d5++;
        fread(&(gold_speed[i_d5]),sizeof(double),1,fout);
        i_d5++;
    }

    fclose(fout);
}

//static void
//check_solution(Domain& domain, int *gold_meshConn,double *gold_coord,double *gold_e,double *gold_p,double *gold_v,double *gold_q,double *gold_speed)
//{
//
//   int i = 0, errors=0;
//   /* Check the mesh connectivity in fully unstructured format */
//   for (int ei=0; ei < domain.numElem(); ++ei) {
//      Index_t *elemToNode = domain.nodelist(ei);
//      for (int ni=0; ni < 8; ++ni) {
//	 if(elemToNode[ni] != gold_meshConn[i]){
//	     errors++;
//             char error_detail[200];
//             sprintf(error_detail,"(MeshConn) p: [%d], r: %u, e: %u", i, elemToNode[ni], gold_meshConn[i]);
//#ifdef LOGS
//             log_error_detail(error_detail);
//#endif
//	 }
//	 i++;
//      }
//   }
//   //printf("error conn:%d\n",errors);
//
//   /* Check the mesh coordinates associated with the mesh */
//   int i_d=0;
//   for (int ni=0; ni < domain.numNode() ; ++ni) {
//      if ((fabs((domain.x(ni) - gold_coord[i_d]) / domain.x(ni)) > 0.0000000001) || (fabs((domain.x(ni) - gold_coord[i_d]) / gold_coord[i_d]) > 0.0000000001)) {
//          errors++;
//          char error_detail[200];
//          sprintf(error_detail,"(MeshCoordinates x) p: [%d], r: %u, e: %u", ni, domain.x(ni), gold_coord[i_d]);
//#ifdef LOGS
//          log_error_detail(error_detail);
//#endif
//      }
//      i_d++;
//      if ((fabs((domain.y(ni) - gold_coord[i_d]) / domain.y(ni)) > 0.0000000001) || (fabs((domain.y(ni) - gold_coord[i_d]) / gold_coord[i_d]) > 0.0000000001)) {
//          errors++;
//          char error_detail[200];
//          sprintf(error_detail,"(MeshCoordinates y) p: [%d], r: %u, e: %u", ni, domain.y(ni), gold_coord[i_d]);
//#ifdef LOGS
//          log_error_detail(error_detail);
//#endif
//      }
//      i_d++;
//      if ((fabs((domain.z(ni) - gold_coord[i_d]) / domain.z(ni)) > 0.0000000001) || (fabs((domain.z(ni) - gold_coord[i_d]) / gold_coord[i_d]) > 0.0000000001)) {
//          errors++;
//          char error_detail[200];
//          sprintf(error_detail,"(MeshCoordinates z) p: [%d], r: %u, e: %u", ni, domain.z(ni), gold_coord[i_d]);
//#ifdef LOGS
//          log_error_detail(error_detail);
//#endif
//      }
//      i_d++;
//   }
//
//   //printf("error coord:%d\n",errors);
//   /* Write out pressure, energy, relvol, q */
//
//   for (int ei=0; ei < domain.numElem(); ++ei) {
//      int i = domain.numNode()*3 + ei;
//      if ((fabs((domain.e(ei) - gold_e[ei]) / domain.e(ei)) > 0.0000000001) || (fabs((domain.e(ei) - gold_e[ei]) / gold_e[ei]) > 0.0000000001)) {
//          errors++;
//          char error_detail[200];
//          sprintf(error_detail,"(MeshEnergy) p: [%d], r: %u, e: %u", ei, domain.e(ei), gold_e[ei]);
//#ifdef LOGS
//          log_error_detail(error_detail);
//#endif
//      }
//   }
//
//   //printf("error energy:%d\n",errors);
//
//   for (int ei=0; ei < domain.numElem(); ++ei) {
//      int i = domain.numNode()*3 + domain.numElem() + ei;
//      if ((fabs((domain.p(ei) - gold_p[ei]) / domain.p(ei)) > 0.0000000001) || (fabs((domain.p(ei) - gold_p[ei]) / gold_p[ei]) > 0.0000000001)) {
//          errors++;
//          char error_detail[200];
//          sprintf(error_detail,"(MeshPressure) p: [%d], r: %u, e: %u", ei, domain.p(ei), gold_p[ei]);
//#ifdef LOGS
//          log_error_detail(error_detail);
//#endif
//      }
//   }
//
//   //printf("error press:%d\n",errors);
//   for (int ei=0; ei < domain.numElem(); ++ei) {
//      int i = domain.numNode()*3 + domain.numElem()*2 + ei;
//      if ((fabs((domain.v(ei) - gold_v[ei]) / domain.v(ei)) > 0.0000000001) || (fabs((domain.v(ei) - gold_v[ei]) / gold_v[ei]) > 0.0000000001)) {
//          errors++;
//          char error_detail[200];
//          sprintf(error_detail,"(MeshRelVol) p: [%d], r: %u, e: %u", ei, domain.v(ei), gold_v[ei]);
//#ifdef LOGS
//          log_error_detail(error_detail);
//#endif
//      }
//   }
//   //printf("error v:%d\n",errors);
//
//   for (int ei=0; ei < domain.numElem(); ++ei) {
//      int i = domain.numNode()*3 + domain.numElem()*3 + ei;
//      if ((fabs((domain.q(ei) - gold_q[ei]) / domain.q(ei)) > 0.0000000001) || (fabs((domain.q(ei) - gold_q[ei]) / gold_q[ei]) > 0.0000000001)) {
//          errors++;
//          char error_detail[200];
//          sprintf(error_detail,"(Mesh q) p: [%d], r: %u, e: %u", ei, domain.q(ei), gold_q[ei]);
//#ifdef LOGS
//          log_error_detail(error_detail);
//#endif
//      }
//   }
//   //printf("error q:%d\n",errors);
//
//   /* Write out nodal speed, velocities */
//   i_d=0;
//   for(int ni=0 ; ni < domain.numNode() ; ++ni) {
//      int i = domain.numNode()*3 + domain.numElem()*4 + ni;
//      if ((fabs((domain.xd(ni) - gold_speed[i_d]) / domain.xd(ni)) > 0.0000000001) || (fabs((domain.xd(ni) - gold_speed[i_d]) / gold_speed[i_d]) > 0.0000000001)) {
//          errors++;
//          char error_detail[200];
//          sprintf(error_detail,"(MeshSpeed xd) p: [%d], r: %u, e: %u", ni, domain.xd(ni), gold_speed[i_d]);
//#ifdef LOGS
//          log_error_detail(error_detail);
//#endif
//      }
//      i_d++;
//      if ((fabs((domain.yd(ni) - gold_speed[i_d]) / domain.yd(ni)) > 0.0000000001) || (fabs((domain.yd(ni) - gold_speed[i_d]) / gold_speed[i_d]) > 0.0000000001)) {
//          errors++;
//          char error_detail[200];
//          sprintf(error_detail,"(MeshSpeed yd) p: [%d], r: %u, e: %u", ni, domain.yd(ni), gold_speed[i_d]);
//#ifdef LOGS
//          log_error_detail(error_detail);
//#endif
//      }
//      i_d++;
//      if ((fabs((domain.zd(ni) - gold_speed[i_d]) / domain.zd(ni)) > 0.0000000001) || (fabs((domain.zd(ni) - gold_speed[i_d]) / gold_speed[i_d]) > 0.0000000001)) {
//          errors++;
//          char error_detail[200];
//          sprintf(error_detail,"(MeshSpeed zd) p: [%d], r: %u, e: %u", ni, domain.zd(ni), gold_speed[i_d]);
//#ifdef LOGS
//          log_error_detail(error_detail);
//#endif
//      }
//      i_d++;
//   }
//   //printf("error speed:%d\n",errors);
//
////        #pragma omp parallel for reduction(+:errors) private(i)
//#ifdef LOGS
//        log_error_count(errors);
//#endif
//        if(errors > 0) {
//            printf("Errors: %d\n",errors);
//        } else {
//            //printf("Errors: %d\n",errors);
//            printf(".");
//        }
//}
///******************************************/

int main(int argc, char *argv[])
{
    Domain *locDom ;
    Int_t numRanks ;
    Int_t myRank ;
    struct cmdLineOpts opts;

    numRanks = 1;
    myRank = 0;

    /* Set defaults that can be overridden by command line opts */
    opts.nx  = 30;

    ParseCommandLineOptions(argc, argv, myRank, &opts);

    if(!opts.gold_filename) {
        printf("Error: Gold file need to be specified, use -g flag\n");
        exit(1);
    }
    char * gold_filename;
    gold_filename = (char*)malloc(500*sizeof(char));
    strcpy(gold_filename, opts.gold_filename);
    if(opts.output_filename == NULL) {
        printf("Error: Output file need to be specified, use -o flag\n");
        exit(1);
    }

    int nx = opts.nx;
    int numElem = nx*nx*nx;
    int numNode = (nx+1)*(nx+1)*(nx+1);


    printf("#HEADER size:%d omp_num_threads:%d its:%d balance:%d cost:%d\n", opts.nx, omp_get_max_threads(), opts.its,opts.balance,opts.cost);

    int *gold_meshConn = (int*) malloc(numElem*8*sizeof(int));
    double *gold_coord = (double*) malloc(numNode*3*sizeof(double));
    double *gold_e = (double*) malloc(numElem*sizeof(double));
    double *gold_p = (double*) malloc(numElem*sizeof(double));
    double *gold_v = (double*) malloc(numElem*sizeof(double));
    double *gold_q = (double*) malloc(numElem*sizeof(double));
    double *gold_speed = (double*) malloc(numNode*3*sizeof(double));
    read_solution(nx, gold_filename, gold_meshConn, gold_coord, gold_e, gold_p, gold_v, gold_q, gold_speed);
    int *out_meshConn = (int*) malloc(numElem*8*sizeof(int));
    double *out_coord = (double*) malloc(numNode*3*sizeof(double));
    double *out_e = (double*) malloc(numElem*sizeof(double));
    double *out_p = (double*) malloc(numElem*sizeof(double));
    double *out_v = (double*) malloc(numElem*sizeof(double));
    double *out_q = (double*) malloc(numElem*sizeof(double));
    double *out_speed = (double*) malloc(numNode*3*sizeof(double));
    read_solution(nx, opts.output_filename, out_meshConn, out_coord, out_e, out_p, out_v, out_q, out_speed);

    //check_solution
    int i = 0, errors=0;
    /* Check the mesh connectivity in fully unstructured format */
    for (int ei=0; ei < numElem; ++ei) {
        for (int ni=0; ni < 8; ++ni) {
            if(out_meshConn[ni] != gold_meshConn[ni]) {
                errors++;
                char error_detail[200];
                sprintf(error_detail,"(MeshConn) p: [%d], r: %u, e: %u", ni, out_meshConn[ni], gold_meshConn[ni]);
                printf("%s\n",error_detail);
            }
        }
    }
    //printf("error conn:%d\n",errors);

    /* Check the mesh coordinates associated with the mesh */
    int i_d=0;
    for (int ni=0; ni < numNode ; ++ni) {
        if ((fabs((out_coord[i_d] - gold_coord[i_d]) / out_coord[i_d]) > 0.0000000001) || (fabs((out_coord[i_d] - gold_coord[i_d]) / gold_coord[i_d]) > 0.0000000001)) {
            errors++;
            char error_detail[200];
            sprintf(error_detail,"(MeshCoordinates x) p: [%d], r: %u, e: %u", ni, out_coord[i_d], gold_coord[i_d]);
            printf("%s\n",error_detail);
        }
        i_d++;
        if ((fabs((out_coord[i_d] - gold_coord[i_d]) / out_coord[i_d]) > 0.0000000001) || (fabs((out_coord[i_d] - gold_coord[i_d]) / gold_coord[i_d]) > 0.0000000001)) {
            errors++;
            char error_detail[200];
            sprintf(error_detail,"(MeshCoordinates y) p: [%d], r: %u, e: %u", ni, out_coord[i_d], gold_coord[i_d]);
            printf("%s\n",error_detail);
        }
        i_d++;
        if ((fabs((out_coord[i_d] - gold_coord[i_d]) / out_coord[i_d]) > 0.0000000001) || (fabs((out_coord[i_d] - gold_coord[i_d]) / gold_coord[i_d]) > 0.0000000001)) {
            errors++;
            char error_detail[200];
            sprintf(error_detail,"(MeshCoordinates z) p: [%d], r: %u, e: %u", ni, out_coord[i_d], gold_coord[i_d]);
            printf("%s\n",error_detail);
        }
        i_d++;
    }

    //printf("error coord:%d\n",errors);
    /* Write out pressure, energy, relvol, q */

    for (int ei=0; ei < numElem; ++ei) {
        int i = numNode*3 + ei;
        if ((fabs((out_e[ei] - gold_e[ei]) / out_e[ei]) > 0.0000000001) || (fabs((out_e[ei] - gold_e[ei]) / gold_e[ei]) > 0.0000000001)) {
            errors++;
            char error_detail[200];
            sprintf(error_detail,"(MeshEnergy) p: [%d], r: %u, e: %u", ei, out_e[ei], gold_e[ei]);
            printf("%s\n",error_detail);
        }
    }

    //printf("error energy:%d\n",errors);

    for (int ei=0; ei < numElem; ++ei) {
        int i = numNode*3 + numElem + ei;
        if ((fabs((out_p[ei] - gold_p[ei]) / out_p[ei]) > 0.0000000001) || (fabs((out_p[ei] - gold_p[ei]) / gold_p[ei]) > 0.0000000001)) {
            errors++;
            char error_detail[200];
            sprintf(error_detail,"(MeshPressure) p: [%d], r: %u, e: %u", ei, out_p[ei], gold_p[ei]);
            printf("%s\n",error_detail);
        }
    }

    //printf("error press:%d\n",errors);
    for (int ei=0; ei < numElem; ++ei) {
        int i = numNode*3 + numElem*2 + ei;
        if ((fabs((out_v[ei] - gold_v[ei]) / out_v[ei]) > 0.0000000001) || (fabs((out_v[ei] - gold_v[ei]) / gold_v[ei]) > 0.0000000001)) {
            errors++;
            char error_detail[200];
            sprintf(error_detail,"(MeshRelVol) p: [%d], r: %u, e: %u", ei, out_v[ei], gold_v[ei]);
            printf("%s\n",error_detail);
        }
    }
    //printf("error v:%d\n",errors);

    for (int ei=0; ei < numElem; ++ei) {
        int i = numNode*3 + numElem*3 + ei;
        if ((fabs((out_q[ei] - gold_q[ei]) / out_q[ei]) > 0.0000000001) || (fabs((out_q[ei] - gold_q[ei]) / gold_q[ei]) > 0.0000000001)) {
            errors++;
            char error_detail[200];
            sprintf(error_detail,"(Mesh q) p: [%d], r: %u, e: %u", ei, out_q[ei], gold_q[ei]);
            printf("%s\n",error_detail);
        }
    }
    //printf("error q:%d\n",errors);

    /* Write out nodal speed, velocities */
    i_d=0;
    for(int ni=0 ; ni < numNode ; ++ni) {
        int i = numNode*3 + numElem*4 + ni;
        if ((fabs((out_speed[i_d] - gold_speed[i_d]) / out_speed[i_d]) > 0.0000000001) || (fabs((out_speed[i_d] - gold_speed[i_d]) / gold_speed[i_d]) > 0.0000000001)) {
            errors++;
            char error_detail[200];
            sprintf(error_detail,"(MeshSpeed xd) p: [%d], r: %u, e: %u", ni, out_speed[i_d], gold_speed[i_d]);
            printf("%s\n",error_detail);
        }
        i_d++;
        if ((fabs((out_speed[i_d] - gold_speed[i_d]) / out_speed[i_d]) > 0.0000000001) || (fabs((out_speed[i_d] - gold_speed[i_d]) / gold_speed[i_d]) > 0.0000000001)) {
            errors++;
            char error_detail[200];
            sprintf(error_detail,"(MeshSpeed yd) p: [%d], r: %u, e: %u", ni, out_speed[i_d], gold_speed[i_d]);
            printf("%s\n",error_detail);
        }
        i_d++;
        if ((fabs((out_speed[i_d] - gold_speed[i_d]) / out_speed[i_d]) > 0.0000000001) || (fabs((out_speed[i_d] - gold_speed[i_d]) / gold_speed[i_d]) > 0.0000000001)) {
            errors++;
            char error_detail[200];
            sprintf(error_detail,"(MeshSpeed zd) p: [%d], r: %u, e: %u", ni, out_speed[i_d], gold_speed[i_d]);
            printf("%s\n",error_detail);
        }
        i_d++;
    }

    printf("#SDC Ite:1 KerTime:0.0 AccTime:0.0 KerErr:%d AccErr:%d\n#END",errors, errors);


    return 0 ;
}
