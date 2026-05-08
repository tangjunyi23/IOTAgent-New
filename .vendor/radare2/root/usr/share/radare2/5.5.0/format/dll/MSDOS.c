// SDB-CGEN V1.8.3
// gcc -DMAIN=1 MSDOS.c ; ./a.out > MSDOS.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {NULL, NULL}
};
// 0x55b3a7949230
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_MSDOS_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_MSDOS_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_MSDOS(x,y) gperf_MSDOS_hash(x)
const unsigned int gperf_MSDOS_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_MSDOS = {
  .name = "MSDOS",
  .get = &gperf_MSDOS_get,
  .hash = &gperf_MSDOS_hash,
  .foreach = &gperf_MSDOS_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_MSDOS.get)("foo");
	printf ("%s\n", s);
}
#endif
