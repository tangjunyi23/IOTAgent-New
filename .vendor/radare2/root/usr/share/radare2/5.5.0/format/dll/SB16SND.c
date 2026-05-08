// SDB-CGEN V1.8.3
// gcc -DMAIN=1 SB16SND.c ; ./a.out > SB16SND.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"2","DRIVERPROC"}, 
  {"3","WODMESSAGE"}, 
  {"4","WIDMESSAGE"}, 
  {"5","MODMESSAGE"}, 
  {"6","MIDMESSAGE"}, 
  {"7","AUXMESSAGE"}, 
  {"8","GETDMABUFFERVU"}, 
  {"9","MXDMESSAGE"}, 
  {NULL, NULL}
};
// 0x559ceab0bad0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_SB16SND_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_SB16SND_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_SB16SND(x,y) gperf_SB16SND_hash(x)
const unsigned int gperf_SB16SND_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_SB16SND = {
  .name = "SB16SND",
  .get = &gperf_SB16SND_get,
  .hash = &gperf_SB16SND_hash,
  .foreach = &gperf_SB16SND_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_SB16SND.get)("foo");
	printf ("%s\n", s);
}
#endif
