// SDB-CGEN V1.8.3
// gcc -DMAIN=1 ebcdic37.c ; ./a.out > ebcdic37.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {NULL, NULL}
};
// 0x56043418b1b0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_ebcdic37_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_ebcdic37_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_ebcdic37(x,y) gperf_ebcdic37_hash(x)
const unsigned int gperf_ebcdic37_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_ebcdic37 = {
  .name = "ebcdic37",
  .get = &gperf_ebcdic37_get,
  .hash = &gperf_ebcdic37_hash,
  .foreach = &gperf_ebcdic37_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_ebcdic37.get)("foo");
	printf ("%s\n", s);
}
#endif
