// SDB-CGEN V1.8.3
// gcc -DMAIN=1 borlndmm.c ; ./a.out > borlndmm.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","GetAllocMemSize"}, 
  {"10","@Borlndmm@SysAllocMem$qqri"}, 
  {"11","@Borlndmm@SysReallocMem$qqrpvi"}, 
  {"12","@Borlndmm@SysFreeMem$qqrpv"}, 
  {"13","@Borlndmm@SysGetMem$qqri"}, 
  {"14","@Borlndmm@HeapRelease$qqrv"}, 
  {"15","@Borlndmm@HeapAddRef$qqrv"}, 
  {"2","GetAllocMemCount"}, 
  {"3","GetHeapStatus"}, 
  {"4","DumpBlocks"}, 
  {"5","ReallocMemory"}, 
  {"6","FreeMemory"}, 
  {"7","GetMemory"}, 
  {"8","@Borlndmm@SysUnregisterExpectedMemoryLeak$qqrpi"}, 
  {"9","@Borlndmm@SysRegisterExpectedMemoryLeak$qqrpi"}, 
  {NULL, NULL}
};
// 0x561c1fd55090
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_borlndmm_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_borlndmm_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_borlndmm(x,y) gperf_borlndmm_hash(x)
const unsigned int gperf_borlndmm_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_borlndmm = {
  .name = "borlndmm",
  .get = &gperf_borlndmm_get,
  .hash = &gperf_borlndmm_hash,
  .foreach = &gperf_borlndmm_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_borlndmm.get)("foo");
	printf ("%s\n", s);
}
#endif
