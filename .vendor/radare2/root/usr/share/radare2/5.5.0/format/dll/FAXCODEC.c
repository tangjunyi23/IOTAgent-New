// SDB-CGEN V1.8.3
// gcc -DMAIN=1 FAXCODEC.c ; ./a.out > FAXCODEC.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"10","FAXCODECINIT"}, 
  {"11","FAXCODECCONVERT"}, 
  {"13","FAXCODECCOUNT"}, 
  {"14","FAXCODECCHANGE"}, 
  {"20","BITREVERSEBUF"}, 
  {"21","INVERTBUF"}, 
  {NULL, NULL}
};
// 0x55c6989c29c0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_FAXCODEC_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_FAXCODEC_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_FAXCODEC(x,y) gperf_FAXCODEC_hash(x)
const unsigned int gperf_FAXCODEC_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_FAXCODEC = {
  .name = "FAXCODEC",
  .get = &gperf_FAXCODEC_get,
  .hash = &gperf_FAXCODEC_hash,
  .foreach = &gperf_FAXCODEC_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_FAXCODEC.get)("foo");
	printf ("%s\n", s);
}
#endif
