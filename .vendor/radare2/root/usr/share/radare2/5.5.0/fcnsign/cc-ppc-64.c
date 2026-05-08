// SDB-CGEN V1.8.3
// gcc -DMAIN=1 cc_ppc_64.c ; ./a.out > cc_ppc_64.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"cc.ppc-64.arg0","r3"}, 
  {"cc.ppc-64.arg1","r4"}, 
  {"cc.ppc-64.arg2","r5"}, 
  {"cc.ppc-64.arg3","r6"}, 
  {"cc.ppc-64.arg4","r7"}, 
  {"cc.ppc-64.arg5","r8"}, 
  {"cc.ppc-64.arg6","r9"}, 
  {"cc.ppc-64.arg7","r10"}, 
  {"cc.ppc-64.argn","stack_rev"}, 
  {"cc.ppc-64.ret","r3"}, 
  {"default.cc","ppc-64"}, 
  {"ppc-64","cc"}, 
  {NULL, NULL}
};
// 0x555f63c49d80
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_cc_ppc_64_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_cc_ppc_64_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_cc_ppc_64(x,y) gperf_cc_ppc_64_hash(x)
const unsigned int gperf_cc_ppc_64_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_cc_ppc_64 = {
  .name = "cc-ppc-64",
  .get = &gperf_cc_ppc_64_get,
  .hash = &gperf_cc_ppc_64_hash,
  .foreach = &gperf_cc_ppc_64_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_cc_ppc_64.get)("foo");
	printf ("%s\n", s);
}
#endif
