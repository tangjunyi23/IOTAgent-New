// SDB-CGEN V1.8.3
// gcc -DMAIN=1 types_64.c ; ./a.out > types_64.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"gid_t","type"}, 
  {"pid_t","type"}, 
  {"size_t","type"}, 
  {"type.char *.size","64"}, 
  {"type.gid_t","d"}, 
  {"type.gid_t.uid","64"}, 
  {"type.pid_t","d"}, 
  {"type.pid_t.pid","64"}, 
  {"type.size_t","x"}, 
  {"type.size_t.size","64"}, 
  {"type.uid_t","d"}, 
  {"type.uid_t.uid","64"}, 
  {"type.void *.size","64"}, 
  {"uid_t","type"}, 
  {NULL, NULL}
};
// 0x563be46dbf10
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_types_64_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_types_64_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_types_64(x,y) gperf_types_64_hash(x)
const unsigned int gperf_types_64_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_types_64 = {
  .name = "types-64",
  .get = &gperf_types_64_get,
  .hash = &gperf_types_64_hash,
  .foreach = &gperf_types_64_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_types_64.get)("foo");
	printf ("%s\n", s);
}
#endif
