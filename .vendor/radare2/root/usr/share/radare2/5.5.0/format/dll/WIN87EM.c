// SDB-CGEN V1.8.3
// gcc -DMAIN=1 WIN87EM.c ; ./a.out > WIN87EM.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","__FPMATH"}, 
  {"2","WEP"}, 
  {"3","__WIN87EMRESTORE"}, 
  {"4","__WIN87EMSAVE"}, 
  {"5","__WIN87EMINFO"}, 
  {NULL, NULL}
};
// 0x562f2d2c36a0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_WIN87EM_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_WIN87EM_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_WIN87EM(x,y) gperf_WIN87EM_hash(x)
const unsigned int gperf_WIN87EM_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_WIN87EM = {
  .name = "WIN87EM",
  .get = &gperf_WIN87EM_get,
  .hash = &gperf_WIN87EM_hash,
  .foreach = &gperf_WIN87EM_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_WIN87EM.get)("foo");
	printf ("%s\n", s);
}
#endif
