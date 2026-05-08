// SDB-CGEN V1.8.3
// gcc -DMAIN=1 MCIMIDI.c ; ./a.out > MCIMIDI.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","DRIVERPROC"}, 
  {NULL, NULL}
};
// 0x55bef1389310
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_MCIMIDI_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_MCIMIDI_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_MCIMIDI(x,y) gperf_MCIMIDI_hash(x)
const unsigned int gperf_MCIMIDI_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_MCIMIDI = {
  .name = "MCIMIDI",
  .get = &gperf_MCIMIDI_get,
  .hash = &gperf_MCIMIDI_hash,
  .foreach = &gperf_MCIMIDI_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_MCIMIDI.get)("foo");
	printf ("%s\n", s);
}
#endif
