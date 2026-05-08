// SDB-CGEN V1.8.3
// gcc -DMAIN=1 cc_mips_32.c ; ./a.out > cc_mips_32.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"cc.n32.arg0","a0"}, 
  {"cc.n32.arg1","a1"}, 
  {"cc.n32.arg2","a2"}, 
  {"cc.n32.arg3","a3"}, 
  {"cc.n32.arg4","a4"}, 
  {"cc.n32.arg5","a5"}, 
  {"cc.n32.arg6","a6"}, 
  {"cc.n32.arg7","a7"}, 
  {"cc.n32.argn","stack"}, 
  {"cc.n32.ret","v0"}, 
  {"cc.o32.arg0","a0"}, 
  {"cc.o32.arg1","a1"}, 
  {"cc.o32.arg2","a2"}, 
  {"cc.o32.arg3","a3"}, 
  {"cc.o32.argn","stack"}, 
  {"cc.o32.ret","v0"}, 
  {"default.cc","n32"}, 
  {"n32","cc"}, 
  {"o32","cc"}, 
  {NULL, NULL}
};
// 0x55dc41f435b0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_cc_mips_32_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_cc_mips_32_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_cc_mips_32(x,y) gperf_cc_mips_32_hash(x)
const unsigned int gperf_cc_mips_32_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_cc_mips_32 = {
  .name = "cc-mips-32",
  .get = &gperf_cc_mips_32_get,
  .hash = &gperf_cc_mips_32_hash,
  .foreach = &gperf_cc_mips_32_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_cc_mips_32.get)("foo");
	printf ("%s\n", s);
}
#endif
