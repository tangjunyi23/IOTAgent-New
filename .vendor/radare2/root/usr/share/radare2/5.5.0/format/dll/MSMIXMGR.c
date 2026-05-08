// SDB-CGEN V1.8.3
// gcc -DMAIN=1 MSMIXMGR.c ; ./a.out > MSMIXMGR.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"10","MIXERGETNUMDEVS"}, 
  {"11","MIXERGETDEVCAPS"}, 
  {"12","MIXERGETID"}, 
  {"13","MIXEROPEN"}, 
  {"14","MIXERCLOSE"}, 
  {"15","MIXERMESSAGE"}, 
  {"16","MIXERGETLINEINFO"}, 
  {"17","MIXERGETLINECONTROLS"}, 
  {"18","MIXERGETCONTROLDETAILS"}, 
  {"19","MIXERSETCONTROLDETAILS"}, 
  {NULL, NULL}
};
// 0x55784d0cfdf0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_MSMIXMGR_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_MSMIXMGR_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_MSMIXMGR(x,y) gperf_MSMIXMGR_hash(x)
const unsigned int gperf_MSMIXMGR_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_MSMIXMGR = {
  .name = "MSMIXMGR",
  .get = &gperf_MSMIXMGR_get,
  .hash = &gperf_MSMIXMGR_hash,
  .foreach = &gperf_MSMIXMGR_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_MSMIXMGR.get)("foo");
	printf ("%s\n", s);
}
#endif
