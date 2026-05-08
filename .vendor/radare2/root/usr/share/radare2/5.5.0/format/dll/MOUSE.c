// SDB-CGEN V1.8.3
// gcc -DMAIN=1 MOUSE.c ; ./a.out > MOUSE.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","INQUIRE"}, 
  {"10","MOUSEREDETECT"}, 
  {"2","ENABLE"}, 
  {"3","DISABLE"}, 
  {"4","MOUSEGETINTVECT"}, 
  {"5","GETSETMOUSEDATA"}, 
  {"6","CPLAPPLET"}, 
  {"7","POWEREVENTPROC"}, 
  {"8","EXTRAPOINTS"}, 
  {"9","WEP"}, 
  {NULL, NULL}
};
// 0x55775f0dab70
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_MOUSE_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_MOUSE_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_MOUSE(x,y) gperf_MOUSE_hash(x)
const unsigned int gperf_MOUSE_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_MOUSE = {
  .name = "MOUSE",
  .get = &gperf_MOUSE_get,
  .hash = &gperf_MOUSE_hash,
  .foreach = &gperf_MOUSE_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_MOUSE.get)("foo");
	printf ("%s\n", s);
}
#endif
