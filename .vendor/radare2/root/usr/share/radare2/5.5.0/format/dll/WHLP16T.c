// SDB-CGEN V1.8.3
// gcc -DMAIN=1 WHLP16T.c ; ./a.out > WHLP16T.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","THK_THUNKDATA16"}, 
  {"10","MAKEINFORMCALL"}, 
  {"11","THUNKEMBEDCREATE"}, 
  {"12","GETMODULEFILENAME16"}, 
  {"2","DLLENTRYPOINT"}, 
  {"3","THKR_THUNKDATA16"}, 
  {"4","WEP"}, 
  {"5","IMTDISPATCHPROC"}, 
  {"8","MAKECALLDATA"}, 
  {"9","MAKECALLSTR"}, 
  {NULL, NULL}
};
// 0x55aa171ddba0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_WHLP16T_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_WHLP16T_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_WHLP16T(x,y) gperf_WHLP16T_hash(x)
const unsigned int gperf_WHLP16T_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_WHLP16T = {
  .name = "WHLP16T",
  .get = &gperf_WHLP16T_get,
  .hash = &gperf_WHLP16T_hash,
  .foreach = &gperf_WHLP16T_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_WHLP16T.get)("foo");
	printf ("%s\n", s);
}
#endif
