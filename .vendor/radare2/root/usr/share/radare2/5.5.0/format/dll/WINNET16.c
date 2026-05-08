// SDB-CGEN V1.8.3
// gcc -DMAIN=1 WINNET16.c ; ./a.out > WINNET16.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"199","WEP"}, 
  {"501","FT_MPRTHKTHKCONNECTIONDATA"}, 
  {NULL, NULL}
};
// 0x55c1a06e73f0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_WINNET16_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_WINNET16_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_WINNET16(x,y) gperf_WINNET16_hash(x)
const unsigned int gperf_WINNET16_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_WINNET16 = {
  .name = "WINNET16",
  .get = &gperf_WINNET16_get,
  .hash = &gperf_WINNET16_hash,
  .foreach = &gperf_WINNET16_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_WINNET16.get)("foo");
	printf ("%s\n", s);
}
#endif
