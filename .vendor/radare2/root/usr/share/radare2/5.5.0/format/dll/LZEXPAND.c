// SDB-CGEN V1.8.3
// gcc -DMAIN=1 LZEXPAND.c ; ./a.out > LZEXPAND.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","LZCOPY"}, 
  {"10","GETEXPANDEDNAME"}, 
  {"11","WEP"}, 
  {"12","___EXPORTEDSTUB"}, 
  {"2","LZOPENFILE"}, 
  {"3","LZINIT"}, 
  {"4","LZSEEK"}, 
  {"5","LZREAD"}, 
  {"6","LZCLOSE"}, 
  {"7","LZSTART"}, 
  {"8","COPYLZFILE"}, 
  {"9","LZDONE"}, 
  {NULL, NULL}
};
// 0x56031ca84e00
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_LZEXPAND_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_LZEXPAND_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_LZEXPAND(x,y) gperf_LZEXPAND_hash(x)
const unsigned int gperf_LZEXPAND_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_LZEXPAND = {
  .name = "LZEXPAND",
  .get = &gperf_LZEXPAND_get,
  .hash = &gperf_LZEXPAND_hash,
  .foreach = &gperf_LZEXPAND_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_LZEXPAND.get)("foo");
	printf ("%s\n", s);
}
#endif
