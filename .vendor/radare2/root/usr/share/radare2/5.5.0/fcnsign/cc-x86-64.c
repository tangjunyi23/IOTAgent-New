// SDB-CGEN V1.8.3
// gcc -DMAIN=1 cc_x86_64.c ; ./a.out > cc_x86_64.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"amd64","cc"}, 
  {"amd64syscall","cc"}, 
  {"cc.amd64.arg0","rdi"}, 
  {"cc.amd64.arg1","rsi"}, 
  {"cc.amd64.arg10","xmm4"}, 
  {"cc.amd64.arg2","rdx"}, 
  {"cc.amd64.arg3","rcx"}, 
  {"cc.amd64.arg4","r8"}, 
  {"cc.amd64.arg5","r9"}, 
  {"cc.amd64.arg6","xmm0"}, 
  {"cc.amd64.arg7","xmm1"}, 
  {"cc.amd64.arg8","xmm2"}, 
  {"cc.amd64.arg9","xmm3"}, 
  {"cc.amd64.ret","rax"}, 
  {"cc.amd64syscall.arg0","rdi"}, 
  {"cc.amd64syscall.arg1","rsi"}, 
  {"cc.amd64syscall.arg2","rdx"}, 
  {"cc.amd64syscall.arg3","r10"}, 
  {"cc.amd64syscall.arg4","r8"}, 
  {"cc.amd64syscall.arg5","r9"}, 
  {"cc.amd64syscall.ret","rax"}, 
  {"cc.ms.arg0","rcx"}, 
  {"cc.ms.arg1","rdx"}, 
  {"cc.ms.arg2","r8"}, 
  {"cc.ms.arg3","r9"}, 
  {"cc.ms.argn","stack"}, 
  {"cc.ms.ret","rax"}, 
  {"cc.swift.arg0","rdi"}, 
  {"cc.swift.arg1","rsi"}, 
  {"cc.swift.arg10","xmm4"}, 
  {"cc.swift.arg2","rdx"}, 
  {"cc.swift.arg3","rcx"}, 
  {"cc.swift.arg4","r8"}, 
  {"cc.swift.arg5","r9"}, 
  {"cc.swift.arg6","xmm0"}, 
  {"cc.swift.arg7","xmm1"}, 
  {"cc.swift.arg8","xmm2"}, 
  {"cc.swift.arg9","xmm3"}, 
  {"cc.swift.error","r12"}, 
  {"cc.swift.ret","rax"}, 
  {"cc.swift.self","r13"}, 
  {"default.cc","amd64"}, 
  {"ms","cc"}, 
  {"swift","cc"}, 
  {NULL, NULL}
};
// 0x55e393334ba0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_cc_x86_64_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_cc_x86_64_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_cc_x86_64(x,y) gperf_cc_x86_64_hash(x)
const unsigned int gperf_cc_x86_64_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_cc_x86_64 = {
  .name = "cc-x86-64",
  .get = &gperf_cc_x86_64_get,
  .hash = &gperf_cc_x86_64_hash,
  .foreach = &gperf_cc_x86_64_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_cc_x86_64.get)("foo");
	printf ("%s\n", s);
}
#endif
