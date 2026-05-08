// SDB-CGEN V1.8.3
// gcc -DMAIN=1 cc_ppc_32.c ; ./a.out > cc_ppc_32.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"cc.ppc-32.arg0","r3"}, 
  {"cc.ppc-32.arg1","r4"}, 
  {"cc.ppc-32.arg2","r5"}, 
  {"cc.ppc-32.arg3","r6"}, 
  {"cc.ppc-32.arg4","r7"}, 
  {"cc.ppc-32.arg5","r8"}, 
  {"cc.ppc-32.arg6","r9"}, 
  {"cc.ppc-32.arg7","r10"}, 
  {"cc.ppc-32.argn","stack_rev"}, 
  {"cc.ppc-32.ret","r3"}, 
  {"default.cc","ppc-32"}, 
  {"ppc-32","cc"}, 
  {NULL, NULL}
};
// 0x559c50d3adb0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_cc_ppc_32_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_cc_ppc_32_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_cc_ppc_32(x,y) gperf_cc_ppc_32_hash(x)
const unsigned int gperf_cc_ppc_32_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_cc_ppc_32 = {
  .name = "cc-ppc-32",
  .get = &gperf_cc_ppc_32_get,
  .hash = &gperf_cc_ppc_32_hash,
  .foreach = &gperf_cc_ppc_32_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_cc_ppc_32.get)("foo");
	printf ("%s\n", s);
}
#endif
