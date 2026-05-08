// SDB-CGEN V1.8.3
// gcc -DMAIN=1 RASAPI16.c ; ./a.out > RASAPI16.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"2","DLLENTRYPOINT"}, 
  {"3","RNA1632_THUNKDATA16"}, 
  {"4","RASGETERRORSTRING"}, 
  {"5","RASENUMCONNECTIONS"}, 
  {"6","RASHANGUP"}, 
  {"7","RASENUMENTRIES"}, 
  {"8","RASGETCONNECTSTATUS"}, 
  {"9","RASDIAL"}, 
  {NULL, NULL}
};
// 0x55b567f52aa0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_RASAPI16_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_RASAPI16_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_RASAPI16(x,y) gperf_RASAPI16_hash(x)
const unsigned int gperf_RASAPI16_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_RASAPI16 = {
  .name = "RASAPI16",
  .get = &gperf_RASAPI16_get,
  .hash = &gperf_RASAPI16_hash,
  .foreach = &gperf_RASAPI16_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_RASAPI16.get)("foo");
	printf ("%s\n", s);
}
#endif
