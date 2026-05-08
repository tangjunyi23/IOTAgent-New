// SDB-CGEN V1.8.3
// gcc -DMAIN=1 MSACMMAP.c ; ./a.out > MSACMMAP.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"2","DRIVERPROC"}, 
  {"3","___EXPORTEDSTUB"}, 
  {"4","WODMESSAGE"}, 
  {"5","WIDMESSAGE"}, 
  {NULL, NULL}
};
// 0x55a92e1ba670
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_MSACMMAP_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_MSACMMAP_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_MSACMMAP(x,y) gperf_MSACMMAP_hash(x)
const unsigned int gperf_MSACMMAP_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_MSACMMAP = {
  .name = "MSACMMAP",
  .get = &gperf_MSACMMAP_get,
  .hash = &gperf_MSACMMAP_hash,
  .foreach = &gperf_MSACMMAP_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_MSACMMAP.get)("foo");
	printf ("%s\n", s);
}
#endif
