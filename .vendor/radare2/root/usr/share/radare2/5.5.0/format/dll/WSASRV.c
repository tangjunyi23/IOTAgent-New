// SDB-CGEN V1.8.3
// gcc -DMAIN=1 WSASRV.c ; ./a.out > WSASRV.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WSANOTIFICATIONCALLBACK"}, 
  {NULL, NULL}
};
// 0x55f999584310
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_WSASRV_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_WSASRV_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_WSASRV(x,y) gperf_WSASRV_hash(x)
const unsigned int gperf_WSASRV_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_WSASRV = {
  .name = "WSASRV",
  .get = &gperf_WSASRV_get,
  .hash = &gperf_WSASRV_hash,
  .foreach = &gperf_WSASRV_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_WSASRV.get)("foo");
	printf ("%s\n", s);
}
#endif
