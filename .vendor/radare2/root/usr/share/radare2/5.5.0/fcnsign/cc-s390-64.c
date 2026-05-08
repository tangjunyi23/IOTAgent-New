// SDB-CGEN V1.8.3
// gcc -DMAIN=1 cc_s390_64.c ; ./a.out > cc_s390_64.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"cc.sysz.arg0","r2"}, 
  {"cc.sysz.arg1","r3"}, 
  {"cc.sysz.arg2","r4"}, 
  {"cc.sysz.arg3","r5"}, 
  {"cc.sysz.arg4","r6"}, 
  {"cc.sysz.ret","r2"}, 
  {"default.cc","sysz"}, 
  {"sysz","cc"}, 
  {NULL, NULL}
};
// 0x55f42ecd0990
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_cc_s390_64_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_cc_s390_64_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_cc_s390_64(x,y) gperf_cc_s390_64_hash(x)
const unsigned int gperf_cc_s390_64_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_cc_s390_64 = {
  .name = "cc-s390-64",
  .get = &gperf_cc_s390_64_get,
  .hash = &gperf_cc_s390_64_hash,
  .foreach = &gperf_cc_s390_64_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_cc_s390_64.get)("foo");
	printf ("%s\n", s);
}
#endif
