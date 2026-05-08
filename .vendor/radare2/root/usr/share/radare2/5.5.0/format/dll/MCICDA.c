// SDB-CGEN V1.8.3
// gcc -DMAIN=1 MCICDA.c ; ./a.out > MCICDA.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"2","DRIVERPROC"}, 
  {NULL, NULL}
};
// 0x55a848bc23e0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_MCICDA_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_MCICDA_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_MCICDA(x,y) gperf_MCICDA_hash(x)
const unsigned int gperf_MCICDA_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_MCICDA = {
  .name = "MCICDA",
  .get = &gperf_MCICDA_get,
  .hash = &gperf_MCICDA_hash,
  .foreach = &gperf_MCICDA_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_MCICDA.get)("foo");
	printf ("%s\n", s);
}
#endif
