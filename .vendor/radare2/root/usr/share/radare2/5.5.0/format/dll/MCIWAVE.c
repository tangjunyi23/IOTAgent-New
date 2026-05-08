// SDB-CGEN V1.8.3
// gcc -DMAIN=1 MCIWAVE.c ; ./a.out > MCIWAVE.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"2","DRIVERPROC"}, 
  {NULL, NULL}
};
// 0x563d0e7dd3e0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_MCIWAVE_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_MCIWAVE_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_MCIWAVE(x,y) gperf_MCIWAVE_hash(x)
const unsigned int gperf_MCIWAVE_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_MCIWAVE = {
  .name = "MCIWAVE",
  .get = &gperf_MCIWAVE_get,
  .hash = &gperf_MCIWAVE_hash,
  .foreach = &gperf_MCIWAVE_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_MCIWAVE.get)("foo");
	printf ("%s\n", s);
}
#endif
