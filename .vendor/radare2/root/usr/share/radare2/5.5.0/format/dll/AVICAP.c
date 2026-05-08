// SDB-CGEN V1.8.3
// gcc -DMAIN=1 AVICAP.c ; ./a.out > AVICAP.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"2","CAPCREATECAPTUREWINDOW"}, 
  {"3","CAPGETDRIVERDESCRIPTION"}, 
  {"4","DLLENTRYPOINT"}, 
  {"5","AVICAPF_THUNKDATA16"}, 
  {"6","___EXPORTEDSTUB"}, 
  {"7","CAPWNDPROC"}, 
  {NULL, NULL}
};
// 0x55d888bea960
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_AVICAP_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_AVICAP_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_AVICAP(x,y) gperf_AVICAP_hash(x)
const unsigned int gperf_AVICAP_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_AVICAP = {
  .name = "AVICAP",
  .get = &gperf_AVICAP_get,
  .hash = &gperf_AVICAP_hash,
  .foreach = &gperf_AVICAP_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_AVICAP.get)("foo");
	printf ("%s\n", s);
}
#endif
