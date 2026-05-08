// SDB-CGEN V1.8.3
// gcc -DMAIN=1 DISPDIB.c ; ./a.out > DISPDIB.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","DISPLAYDIB"}, 
  {"2","DISPLAYDIBEX"}, 
  {"3","WEP"}, 
  {NULL, NULL}
};
// 0x56367ec8a560
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_DISPDIB_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_DISPDIB_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_DISPDIB(x,y) gperf_DISPDIB_hash(x)
const unsigned int gperf_DISPDIB_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_DISPDIB = {
  .name = "DISPDIB",
  .get = &gperf_DISPDIB_get,
  .hash = &gperf_DISPDIB_hash,
  .foreach = &gperf_DISPDIB_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_DISPDIB.get)("foo");
	printf ("%s\n", s);
}
#endif
