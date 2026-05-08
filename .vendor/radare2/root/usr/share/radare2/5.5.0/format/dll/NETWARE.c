// SDB-CGEN V1.8.3
// gcc -DMAIN=1 NETWARE.c ; ./a.out > NETWARE.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"1000","NETWAREREQUEST"}, 
  {"1001","PNETWAREREQUEST"}, 
  {"12","WNETGETCONNECTION"}, 
  {"17","WNETADDCONNECTION"}, 
  {"18","WNETCANCELCONNECTION"}, 
  {"520","ALWNETCOMMONDIALOG"}, 
  {NULL, NULL}
};
// 0x559cd54a1990
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_NETWARE_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_NETWARE_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_NETWARE(x,y) gperf_NETWARE_hash(x)
const unsigned int gperf_NETWARE_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_NETWARE = {
  .name = "NETWARE",
  .get = &gperf_NETWARE_get,
  .hash = &gperf_NETWARE_hash,
  .foreach = &gperf_NETWARE_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_NETWARE.get)("foo");
	printf ("%s\n", s);
}
#endif
