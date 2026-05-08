// SDB-CGEN V1.8.3
// gcc -DMAIN=1 browseui.c ; ./a.out > browseui.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"104","DllCanUnloadNow"}, 
  {"108","DllGetClassObject"}, 
  {"109","DllGetVersion"}, 
  {NULL, NULL}
};
// 0x556f86709530
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_browseui_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_browseui_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_browseui(x,y) gperf_browseui_hash(x)
const unsigned int gperf_browseui_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_browseui = {
  .name = "browseui",
  .get = &gperf_browseui_get,
  .hash = &gperf_browseui_hash,
  .foreach = &gperf_browseui_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_browseui.get)("foo");
	printf ("%s\n", s);
}
#endif
