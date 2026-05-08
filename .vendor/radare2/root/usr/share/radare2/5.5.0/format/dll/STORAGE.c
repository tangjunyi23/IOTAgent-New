// SDB-CGEN V1.8.3
// gcc -DMAIN=1 STORAGE.c ; ./a.out > STORAGE.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","STGCREATEDOCFILE"}, 
  {"103","DLLGETCLASSOBJECT"}, 
  {"2","STGCREATEDOCFILEONILOCKBYTES"}, 
  {"3","STGOPENSTORAGE"}, 
  {"4","STGOPENSTORAGEONILOCKBYTES"}, 
  {"5","STGISSTORAGEFILE"}, 
  {"6","STGISSTORAGEILOCKBYTES"}, 
  {"7","STGSETTIMES"}, 
  {"8","WEP"}, 
  {"9","___EXPORTEDSTUB"}, 
  {NULL, NULL}
};
// 0x55b282276b30
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_STORAGE_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_STORAGE_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_STORAGE(x,y) gperf_STORAGE_hash(x)
const unsigned int gperf_STORAGE_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_STORAGE = {
  .name = "STORAGE",
  .get = &gperf_STORAGE_get,
  .hash = &gperf_STORAGE_hash,
  .foreach = &gperf_STORAGE_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_STORAGE.get)("foo");
	printf ("%s\n", s);
}
#endif
