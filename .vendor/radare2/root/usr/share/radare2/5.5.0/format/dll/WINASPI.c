// SDB-CGEN V1.8.3
// gcc -DMAIN=1 WINASPI.c ; ./a.out > WINASPI.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","SENDASPICOMMAND"}, 
  {"2","GETASPISUPPORTINFO"}, 
  {"3","INSERTINASPICHAIN"}, 
  {"4","GETASPIDLLVERSION"}, 
  {"5","___EXPORTEDSTUB"}, 
  {NULL, NULL}
};
// 0x558da8b046a0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_WINASPI_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_WINASPI_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_WINASPI(x,y) gperf_WINASPI_hash(x)
const unsigned int gperf_WINASPI_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_WINASPI = {
  .name = "WINASPI",
  .get = &gperf_WINASPI_get,
  .hash = &gperf_WINASPI_hash,
  .foreach = &gperf_WINASPI_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_WINASPI.get)("foo");
	printf ("%s\n", s);
}
#endif
