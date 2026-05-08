// SDB-CGEN V1.8.3
// gcc -DMAIN=1 MSPCIC.c ; ./a.out > MSPCIC.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","CPLAPPLET"}, 
  {"2","CLASSINSTALL"}, 
  {"3","___EXPORTEDSTUB"}, 
  {"4","ENUMCLASSPROPPAGES"}, 
  {"5","PCMCIA_RUNDLL"}, 
  {"6","EJECTSOCKET"}, 
  {"7","EJECTWARNINGDLG"}, 
  {"999","WEP"}, 
  {NULL, NULL}
};
// 0x55c44a5439d0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_MSPCIC_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_MSPCIC_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_MSPCIC(x,y) gperf_MSPCIC_hash(x)
const unsigned int gperf_MSPCIC_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_MSPCIC = {
  .name = "MSPCIC",
  .get = &gperf_MSPCIC_get,
  .hash = &gperf_MSPCIC_hash,
  .foreach = &gperf_MSPCIC_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_MSPCIC.get)("foo");
	printf ("%s\n", s);
}
#endif
