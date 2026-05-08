// SDB-CGEN V1.8.3
// gcc -DMAIN=1 MSJSTICK.c ; ./a.out > MSJSTICK.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","DRIVERPROC"}, 
  {"2","WEP"}, 
  {NULL, NULL}
};
// 0x561270d04410
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_MSJSTICK_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_MSJSTICK_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_MSJSTICK(x,y) gperf_MSJSTICK_hash(x)
const unsigned int gperf_MSJSTICK_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_MSJSTICK = {
  .name = "MSJSTICK",
  .get = &gperf_MSJSTICK_get,
  .hash = &gperf_MSJSTICK_hash,
  .foreach = &gperf_MSJSTICK_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_MSJSTICK.get)("foo");
	printf ("%s\n", s);
}
#endif
