// SDB-CGEN V1.8.3
// gcc -DMAIN=1 cc_arm_64.c ; ./a.out > cc_arm_64.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"arm64","cc"}, 
  {"cc.arm64.arg0","x0"}, 
  {"cc.arm64.arg1","x1"}, 
  {"cc.arm64.arg2","x2"}, 
  {"cc.arm64.arg3","x3"}, 
  {"cc.arm64.arg4","x4"}, 
  {"cc.arm64.arg5","x5"}, 
  {"cc.arm64.arg6","x6"}, 
  {"cc.arm64.arg7","x7"}, 
  {"cc.arm64.argn","stack"}, 
  {"cc.arm64.ret","x0"}, 
  {"cc.swift.arg0","x0"}, 
  {"cc.swift.arg1","x1"}, 
  {"cc.swift.arg2","x2"}, 
  {"cc.swift.arg3","x3"}, 
  {"cc.swift.arg4","x4"}, 
  {"cc.swift.arg5","x5"}, 
  {"cc.swift.arg6","x6"}, 
  {"cc.swift.arg7","x7"}, 
  {"cc.swift.argn","stack"}, 
  {"cc.swift.error","x21"}, 
  {"cc.swift.ret","x0"}, 
  {"cc.swift.self","x20"}, 
  {"default.cc","arm64"}, 
  {"swift","cc"}, 
  {NULL, NULL}
};
// 0x5627fd1dca30
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_cc_arm_64_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_cc_arm_64_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_cc_arm_64(x,y) gperf_cc_arm_64_hash(x)
const unsigned int gperf_cc_arm_64_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_cc_arm_64 = {
  .name = "cc-arm-64",
  .get = &gperf_cc_arm_64_get,
  .hash = &gperf_cc_arm_64_hash,
  .foreach = &gperf_cc_arm_64_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_cc_arm_64.get)("foo");
	printf ("%s\n", s);
}
#endif
