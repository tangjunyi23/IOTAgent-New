// SDB-CGEN V1.8.3
// gcc -DMAIN=1 types_android.c ; ./a.out > types_android.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {NULL, NULL}
};
// 0x5634947321b0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_types_android_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_types_android_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_types_android(x,y) gperf_types_android_hash(x)
const unsigned int gperf_types_android_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_types_android = {
  .name = "types-android",
  .get = &gperf_types_android_get,
  .hash = &gperf_types_android_hash,
  .foreach = &gperf_types_android_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_types_android.get)("foo");
	printf ("%s\n", s);
}
#endif
