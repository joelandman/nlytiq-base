/*****************************************************************************
  Copyright (c) 2014, Intel Corp.
  All rights reserved.

  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of Intel Corporation nor the names of its contributors
      may be used to endorse or promote products derived from this software
      without specific prior written permission.

  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
  THE POSSIBILITY OF SUCH DAMAGE.
*****************************************************************************
* Contents: Native high-level C interface to LAPACK function zggevx
* Author: Intel Corporation
*****************************************************************************/

#include "lapacke_utils.h"

lapack_int LAPACKE_zggevx( int matrix_layout, char balanc, char jobvl,
                           char jobvr, char sense, lapack_int n,
                           lapack_complex_double* a, lapack_int lda,
                           lapack_complex_double* b, lapack_int ldb,
                           lapack_complex_double* alpha,
                           lapack_complex_double* beta,
                           lapack_complex_double* vl, lapack_int ldvl,
                           lapack_complex_double* vr, lapack_int ldvr,
                           lapack_int* ilo, lapack_int* ihi, double* lscale,
                           double* rscale, double* abnrm, double* bbnrm,
                           double* rconde, double* rcondv )
{
    lapack_int info = 0;
    lapack_int lwork = -1;
    /* Additional scalars declarations for work arrays */
    lapack_int lrwork;
    lapack_logical* bwork = NULL;
    lapack_int* iwork = NULL;
    double* rwork = NULL;
    lapack_complex_double* work = NULL;
    lapack_complex_double work_query;
    if( matrix_layout != LAPACK_COL_MAJOR && matrix_layout != LAPACK_ROW_MAJOR ) {
        LAPACKE_xerbla( "LAPACKE_zggevx", -1 );
        return -1;
    }
#ifndef LAPACK_DISABLE_NAN_CHECK
    if( LAPACKE_get_nancheck() ) {
        /* Optionally check input matrices for NaNs */
        if( LAPACKE_zge_nancheck( matrix_layout, n, n, a, lda ) ) {
            return -7;
        }
        if( LAPACKE_zge_nancheck( matrix_layout, n, n, b, ldb ) ) {
            return -9;
        }
    }
#endif
    /* Additional scalars initializations for work arrays */
    if( LAPACKE_lsame( balanc, 's' ) || LAPACKE_lsame( balanc, 'b' ) ) {
        lrwork = MAX(1,6*n);
    } else {
        lrwork = MAX(1,2*n);
    }
    /* Allocate memory for working array(s) */
    if( LAPACKE_lsame( sense, 'b' ) || LAPACKE_lsame( sense, 'e' ) ||
        LAPACKE_lsame( sense, 'v' ) ) {
        bwork = (lapack_logical*)
            LAPACKE_malloc( sizeof(lapack_logical) * MAX(1,n) );
        if( bwork == NULL ) {
            info = LAPACK_WORK_MEMORY_ERROR;
            goto exit_level_0;
        }
    }
    if( LAPACKE_lsame( sense, 'b' ) || LAPACKE_lsame( sense, 'n' ) ||
        LAPACKE_lsame( sense, 'v' ) ) {
        iwork = (lapack_int*)LAPACKE_malloc( sizeof(lapack_int) * MAX(1,n+2) );
        if( iwork == NULL ) {
            info = LAPACK_WORK_MEMORY_ERROR;
            goto exit_level_1;
        }
    }
    rwork = (double*)LAPACKE_malloc( sizeof(double) * lrwork );
    if( rwork == NULL ) {
        info = LAPACK_WORK_MEMORY_ERROR;
        goto exit_level_2;
    }
    /* Query optimal working array(s) size */
    info = LAPACKE_zggevx_work( matrix_layout, balanc, jobvl, jobvr, sense, n, a,
                                lda, b, ldb, alpha, beta, vl, ldvl, vr, ldvr,
                                ilo, ihi, lscale, rscale, abnrm, bbnrm, rconde,
                                rcondv, &work_query, lwork, rwork, iwork,
                                bwork );
    if( info != 0 ) {
        goto exit_level_3;
    }
    lwork = LAPACK_Z2INT( work_query );
    /* Allocate memory for work arrays */
    work = (lapack_complex_double*)
        LAPACKE_malloc( sizeof(lapack_complex_double) * lwork );
    if( work == NULL ) {
        info = LAPACK_WORK_MEMORY_ERROR;
        goto exit_level_3;
    }
    /* Call middle-level interface */
    info = LAPACKE_zggevx_work( matrix_layout, balanc, jobvl, jobvr, sense, n, a,
                                lda, b, ldb, alpha, beta, vl, ldvl, vr, ldvr,
                                ilo, ihi, lscale, rscale, abnrm, bbnrm, rconde,
                                rcondv, work, lwork, rwork, iwork, bwork );
    /* Release memory and exit */
    LAPACKE_free( work );
exit_level_3:
    LAPACKE_free( rwork );
exit_level_2:
    if( LAPACKE_lsame( sense, 'b' ) || LAPACKE_lsame( sense, 'n' ) ||
        LAPACKE_lsame( sense, 'v' ) ) {
        LAPACKE_free( iwork );
    }
exit_level_1:
    if( LAPACKE_lsame( sense, 'b' ) || LAPACKE_lsame( sense, 'e' ) ||
        LAPACKE_lsame( sense, 'v' ) ) {
        LAPACKE_free( bwork );
    }
exit_level_0:
    if( info == LAPACK_WORK_MEMORY_ERROR ) {
        LAPACKE_xerbla( "LAPACKE_zggevx", info );
    }
    return info;
}
