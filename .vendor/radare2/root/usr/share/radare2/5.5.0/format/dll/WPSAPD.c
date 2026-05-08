// SDB-CGEN V1.8.3
// gcc -DMAIN=1 WPSAPD.c ; ./a.out > WPSAPD.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"10","ENUMLANGS_W"}, 
  {"13","APDCHECKSUM_A"}, 
  {"14","APDCHECKSUM_W"}, 
  {"2","LIBMAIN"}, 
  {"3","___EXPORTEDSTUB"}, 
  {"4","GETAPDEX_A"}, 
  {"5","GETAPDEX_W"}, 
  {"6","FREEAPD"}, 
  {"7","LOADAPDRESOURCE_A"}, 
  {"8","LOADAPDRESOURCE_W"}, 
  {"9","ENUMLANGS_A"}, 
  {NULL, NULL}
};
// 0x557a2e577ec0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_WPSAPD_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_WPSAPD_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_WPSAPD(x,y) gperf_WPSAPD_hash(x)
const unsigned int gperf_WPSAPD_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_WPSAPD = {
  .name = "WPSAPD",
  .get = &gperf_WPSAPD_get,
  .hash = &gperf_WPSAPD_hash,
  .foreach = &gperf_WPSAPD_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_WPSAPD.get)("foo");
	printf ("%s\n", s);
}
#endif
