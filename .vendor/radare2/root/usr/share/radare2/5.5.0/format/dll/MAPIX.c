// SDB-CGEN V1.8.3
// gcc -DMAIN=1 MAPIX.c ; ./a.out > MAPIX.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"11","MAPILOGON"}, 
  {"111","MAPILOGONA"}, 
  {"116","_MAPIADMINPROFILES"}, 
  {"16","MAPIADMINPROFILES"}, 
  {"18","MAPIFREEBUFFER"}, 
  {"2","___EXPORTEDSTUB"}, 
  {"290","_MAPIALLOCATEBUFFER"}, 
  {"291","MAPIALLOCATEBUFFER"}, 
  {"3","MAPIINITIALIZE"}, 
  {"300","_MAPIALLOCATEMORE"}, 
  {"301","MAPIALLOCATEMORE"}, 
  {"5","MAPIUNINITIALIZE"}, 
  {NULL, NULL}
};
// 0x55f2ca513f80
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_MAPIX_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_MAPIX_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_MAPIX(x,y) gperf_MAPIX_hash(x)
const unsigned int gperf_MAPIX_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_MAPIX = {
  .name = "MAPIX",
  .get = &gperf_MAPIX_get,
  .hash = &gperf_MAPIX_hash,
  .foreach = &gperf_MAPIX_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_MAPIX.get)("foo");
	printf ("%s\n", s);
}
#endif
