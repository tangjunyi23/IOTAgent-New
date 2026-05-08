// SDB-CGEN V1.8.3
// gcc -DMAIN=1 olepro32.c ; ./a.out > olepro32.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"248","OleIconToCursor"}, 
  {"249","OleCreatePropertyFrameIndirect"}, 
  {"250","OleCreatePropertyFrame"}, 
  {"251","OleLoadPicture"}, 
  {"252","OleCreatePictureIndirect"}, 
  {"253","OleCreateFontIndirect"}, 
  {"254","OleTranslateColor"}, 
  {"255","DllCanUnloadNow"}, 
  {"256","DllGetClassObject"}, 
  {"257","DllRegisterServer"}, 
  {"258","DllUnregisterServer"}, 
  {NULL, NULL}
};
// 0x562f910e0db0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_olepro32_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_olepro32_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_olepro32(x,y) gperf_olepro32_hash(x)
const unsigned int gperf_olepro32_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_olepro32 = {
  .name = "olepro32",
  .get = &gperf_olepro32_get,
  .hash = &gperf_olepro32_hash,
  .foreach = &gperf_olepro32_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_olepro32.get)("foo");
	printf ("%s\n", s);
}
#endif
