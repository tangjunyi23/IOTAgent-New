// SDB-CGEN V1.8.3
// gcc -DMAIN=1 dsound.c ; ./a.out > dsound.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","DirectSoundCreate"}, 
  {"10","DirectSoundFullDuplexCreate"}, 
  {"11","DirectSoundCreate8"}, 
  {"12","DirectSoundCaptureCreate8"}, 
  {"2","DirectSoundEnumerateA"}, 
  {"3","DirectSoundEnumerateW"}, 
  {"4","DllCanUnloadNow"}, 
  {"5","DllGetClassObject"}, 
  {"6","DirectSoundCaptureCreate"}, 
  {"7","DirectSoundCaptureEnumerateA"}, 
  {"8","DirectSoundCaptureEnumerateW"}, 
  {"9","GetDeviceID"}, 
  {NULL, NULL}
};
// 0x558f6085ce80
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_dsound_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_dsound_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_dsound(x,y) gperf_dsound_hash(x)
const unsigned int gperf_dsound_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_dsound = {
  .name = "dsound",
  .get = &gperf_dsound_get,
  .hash = &gperf_dsound_hash,
  .foreach = &gperf_dsound_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_dsound.get)("foo");
	printf ("%s\n", s);
}
#endif
