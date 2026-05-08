// SDB-CGEN V1.8.3
// gcc -DMAIN=1 ppc.c ; ./a.out > ppc.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {NULL, NULL}
};
// 0x5634d7dfb1b0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_ppc_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_ppc_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_ppc(x,y) gperf_ppc_hash(x)
const unsigned int gperf_ppc_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_ppc = {
  .name = "ppc",
  .get = &gperf_ppc_get,
  .hash = &gperf_ppc_hash,
  .foreach = &gperf_ppc_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_ppc.get)("foo");
	printf ("%s\n", s);
}
#endif
