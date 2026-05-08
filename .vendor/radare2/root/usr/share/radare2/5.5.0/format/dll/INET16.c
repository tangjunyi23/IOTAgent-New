// SDB-CGEN V1.8.3
// gcc -DMAIN=1 INET16.c ; ./a.out > INET16.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","DLLENTRYPOINT"}, 
  {"2","WIZTHK_THUNKDATA16"}, 
  {"3","WEP"}, 
  {NULL, NULL}
};
// 0x55d00e787560
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_INET16_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_INET16_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_INET16(x,y) gperf_INET16_hash(x)
const unsigned int gperf_INET16_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_INET16 = {
  .name = "INET16",
  .get = &gperf_INET16_get,
  .hash = &gperf_INET16_hash,
  .foreach = &gperf_INET16_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_INET16.get)("foo");
	printf ("%s\n", s);
}
#endif
