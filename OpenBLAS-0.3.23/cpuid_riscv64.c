/*****************************************************************************
Copyright (c) 2011-2022, The OpenBLAS Project
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
      derived from this software without specific prior written
      permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

**********************************************************************************/


/*********************************************************************/
/* Copyright 2009, 2010 The University of Texas at Austin.           */
/* All rights reserved.                                              */
/*                                                                   */
/* Redistribution and use in source and binary forms, with or        */
/* without modification, are permitted provided that the following   */
/* conditions are met:                                               */
/*                                                                   */
/*   1. Redistributions of source code must retain the above         */
/*      copyright notice, this list of conditions and the following  */
/*      disclaimer.                                                  */
/*                                                                   */
/*   2. Redistributions in binary form must reproduce the above      */
/*      copyright notice, this list of conditions and the following  */
/*      disclaimer in the documentation and/or other materials       */
/*      provided with the distribution.                              */
/*                                                                   */
/*    THIS  SOFTWARE IS PROVIDED  BY THE  UNIVERSITY OF  TEXAS AT    */
/*    AUSTIN  ``AS IS''  AND ANY  EXPRESS OR  IMPLIED WARRANTIES,    */
/*    INCLUDING, BUT  NOT LIMITED  TO, THE IMPLIED  WARRANTIES OF    */
/*    MERCHANTABILITY  AND FITNESS FOR  A PARTICULAR  PURPOSE ARE    */
/*    DISCLAIMED.  IN  NO EVENT SHALL THE UNIVERSITY  OF TEXAS AT    */
/*    AUSTIN OR CONTRIBUTORS BE  LIABLE FOR ANY DIRECT, INDIRECT,    */
/*    INCIDENTAL,  SPECIAL, EXEMPLARY,  OR  CONSEQUENTIAL DAMAGES    */
/*    (INCLUDING, BUT  NOT LIMITED TO,  PROCUREMENT OF SUBSTITUTE    */
/*    GOODS  OR  SERVICES; LOSS  OF  USE,  DATA,  OR PROFITS;  OR    */
/*    BUSINESS INTERRUPTION) HOWEVER CAUSED  AND ON ANY THEORY OF    */
/*    LIABILITY, WHETHER  IN CONTRACT, STRICT  LIABILITY, OR TORT    */
/*    (INCLUDING NEGLIGENCE OR OTHERWISE)  ARISING IN ANY WAY OUT    */
/*    OF  THE  USE OF  THIS  SOFTWARE,  EVEN  IF ADVISED  OF  THE    */
/*    POSSIBILITY OF SUCH DAMAGE.                                    */
/*                                                                   */
/* The views and conclusions contained in the software and           */
/* documentation are those of the authors and should not be          */
/* interpreted as representing official policies, either expressed   */
/* or implied, of The University of Texas at Austin.                 */
/*********************************************************************/

#define CPU_GENERIC   0
#define CPU_C910V     1

static char *cpuname[] = {
  "RISCV64_GENERIC",
  "C910V"
};

int detect(void){
#ifdef __linux
  FILE *infile;
  char buffer[512],isa_buffer[512],model_buffer[512];
  const char* check_c910_str = "T-HEAD C910";
  char *pmodel = NULL, *pisa = NULL;

  infile = fopen("/proc/cpuinfo", "r");
  while (fgets(buffer, sizeof(buffer), infile)){
    if(!strncmp(buffer, "model name", 10)){
      strcpy(model_buffer, buffer);
      pmodel = strchr(isa_buffer, ':') + 1;
    }

    if(!strncmp(buffer, "isa", 3)){
      strcpy(isa_buffer, buffer);
      pisa = strchr(isa_buffer, '4') + 1;
    }
  }

  fclose(infile);

  if (!pmodel)
   return(CPU_GENERIC);
   
  if (strstr(pmodel, check_c910_str) && strchr(pisa, 'v'))
    return CPU_C910V;

  return CPU_GENERIC;
#endif

  return CPU_GENERIC;
}

char *get_corename(void){
  return cpuname[detect()];
}

void get_architecture(void){
  printf("RISCV64");
}

void get_subarchitecture(void){
  printf("%s",cpuname[detect()]);
}

void get_subdirname(void){
  printf("riscv64");
}

void get_cpuconfig(void){
  printf("#define %s\n", cpuname[detect()]);
  printf("#define L1_DATA_SIZE 65536\n");
  printf("#define L1_DATA_LINESIZE 32\n");
  printf("#define L2_SIZE 512488\n");
  printf("#define L2_LINESIZE 32\n");
  printf("#define DTB_DEFAULT_ENTRIES 64\n");
  printf("#define DTB_SIZE 4096\n");
  printf("#define L2_ASSOCIATIVE 4\n");
}

void get_libname(void){
  printf("riscv64\n");
}
