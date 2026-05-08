// SDB-CGEN V1.8.3
// gcc -DMAIN=1 MSPRINT.c ; ./a.out > MSPRINT.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","DLLENTRYPOINT"}, 
  {"2","MSPTHK_THUNKDATA16"}, 
  {"3","MSPFTHK_THUNKDATA16"}, 
  {"4","CLASSINSTALL"}, 
  {"5","SETUPENTRY"}, 
  {"6","___EXPORTEDSTUB"}, 
  {NULL, NULL}
};
// 0x5555fb92d710
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_MSPRINT_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_MSPRINT_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_MSPRINT(x,y) gperf_MSPRINT_hash(x)
const unsigned int gperf_MSPRINT_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_MSPRINT = {
  .name = "MSPRINT",
  .get = &gperf_MSPRINT_get,
  .hash = &gperf_MSPRINT_hash,
  .foreach = &gperf_MSPRINT_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_MSPRINT.get)("foo");
	printf ("%s\n", s);
}
#endif
