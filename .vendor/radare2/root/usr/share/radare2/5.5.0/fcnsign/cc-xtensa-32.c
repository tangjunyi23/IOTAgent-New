// SDB-CGEN V1.8.3
// gcc -DMAIN=1 cc_xtensa_32.c ; ./a.out > cc_xtensa_32.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"call0","cc"}, 
  {"cc.call0.arg0","a2"}, 
  {"cc.call0.arg1","a3"}, 
  {"cc.call0.arg2","a4"}, 
  {"cc.call0.arg3","a5"}, 
  {"cc.call0.arg4","a6"}, 
  {"cc.call0.arg5","a7"}, 
  {"cc.call0.argn","stack"}, 
  {"cc.call0.ret","a2"}, 
  {"default.cc","call0"}, 
  {NULL, NULL}
};
// 0x56250d2a8bd0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_cc_xtensa_32_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_cc_xtensa_32_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_cc_xtensa_32(x,y) gperf_cc_xtensa_32_hash(x)
const unsigned int gperf_cc_xtensa_32_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_cc_xtensa_32 = {
  .name = "cc-xtensa-32",
  .get = &gperf_cc_xtensa_32_get,
  .hash = &gperf_cc_xtensa_32_hash,
  .foreach = &gperf_cc_xtensa_32_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_cc_xtensa_32.get)("foo");
	printf ("%s\n", s);
}
#endif
