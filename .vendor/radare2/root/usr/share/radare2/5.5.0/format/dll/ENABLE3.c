// SDB-CGEN V1.8.3
// gcc -DMAIN=1 ENABLE3.c ; ./a.out > ENABLE3.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"2","HELPER_FLASHITEM"}, 
  {"3","HELPER_CLEARHIGHCONTRAST"}, 
  {"4","HELPER_SETHIGHCONTRAST"}, 
  {"5","HELPER_CREATETRANSLATIONTABLE"}, 
  {"6","HELPER_DISPLAYWARNING"}, 
  {"7","HELPER_SPAWNSTATUSAPP"}, 
  {NULL, NULL}
};
// 0x562e0af83980
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_ENABLE3_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_ENABLE3_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_ENABLE3(x,y) gperf_ENABLE3_hash(x)
const unsigned int gperf_ENABLE3_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_ENABLE3 = {
  .name = "ENABLE3",
  .get = &gperf_ENABLE3_get,
  .hash = &gperf_ENABLE3_hash,
  .foreach = &gperf_ENABLE3_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_ENABLE3.get)("foo");
	printf ("%s\n", s);
}
#endif
