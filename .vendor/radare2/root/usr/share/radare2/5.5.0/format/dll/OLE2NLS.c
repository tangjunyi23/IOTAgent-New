// SDB-CGEN V1.8.3
// gcc -DMAIN=1 OLE2NLS.c ; ./a.out > OLE2NLS.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","GETUSERDEFAULTLCID"}, 
  {"10","WEP"}, 
  {"11","LIBMAIN"}, 
  {"12","NOTIFYWINDOWPROC"}, 
  {"2","GETSYSTEMDEFAULTLCID"}, 
  {"3","GETUSERDEFAULTLANGID"}, 
  {"4","GETSYSTEMDEFAULTLANGID"}, 
  {"5","GETLOCALEINFOA"}, 
  {"6","LCMAPSTRINGA"}, 
  {"7","GETSTRINGTYPEA"}, 
  {"8","COMPARESTRINGA"}, 
  {"9","REGISTERNLSINFOCHANGED"}, 
  {NULL, NULL}
};
// 0x55f48db11e30
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_OLE2NLS_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_OLE2NLS_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_OLE2NLS(x,y) gperf_OLE2NLS_hash(x)
const unsigned int gperf_OLE2NLS_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_OLE2NLS = {
  .name = "OLE2NLS",
  .get = &gperf_OLE2NLS_get,
  .hash = &gperf_OLE2NLS_hash,
  .foreach = &gperf_OLE2NLS_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_OLE2NLS.get)("foo");
	printf ("%s\n", s);
}
#endif
