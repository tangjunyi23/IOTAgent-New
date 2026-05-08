// SDB-CGEN V1.8.3
// gcc -DMAIN=1 MCIOLE.c ; ./a.out > MCIOLE.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"10","OLEQUERYOBJPOS"}, 
  {"2","DLLLOADFROMSTREAM"}, 
  {"3","DLLCREATEFROMCLIP"}, 
  {"4","DLLCREATELINKFROMCLIP"}, 
  {"5","DLLCREATEFROMTEMPLATE"}, 
  {"6","DLLCREATE"}, 
  {"7","DLLCREATEFROMFILE"}, 
  {"8","DLLCREATELINKFROMFILE"}, 
  {NULL, NULL}
};
// 0x557bb733dad0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_MCIOLE_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_MCIOLE_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_MCIOLE(x,y) gperf_MCIOLE_hash(x)
const unsigned int gperf_MCIOLE_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_MCIOLE = {
  .name = "MCIOLE",
  .get = &gperf_MCIOLE_get,
  .hash = &gperf_MCIOLE_hash,
  .foreach = &gperf_MCIOLE_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_MCIOLE.get)("foo");
	printf ("%s\n", s);
}
#endif
