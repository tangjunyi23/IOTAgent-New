// SDB-CGEN V1.8.3
// gcc -DMAIN=1 spec.c ; ./a.out > spec.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"gcc","spec"}, 
  {"spec.gcc.c","char"}, 
  {"spec.gcc.d","int"}, 
  {"spec.gcc.f","float"}, 
  {"spec.gcc.g","double"}, 
  {"spec.gcc.ld","long int"}, 
  {"spec.gcc.lf","double"}, 
  {"spec.gcc.li","long int"}, 
  {"spec.gcc.lld","long long int"}, 
  {"spec.gcc.lli","long long int"}, 
  {"spec.gcc.llu","unsigned long long int"}, 
  {"spec.gcc.lu","unsigned long int"}, 
  {"spec.gcc.p","void *"}, 
  {"spec.gcc.s","const char *"}, 
  {"spec.gcc.u","unsigned int"}, 
  {NULL, NULL}
};
// 0x55a36382ff40
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_spec_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_spec_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_spec(x,y) gperf_spec_hash(x)
const unsigned int gperf_spec_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_spec = {
  .name = "spec",
  .get = &gperf_spec_get,
  .hash = &gperf_spec_hash,
  .foreach = &gperf_spec_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_spec.get)("foo");
	printf ("%s\n", s);
}
#endif
