/***************************************************************************
Copyright (c) 2022, Arm Ltd
All rights reserved.
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:
1. Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in
the documentation and/or other materials provided with the
distribution.
3. Neither the name of the OpenBLAS project nor the names of
its contributors may be used to endorse or promote products
derived from this software without specific prior written permission.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE OPENBLAS PROJECT OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*****************************************************************************/

#include "common.h"

#include <arm_sve.h>

#ifdef DOUBLE
#define SVE_TYPE svfloat64_t
#define SVE_ZERO svdup_f64(0.0)
#define SVE_WHILELT svwhilelt_b64
#define SVE_ALL svptrue_b64()
#define SVE_WIDTH svcntd()
#else
#define SVE_TYPE svfloat32_t
#define SVE_ZERO svdup_f32(0.0)
#define SVE_WHILELT svwhilelt_b32
#define SVE_ALL svptrue_b32()
#define SVE_WIDTH svcntw()
#endif

static FLOAT dot_kernel_sve(BLASLONG n, FLOAT *x, FLOAT *y) {
        SVE_TYPE acc_a = SVE_ZERO;
        SVE_TYPE acc_b = SVE_ZERO;

        BLASLONG sve_width = SVE_WIDTH;

        for (BLASLONG i = 0; i < n; i += sve_width * 2) {
                svbool_t pg_a = SVE_WHILELT(i, n);
                svbool_t pg_b = SVE_WHILELT(i + sve_width, n);

                SVE_TYPE x_vec_a = svld1(pg_a, &x[i]);
                SVE_TYPE y_vec_a = svld1(pg_a, &y[i]);
                SVE_TYPE x_vec_b = svld1(pg_b, &x[i + sve_width]);
                SVE_TYPE y_vec_b = svld1(pg_b, &y[i + sve_width]);

                acc_a = svmla_m(pg_a, acc_a, x_vec_a, y_vec_a);
                acc_b = svmla_m(pg_b, acc_b, x_vec_b, y_vec_b);
        }

        return svaddv(SVE_ALL, acc_a) + svaddv(SVE_ALL, acc_b);
}
