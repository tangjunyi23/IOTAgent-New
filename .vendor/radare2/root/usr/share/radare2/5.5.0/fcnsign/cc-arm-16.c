// SDB-CGEN V1.8.3
// gcc -DMAIN=1 cc_arm_16.c ; ./a.out > cc_arm_16.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"arm16","cc"}, 
  {"arm32","cc"}, 
  {"cc.arm16.arg0","r0"}, 
  {"cc.arm16.arg1","r1"}, 
  {"cc.arm16.arg2","r2"}, 
  {"cc.arm16.arg3","r3"}, 
  {"cc.arm16.argn","stack"}, 
  {"cc.arm16.ret","r0"}, 
  {"cc.arm32.arg0","r0"}, 
  {"cc.arm32.arg1","r1"}, 
  {"cc.arm32.arg2","r2"}, 
  {"cc.arm32.argn","stack"}, 
  {"cc.arm32.ret","r0"}, 
  {"default.cc","arm16"}, 
  {NULL, NULL}
};
// 0x55ce888d3e90
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_cc_arm_16_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_cc_arm_16_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_cc_arm_16(x,y) gperf_cc_arm_16_hash(x)
const unsigned int gperf_cc_arm_16_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_cc_arm_16 = {
  .name = "cc-arm-16",
  .get = &gperf_cc_arm_16_get,
  .hash = &gperf_cc_arm_16_hash,
  .foreach = &gperf_cc_arm_16_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_cc_arm_16.get)("foo");
	printf ("%s\n", s);
}
#endif
