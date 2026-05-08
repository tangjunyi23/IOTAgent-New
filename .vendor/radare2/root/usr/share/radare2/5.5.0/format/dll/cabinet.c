// SDB-CGEN V1.8.3
// gcc -DMAIN=1 cabinet.c ; ./a.out > cabinet.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","GetDllVersion"}, 
  {"10","FCICreate"}, 
  {"11","FCIAddFile"}, 
  {"12","FCIFlushFolder"}, 
  {"13","FCIFlushCabinet"}, 
  {"14","FCIDestroy"}, 
  {"2","DllGetVersion"}, 
  {"20","FDICreate"}, 
  {"21","FDIIsCabinet"}, 
  {"22","FDICopy"}, 
  {"23","FDIDestroy"}, 
  {"24","FDITruncateCabinet"}, 
  {"3","Extract"}, 
  {"30","CreateCompressor"}, 
  {"31","SetCompressorInformation"}, 
  {"32","QueryCompressorInformation"}, 
  {"33","Compress"}, 
  {"34","ResetCompressor"}, 
  {"35","CloseCompressor"}, 
  {"4","DeleteExtractedFiles"}, 
  {"40","CreateDecompressor"}, 
  {"41","SetDecompressorInformation"}, 
  {"42","QueryDecompressorInformation"}, 
  {"43","Decompress"}, 
  {"44","ResetDecompressor"}, 
  {"45","CloseDecompressor"}, 
  {NULL, NULL}
};
// 0x55bb44acec00
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_cabinet_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_cabinet_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_cabinet(x,y) gperf_cabinet_hash(x)
const unsigned int gperf_cabinet_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_cabinet = {
  .name = "cabinet",
  .get = &gperf_cabinet_get,
  .hash = &gperf_cabinet_hash,
  .foreach = &gperf_cabinet_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_cabinet.get)("foo");
	printf ("%s\n", s);
}
#endif
