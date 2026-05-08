// SDB-CGEN V1.8.3
// gcc -DMAIN=1 VER.c ; ./a.out > VER.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","DLLENTRYPOINT"}, 
  {"10","VERLANGUAGENAME"}, 
  {"11","VERQUERYVALUE"}, 
  {"2","GETFILERESOURCESIZE"}, 
  {"20","GETFILEVERSIONINFORAW"}, 
  {"21","VERFTHK_THUNKDATA16"}, 
  {"22","VERTHKSL_THUNKDATA16"}, 
  {"3","GETFILERESOURCE"}, 
  {"6","GETFILEVERSIONINFOSIZE"}, 
  {"7","GETFILEVERSIONINFO"}, 
  {"8","VERFINDFILE"}, 
  {"9","VERINSTALLFILE"}, 
  {NULL, NULL}
};
// 0x55d937b85e80
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_VER_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_VER_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_VER(x,y) gperf_VER_hash(x)
const unsigned int gperf_VER_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_VER = {
  .name = "VER",
  .get = &gperf_VER_get,
  .hash = &gperf_VER_hash,
  .foreach = &gperf_VER_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_VER.get)("foo");
	printf ("%s\n", s);
}
#endif
