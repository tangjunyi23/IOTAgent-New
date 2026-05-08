// SDB-CGEN V1.8.3
// gcc -DMAIN=1 SETUP4.c ; ./a.out > SETUP4.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"200","DIGETCLASSIMAGELIST"}, 
  {"201","DIGETCLASSIMAGEINDEX"}, 
  {"300","DIGETCLASSDEVPROPERTYSHEETS"}, 
  {NULL, NULL}
};
// 0x55a13847e5b0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_SETUP4_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_SETUP4_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_SETUP4(x,y) gperf_SETUP4_hash(x)
const unsigned int gperf_SETUP4_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_SETUP4 = {
  .name = "SETUP4",
  .get = &gperf_SETUP4_get,
  .hash = &gperf_SETUP4_hash,
  .foreach = &gperf_SETUP4_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_SETUP4.get)("foo");
	printf ("%s\n", s);
}
#endif
