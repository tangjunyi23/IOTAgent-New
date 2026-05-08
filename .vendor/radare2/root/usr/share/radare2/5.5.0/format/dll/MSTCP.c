// SDB-CGEN V1.8.3
// gcc -DMAIN=1 MSTCP.c ; ./a.out > MSTCP.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"10","TCPNDIPROC"}, 
  {"2","___EXPORTEDSTUB"}, 
  {NULL, NULL}
};
// 0x55650cd1e5b0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_MSTCP_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_MSTCP_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_MSTCP(x,y) gperf_MSTCP_hash(x)
const unsigned int gperf_MSTCP_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_MSTCP = {
  .name = "MSTCP",
  .get = &gperf_MSTCP_get,
  .hash = &gperf_MSTCP_hash,
  .foreach = &gperf_MSTCP_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_MSTCP.get)("foo");
	printf ("%s\n", s);
}
#endif
