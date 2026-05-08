// SDB-CGEN V1.8.3
// gcc -DMAIN=1 RNASETUP.c ; ./a.out > RNASETUP.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"2","RNASETUPCALLBACK"}, 
  {"3","INSTALLDEFAULTDRV"}, 
  {NULL, NULL}
};
// 0x562247c18530
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_RNASETUP_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_RNASETUP_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_RNASETUP(x,y) gperf_RNASETUP_hash(x)
const unsigned int gperf_RNASETUP_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_RNASETUP = {
  .name = "RNASETUP",
  .get = &gperf_RNASETUP_get,
  .hash = &gperf_RNASETUP_hash,
  .foreach = &gperf_RNASETUP_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_RNASETUP.get)("foo");
	printf ("%s\n", s);
}
#endif
