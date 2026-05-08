// SDB-CGEN V1.8.3
// gcc -DMAIN=1 MAINCP16.c ; ./a.out > MAINCP16.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","GETKEYBDDEVICEPAGE"}, 
  {"2","GETMOUSEDEVICEPAGE"}, 
  {"3","GETKEYBDLANGUAGEPAGE"}, 
  {NULL, NULL}
};
// 0x55d9b9d45530
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_MAINCP16_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_MAINCP16_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_MAINCP16(x,y) gperf_MAINCP16_hash(x)
const unsigned int gperf_MAINCP16_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_MAINCP16 = {
  .name = "MAINCP16",
  .get = &gperf_MAINCP16_get,
  .hash = &gperf_MAINCP16_hash,
  .foreach = &gperf_MAINCP16_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_MAINCP16.get)("foo");
	printf ("%s\n", s);
}
#endif
