// SDB-CGEN V1.8.3
// gcc -DMAIN=1 UMDM16.c ; ./a.out > UMDM16.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"100","DLLENTRYPOINT"}, 
  {"101","UMDMTHK_THUNKDATA16"}, 
  {"2","OPENMODEM"}, 
  {"3","DUPLICATEMODEMHANDLE"}, 
  {"4","CLOSEMODEM"}, 
  {"5","GETSETMODEMCONFIG"}, 
  {"6","COMMCONFIGDIALOG"}, 
  {"7","GETDEFAULTCOMMCONFIG"}, 
  {"8","SETDEFAULTCOMMCONFIG"}, 
  {"9","LAUNCHMODEMLIGHT"}, 
  {NULL, NULL}
};
// 0x5653df63bdf0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_UMDM16_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_UMDM16_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_UMDM16(x,y) gperf_UMDM16_hash(x)
const unsigned int gperf_UMDM16_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_UMDM16 = {
  .name = "UMDM16",
  .get = &gperf_UMDM16_get,
  .hash = &gperf_UMDM16_hash,
  .foreach = &gperf_UMDM16_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_UMDM16.get)("foo");
	printf ("%s\n", s);
}
#endif
