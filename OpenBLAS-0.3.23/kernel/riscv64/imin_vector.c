/***************************************************************************
Copyright (c) 2020, The OpenBLAS Project
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
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*****************************************************************************/

#include "common.h"
#include <math.h>
#include <float.h>

#if defined(DOUBLE)

#define ABS fabs
#define VSETVL(n) vsetvl_e64m8(n)
#define VSETVL_MAX vsetvlmax_e64m1()
#define FLOAT_V_T vfloat64m8_t
#define FLOAT_V_T_M1 vfloat64m1_t
#define VLEV_FLOAT vle_v_f64m8
#define VLSEV_FLOAT vlse_v_f64m8
#define VFREDMINVS_FLOAT vfredmin_vs_f64m8_f64m1
#define MASK_T vbool8_t
#define VMFLTVV_FLOAT vmflt_vv_f64m8_b8
#define VFMVVF_FLOAT vfmv_v_f_f64m8
#define VFMVVF_FLOAT_M1 vfmv_v_f_f64m1
#define VFMINVV_FLOAT vfmin_vv_f64m8
#define VMFLEVF_FLOAT vmfle_vf_f64m8_b8
#define VMFIRSTM vmfirst_m_b8
#define UINT_V_T vuint64m8_t
#define VIDV_MASK_UINT vid_v_u64m8_m
#define VIDV_UINT vid_v_u64m8
#define VADDVX_MASK_UINT vadd_vx_u64m8_m
#define VADDVX_UINT vadd_vx_u64m8
#define VMVVX_UINT vmv_v_x_u64m8
#else

#define ABS fabsf
#define VSETVL(n) vsetvl_e32m8(n)
#define VSETVL_MAX vsetvlmax_e32m1()
#define FLOAT_V_T vfloat32m8_t
#define FLOAT_V_T_M1 vfloat32m1_t
#define VLEV_FLOAT vle_v_f32m8
#define VLSEV_FLOAT vlse_v_f32m8
#define VFREDMINVS_FLOAT vfredmin_vs_f32m8_f32m1
#define MASK_T vbool4_t
#define VMFLTVV_FLOAT vmflt_vv_f32m8_b4
#define VFMVVF_FLOAT vfmv_v_f_f32m8
#define VFMVVF_FLOAT_M1 vfmv_v_f_f32m1
#define VFMINVV_FLOAT vfmin_vv_f32m8
#define VMFLEVF_FLOAT vmfle_vf_f32m8_b4
#define VMFIRSTM vmfirst_m_b4
#define UINT_V_T vuint32m8_t
#define VIDV_MASK_UINT vid_v_u32m8_m
#define VIDV_UINT vid_v_u32m8
#define VADDVX_MASK_UINT vadd_vx_u32m8_m
#define VADDVX_UINT vadd_vx_u32m8
#define VMVVX_UINT vmv_v_x_u32m8
#endif


