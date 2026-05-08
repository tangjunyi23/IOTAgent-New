// SDB-CGEN V1.8.3
// gcc -DMAIN=1 WIN32S16.c ; ./a.out > WIN32S16.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"45","UTSELECTOROFFSETTOLINEAR"}, 
  {"46","UTLINEARTOSELECTOROFFSET"}, 
  {NULL, NULL}
};
// 0x558bbf505580
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_WIN32S16_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_WIN32S16_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_WIN32S16(x,y) gperf_WIN32S16_hash(x)
const unsigned int gperf_WIN32S16_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_WIN32S16 = {
  .name = "WIN32S16",
  .get = &gperf_WIN32S16_get,
  .hash = &gperf_WIN32S16_hash,
  .foreach = &gperf_WIN32S16_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_WIN32S16.get)("foo");
	printf ("%s\n", s);
}
#endif
