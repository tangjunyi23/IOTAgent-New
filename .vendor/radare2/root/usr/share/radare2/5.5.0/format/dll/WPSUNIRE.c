// SDB-CGEN V1.8.3
// gcc -DMAIN=1 WPSUNIRE.c ; ./a.out > WPSUNIRE.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"2","HHREOPEN"}, 
  {"3","UIHREWRITE"}, 
  {"5","UIHREEXECUTE"}, 
  {"6","UIHRECLOSE"}, 
  {NULL, NULL}
};
// 0x55f9b68a6670
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_WPSUNIRE_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_WPSUNIRE_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_WPSUNIRE(x,y) gperf_WPSUNIRE_hash(x)
const unsigned int gperf_WPSUNIRE_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_WPSUNIRE = {
  .name = "WPSUNIRE",
  .get = &gperf_WPSUNIRE_get,
  .hash = &gperf_WPSUNIRE_hash,
  .foreach = &gperf_WPSUNIRE_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_WPSUNIRE.get)("foo");
	printf ("%s\n", s);
}
#endif