BLASLONG CNAME(BLASLONG n, FLOAT *x, BLASLONG inc_x)
{
	BLASLONG i=0, j=0;
	FLOAT minf=FLT_MAX;
        unsigned int min_index = 0;
	if (n <= 0 || inc_x <= 0) return(min_index);

        FLOAT_V_T vx, v_min;
        UINT_V_T v_min_index;
        MASK_T mask;
        unsigned int gvl = 0;
        FLOAT_V_T_M1 v_res, v_max;
        gvl = VSETVL_MAX;
        v_res = VFMVVF_FLOAT_M1(0, gvl);
        v_max = VFMVVF_FLOAT_M1(FLT_MAX, gvl);

        if(inc_x == 1){
                gvl = VSETVL(n);
                v_min = VFMVVF_FLOAT(FLT_MAX, gvl);
                v_min_index = VMVVX_UINT(0, gvl);
                for(i=0,j=0; i < n/gvl; i++){
                        vx = VLEV_FLOAT(&x[j], gvl);
                        //index where element less than v_min
                        mask = VMFLTVV_FLOAT(vx, v_min, gvl);
                        v_min_index = VIDV_MASK_UINT(mask, v_min_index, gvl);
/*
#if defined(DOUBLE)
asm volatile(
        "vor.vv v0, %1, %1 \n\t"
        "vsetvli x0, %2, e64,m8 \n\t"
        "vid.v %0, v0.t \n\t"
        :"+v"(v_min_index)
        :"v"(mask), "r"(gvl)
        :"v0");
#else
asm volatile(
        "vor.vv v0, %1, %1 \n\t"
        "vsetvli x0, %2, e32,m8 \n\t"
        "vid.v %0, v0.t \n\t"
        :"+v"(v_min_index)
        :"v"(mask), "r"(gvl)
        :"v0");
#endif
*/
                        v_min_index = VADDVX_MASK_UINT(mask, v_min_index, v_min_index, j,gvl);

                        //update v_min and start_index j
                        v_min = VFMINVV_FLOAT(v_min, vx, gvl);
                        j += gvl;
                }
                v_res = VFREDMINVS_FLOAT(v_res, v_min, v_max, gvl);
                minf = *((FLOAT*)&v_res);
                mask = VMFLEVF_FLOAT(v_min, minf, gvl);
                min_index = VMFIRSTM(mask,gvl);
                min_index = *((unsigned int*)&v_min_index+min_index);

                if(j < n){
                        gvl = VSETVL(n-j);
                        v_min = VLEV_FLOAT(&x[j], gvl);

                        v_res = VFREDMINVS_FLOAT(v_res, v_min, v_max, gvl);
                        FLOAT cur_minf = *((FLOAT*)&v_res);
                        if(cur_minf < minf){
                                //tail index
                                v_min_index = VIDV_UINT(gvl);
                                v_min_index = VADDVX_UINT(v_min_index, j, gvl);
                                mask = VMFLEVF_FLOAT(v_min, cur_minf, gvl);
                                min_index = VMFIRSTM(mask,gvl);
                                min_index = *((unsigned int*)&v_min_index+min_index);
                        }
                }
        }else{
                gvl = VSETVL(n);
                unsigned int stride_x = inc_x * sizeof(FLOAT);
                unsigned int idx = 0, inc_v = gvl * inc_x;

                v_min = VFMVVF_FLOAT(FLT_MAX, gvl);
                v_min_index = VMVVX_UINT(0, gvl);
                for(i=0,j=0; i < n/gvl; i++){
                        vx = VLSEV_FLOAT(&x[idx], stride_x, gvl);

                        //index where element less than v_min
                        mask = VMFLTVV_FLOAT(vx, v_min, gvl);
                        v_min_index = VIDV_MASK_UINT(mask, v_min_index, gvl);
/*
#if defined(DOUBLE)
asm volatile(
        "vor.vv v0, %1, %1 \n\t"
        "vsetvli x0, %2, e64,m8 \n\t"
        "vid.v %0, v0.t \n\t"
        :"+v"(v_min_index)
        :"v"(mask), "r"(gvl)
        :"v0");
#else
asm volatile(
        "vor.vv v0, %1, %1 \n\t"
        "vsetvli x0, %2, e32,m8 \n\t"
        "vid.v %0, v0.t \n\t"
        :"+v"(v_min_index)
        :"v"(mask), "r"(gvl)
        :"v0");
#endif
*/

                        v_min_index = VADDVX_MASK_UINT(mask, v_min_index, v_min_index, j,gvl);

                        //update v_min and start_index j
                        v_min = VFMINVV_FLOAT(v_min, vx, gvl);
                        j += gvl;
                        idx += inc_v;
                }
                v_res = VFREDMINVS_FLOAT(v_res, v_min, v_max, gvl);
                minf = *((FLOAT*)&v_res);
                mask = VMFLEVF_FLOAT(v_min, minf, gvl);
                min_index = VMFIRSTM(mask,gvl);
                min_index = *((unsigned int*)&v_min_index+min_index);

                if(j < n){
                        gvl = VSETVL(n-j);
                        v_min = VLSEV_FLOAT(&x[idx], stride_x, gvl);

                        v_res = VFREDMINVS_FLOAT(v_res, v_min, v_max, gvl);
                        FLOAT cur_minf = *((FLOAT*)&v_res);
                        if(cur_minf < minf){
                                //tail index
                                v_min_index = VIDV_UINT(gvl);
                                v_min_index = VADDVX_UINT(v_min_index, j, gvl);
                                mask = VMFLEVF_FLOAT(v_min, cur_minf, gvl);
                                min_index = VMFIRSTM(mask,gvl);
                                min_index = *((unsigned int*)&v_min_index+min_index);
                        }
                }
        }
	return(min_index+1);
}


