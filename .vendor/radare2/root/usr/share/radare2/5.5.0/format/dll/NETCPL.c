// SDB-CGEN V1.8.3
// gcc -DMAIN=1 NETCPL.c ; ./a.out > NETCPL.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"2","CPLAPPLET"}, 
  {"3","___EXPORTEDSTUB"}, 
  {NULL, NULL}
};
// 0x559f38382560
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_NETCPL_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_NETCPL_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_NETCPL(x,y) gperf_NETCPL_hash(x)
const unsigned int gperf_NETCPL_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_NETCPL = {
  .name = "NETCPL",
  .get = &gperf_NETCPL_get,
  .hash = &gperf_NETCPL_hash,
  .foreach = &gperf_NETCPL_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_NETCPL.get)("foo");
	printf ("%s\n", s);
}
#endif
