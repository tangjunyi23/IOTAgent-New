// SDB-CGEN V1.8.3
// gcc -DMAIN=1 NW16.c ; ./a.out > NW16.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"2","___EXPORTEDSTUB"}, 
  {"3","NWSDSCANBINDERYOBJECT"}, 
  {"701","FT_NWNPFTHKTHKCONNECTIONDATA"}, 
  {NULL, NULL}
};
// 0x5625b8acb5b0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_NW16_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_NW16_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_NW16(x,y) gperf_NW16_hash(x)
const unsigned int gperf_NW16_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_NW16 = {
  .name = "NW16",
  .get = &gperf_NW16_get,
  .hash = &gperf_NW16_hash,
  .foreach = &gperf_NW16_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_NW16.get)("foo");
	printf ("%s\n", s);
}
#endif
