// SDB-CGEN V1.8.3
// gcc -DMAIN=1 MODEM.c ; ./a.out > MODEM.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","CPLAPPLET"}, 
  {"2","WEP"}, 
  {"3","CLASSINSTALL"}, 
  {"4","INSTALLLOCALCONNECTIONS"}, 
  {NULL, NULL}
};
// 0x55f4e83aa5d0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_MODEM_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_MODEM_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_MODEM(x,y) gperf_MODEM_hash(x)
const unsigned int gperf_MODEM_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_MODEM = {
  .name = "MODEM",
  .get = &gperf_MODEM_get,
  .hash = &gperf_MODEM_hash,
  .foreach = &gperf_MODEM_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_MODEM.get)("foo");
	printf ("%s\n", s);
}
#endif
