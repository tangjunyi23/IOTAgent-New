// SDB-CGEN V1.8.3
// gcc -DMAIN=1 csncdapi.c ; ./a.out > csncdapi.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","DllGetVersion"}, 
  {"197","CompressBuffer"}, 
  {"198","CompressFileA"}, 
  {"199","CompressFileW"}, 
  {"200","CompressFileExA"}, 
  {"201","CompressFileExW"}, 
  {"202","DecodeBufferA"}, 
  {"203","DecodeBufferW"}, 
  {"204","DecodeFileA"}, 
  {"205","DecodeFileW"}, 
  {"206","EncodeBufferA"}, 
  {"207","EncodeBufferW"}, 
  {"208","EncodeFileA"}, 
  {"209","EncodeFileW"}, 
  {"210","ExpandBuffer"}, 
  {"211","ExpandFileA"}, 
  {"212","ExpandFileW"}, 
  {"213","ExpandFileExA"}, 
  {"214","ExpandFileExW"}, 
  {NULL, NULL}
};
// 0x5591a52ff470
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_csncdapi_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_csncdapi_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_csncdapi(x,y) gperf_csncdapi_hash(x)
const unsigned int gperf_csncdapi_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_csncdapi = {
  .name = "csncdapi",
  .get = &gperf_csncdapi_get,
  .hash = &gperf_csncdapi_hash,
  .foreach = &gperf_csncdapi_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_csncdapi.get)("foo");
	printf ("%s\n", s);
}
#endif
