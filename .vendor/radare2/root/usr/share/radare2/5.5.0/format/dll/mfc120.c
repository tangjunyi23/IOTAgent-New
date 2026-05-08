// SDB-CGEN V1.8.3
// gcc -DMAIN=1 mfc120.c ; ./a.out > mfc120.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {NULL, NULL}
};
// 0x55987a3b5230
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_mfc120_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_mfc120_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_mfc120(x,y) gperf_mfc120_hash(x)
const unsigned int gperf_mfc120_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_mfc120 = {
  .name = "mfc120",
  .get = &gperf_mfc120_get,
  .hash = &gperf_mfc120_hash,
  .foreach = &gperf_mfc120_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_mfc120.get)("foo");
	printf ("%s\n", s);
}
#endif
