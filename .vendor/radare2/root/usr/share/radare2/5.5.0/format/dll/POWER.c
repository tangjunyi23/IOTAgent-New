// SDB-CGEN V1.8.3
// gcc -DMAIN=1 POWER.c ; ./a.out > POWER.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"2","DRIVERPROC"}, 
  {"3","NOTIFYOLDAPPLICATIONSENUMPROC"}, 
  {NULL, NULL}
};
// 0x563b65a33570
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_POWER_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_POWER_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_POWER(x,y) gperf_POWER_hash(x)
const unsigned int gperf_POWER_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_POWER = {
  .name = "POWER",
  .get = &gperf_POWER_get,
  .hash = &gperf_POWER_hash,
  .foreach = &gperf_POWER_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_POWER.get)("foo");
	printf ("%s\n", s);
}
#endif
