// SDB-CGEN V1.8.3
// gcc -DMAIN=1 MSDOSD.c ; ./a.out > MSDOSD.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {NULL, NULL}
};
// 0x55596ada3230
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_MSDOSD_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_MSDOSD_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_MSDOSD(x,y) gperf_MSDOSD_hash(x)
const unsigned int gperf_MSDOSD_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_MSDOSD = {
  .name = "MSDOSD",
  .get = &gperf_MSDOSD_get,
  .hash = &gperf_MSDOSD_hash,
  .foreach = &gperf_MSDOSD_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_MSDOSD.get)("foo");
	printf ("%s\n", s);
}
#endif
