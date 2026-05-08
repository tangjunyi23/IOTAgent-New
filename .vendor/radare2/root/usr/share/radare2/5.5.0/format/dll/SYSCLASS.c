// SDB-CGEN V1.8.3
// gcc -DMAIN=1 SYSCLASS.c ; ./a.out > SYSCLASS.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","ENUMPROPPAGES"}, 
  {"2","DMAPROBLEMHANDLER"}, 
  {"3","CLASSINSTALL"}, 
  {"4","DMAENUMPROPPAGES"}, 
  {"6","FPUENUMPROPPAGES"}, 
  {"7","APMENUMPROPPAGES"}, 
  {"999","WEP"}, 
  {NULL, NULL}
};
// 0x5648a15b3930
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_SYSCLASS_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_SYSCLASS_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_SYSCLASS(x,y) gperf_SYSCLASS_hash(x)
const unsigned int gperf_SYSCLASS_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_SYSCLASS = {
  .name = "SYSCLASS",
  .get = &gperf_SYSCLASS_get,
  .hash = &gperf_SYSCLASS_hash,
  .foreach = &gperf_SYSCLASS_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_SYSCLASS.get)("foo");
	printf ("%s\n", s);
}
#endif
