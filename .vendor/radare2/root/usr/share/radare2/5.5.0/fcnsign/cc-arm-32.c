// SDB-CGEN V1.8.3
// gcc -DMAIN=1 cc_arm_32.c ; ./a.out > cc_arm_32.h
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
  {"cc.arm32.ret","r0"}, 
  {"cc.swift.arg0","r0"}, 
  {"cc.swift.arg1","r1"}, 
  {"cc.swift.arg2","r2"}, 
  {"cc.swift.arg3","r3"}, 
  {"cc.swift.argn","stack"}, 
  {"cc.swift.ret","r0"}, 
  {"cc.swift.self","r8"}, 
  {"default.cc","arm32"}, 
  {"swift","cc"}, 
  {NULL, NULL}
};
// 0x55c75c65a590
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_cc_arm_32_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_cc_arm_32_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_cc_arm_32(x,y) gperf_cc_arm_32_hash(x)
const unsigned int gperf_cc_arm_32_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_cc_arm_32 = {
  .name = "cc-arm-32",
  .get = &gperf_cc_arm_32_get,
  .hash = &gperf_cc_arm_32_hash,
  .foreach = &gperf_cc_arm_32_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_cc_arm_32.get)("foo");
	printf ("%s\n", s);
}
#endif
