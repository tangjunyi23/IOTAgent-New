// SDB-CGEN V1.8.3
// gcc -DMAIN=1 IOSCLASS.c ; ./a.out > IOSCLASS.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","ENUMPROPPAGES"}, 
  {"2","CDROMCLASSINSTALL"}, 
  {"3","SCSIENUMPROPPAGES"}, 
  {"999","WEP"}, 
  {NULL, NULL}
};
// 0x55ed0188b600
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_IOSCLASS_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_IOSCLASS_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_IOSCLASS(x,y) gperf_IOSCLASS_hash(x)
const unsigned int gperf_IOSCLASS_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_IOSCLASS = {
  .name = "IOSCLASS",
  .get = &gperf_IOSCLASS_get,
  .hash = &gperf_IOSCLASS_hash,
  .foreach = &gperf_IOSCLASS_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_IOSCLASS.get)("foo");
	printf ("%s\n", s);
}
#endif
