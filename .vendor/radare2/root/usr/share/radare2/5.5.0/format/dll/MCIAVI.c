// SDB-CGEN V1.8.3
// gcc -DMAIN=1 MCIAVI.c ; ./a.out > MCIAVI.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"2","DRIVERPROC"}, 
  {NULL, NULL}
};
// 0x56433110d3e0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_MCIAVI_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_MCIAVI_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_MCIAVI(x,y) gperf_MCIAVI_hash(x)
const unsigned int gperf_MCIAVI_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_MCIAVI = {
  .name = "MCIAVI",
  .get = &gperf_MCIAVI_get,
  .hash = &gperf_MCIAVI_hash,
  .foreach = &gperf_MCIAVI_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_MCIAVI.get)("foo");
	printf ("%s\n", s);
}
#endif
