// SDB-CGEN V1.8.3
// gcc -DMAIN=1 types_32.c ; ./a.out > types_32.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"gid_t","type"}, 
  {"pid_t","type"}, 
  {"size_t","type"}, 
  {"type.char *.size","32"}, 
  {"type.gid_t","d"}, 
  {"type.gid_t.uid","32"}, 
  {"type.pid_t","d"}, 
  {"type.pid_t.pid","32"}, 
  {"type.size_t","d"}, 
  {"type.size_t.size","32"}, 
  {"type.uid_t","d"}, 
  {"type.uid_t.uid","32"}, 
  {"type.void *.size","32"}, 
  {"uid_t","type"}, 
  {NULL, NULL}
};
// 0x5616f4faaf10
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_types_32_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_types_32_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_types_32(x,y) gperf_types_32_hash(x)
const unsigned int gperf_types_32_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_types_32 = {
  .name = "types-32",
  .get = &gperf_types_32_get,
  .hash = &gperf_types_32_hash,
  .foreach = &gperf_types_32_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_types_32.get)("foo");
	printf ("%s\n", s);
}
#endif
