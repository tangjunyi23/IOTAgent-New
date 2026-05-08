// SDB-CGEN V1.8.3
// gcc -DMAIN=1 cc_riscv_64.c ; ./a.out > cc_riscv_64.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"cc.rvg.arg0","a0"}, 
  {"cc.rvg.arg1","a1"}, 
  {"cc.rvg.arg2","a2"}, 
  {"cc.rvg.arg3","a3"}, 
  {"cc.rvg.arg4","a4"}, 
  {"cc.rvg.arg5","a5"}, 
  {"cc.rvg.arg6","a6"}, 
  {"cc.rvg.arg7","a7"}, 
  {"cc.rvg.ret","a0"}, 
  {"default.cc","rvg"}, 
  {"rvg","cc"}, 
  {NULL, NULL}
};
// 0x556ebdb56d10
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_cc_riscv_64_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_cc_riscv_64_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_cc_riscv_64(x,y) gperf_cc_riscv_64_hash(x)
const unsigned int gperf_cc_riscv_64_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_cc_riscv_64 = {
  .name = "cc-riscv-64",
  .get = &gperf_cc_riscv_64_get,
  .hash = &gperf_cc_riscv_64_hash,
  .foreach = &gperf_cc_riscv_64_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_cc_riscv_64.get)("foo");
	printf ("%s\n", s);
}
#endif
