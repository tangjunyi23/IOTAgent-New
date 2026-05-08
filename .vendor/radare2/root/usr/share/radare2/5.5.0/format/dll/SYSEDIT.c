// SDB-CGEN V1.8.3
// gcc -DMAIN=1 SYSEDIT.c ; ./a.out > SYSEDIT.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","MPFRAMEWNDPROC"}, 
  {"2","MPMDICHILDWNDPROC"}, 
  {"4","FINDDLGPROC"}, 
  {"5","SAVEASDLGPROC"}, 
  {"6","PRINTDLGPROC"}, 
  {"7","ABORTPROC"}, 
  {"8","FILEOPENDLGPROC"}, 
  {NULL, NULL}
};
// 0x55b6c38d4a10
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_SYSEDIT_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_SYSEDIT_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_SYSEDIT(x,y) gperf_SYSEDIT_hash(x)
const unsigned int gperf_SYSEDIT_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_SYSEDIT = {
  .name = "SYSEDIT",
  .get = &gperf_SYSEDIT_get,
  .hash = &gperf_SYSEDIT_hash,
  .foreach = &gperf_SYSEDIT_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_SYSEDIT.get)("foo");
	printf ("%s\n", s);
}
#endif
