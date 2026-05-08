// SDB-CGEN V1.8.3
// gcc -DMAIN=1 WINSPL16.c ; ./a.out > WINSPL16.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"13","DEVICEMODE"}, 
  {"90","EXTDEVICEMODE"}, 
  {"91","DEVICECAPABILITIES"}, 
  {"93","ADVANCEDSETUPDIALOG"}, 
  {NULL, NULL}
};
// 0x55a1af8f46c0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_WINSPL16_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_WINSPL16_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_WINSPL16(x,y) gperf_WINSPL16_hash(x)
const unsigned int gperf_WINSPL16_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_WINSPL16 = {
  .name = "WINSPL16",
  .get = &gperf_WINSPL16_get,
  .hash = &gperf_WINSPL16_hash,
  .foreach = &gperf_WINSPL16_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_WINSPL16.get)("foo");
	printf ("%s\n", s);
}
#endif
