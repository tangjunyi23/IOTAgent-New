// SDB-CGEN V1.8.3
// gcc -DMAIN=1 netbsd_x86_32.c ; ./a.out > netbsd_x86_32.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"_","0x80"}, 
  {"close","0x80,6,1,"}, 
  {"compat_43_ocreat","0x80,8,2,"}, 
  {"exit","0x80,1,1,"}, 
  {"fork","0x80,2,0,"}, 
  {"link","0x80,9,2,"}, 
  {"open","0x80,5,3,"}, 
  {"read","0x80,3,3,"}, 
  {"syscall","0x80,0,4,"}, 
  {"unlink","0x80,10,1,"}, 
  {"wait4","0x80,7,3,"}, 
  {"write","0x80,4,3,"}, 
  {NULL, NULL}
};
// 0x55b3b3ce52b0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_netbsd_x86_32_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_netbsd_x86_32_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_netbsd_x86_32(x,y) gperf_netbsd_x86_32_hash(x)
const unsigned int gperf_netbsd_x86_32_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_netbsd_x86_32 = {
  .name = "netbsd-x86-32",
  .get = &gperf_netbsd_x86_32_get,
  .hash = &gperf_netbsd_x86_32_hash,
  .foreach = &gperf_netbsd_x86_32_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_netbsd_x86_32.get)("foo");
	printf ("%s\n", s);
}
#endif
