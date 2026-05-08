// SDB-CGEN V1.8.3
// gcc -DMAIN=1 MIDIMAP.c ; ./a.out > MIDIMAP.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"2","DRIVERPROC"}, 
  {"3","MODMESSAGE"}, 
  {"4","MODMCALLBACK"}, 
  {NULL, NULL}
};
// 0x5594dc462560
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_MIDIMAP_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_MIDIMAP_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_MIDIMAP(x,y) gperf_MIDIMAP_hash(x)
const unsigned int gperf_MIDIMAP_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_MIDIMAP = {
  .name = "MIDIMAP",
  .get = &gperf_MIDIMAP_get,
  .hash = &gperf_MIDIMAP_hash,
  .foreach = &gperf_MIDIMAP_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_MIDIMAP.get)("foo");
	printf ("%s\n", s);
}
#endif
