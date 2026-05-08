// SDB-CGEN V1.8.3
// gcc -DMAIN=1 SBFM.c ; ./a.out > SBFM.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"2","DRIVERPROC"}, 
  {"3","MODMESSAGE"}, 
  {NULL, NULL}
};
// 0x55bf48024560
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_SBFM_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_SBFM_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_SBFM(x,y) gperf_SBFM_hash(x)
const unsigned int gperf_SBFM_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_SBFM = {
  .name = "SBFM",
  .get = &gperf_SBFM_get,
  .hash = &gperf_SBFM_hash,
  .foreach = &gperf_SBFM_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_SBFM.get)("foo");
	printf ("%s\n", s);
}
#endif
