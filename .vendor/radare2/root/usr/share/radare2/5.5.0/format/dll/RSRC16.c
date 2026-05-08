// SDB-CGEN V1.8.3
// gcc -DMAIN=1 RSRC16.c ; ./a.out > RSRC16.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","THK_THUNKDATA16"}, 
  {"2","DLLENTRYPOINT"}, 
  {"3","MYGETFREESYSTEMRESOURCES16"}, 
  {"4","WEP"}, 
  {NULL, NULL}
};
// 0x55d7aae365e0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_RSRC16_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_RSRC16_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_RSRC16(x,y) gperf_RSRC16_hash(x)
const unsigned int gperf_RSRC16_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_RSRC16 = {
  .name = "RSRC16",
  .get = &gperf_RSRC16_get,
  .hash = &gperf_RSRC16_hash,
  .foreach = &gperf_RSRC16_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_RSRC16.get)("foo");
	printf ("%s\n", s);
}
#endif
