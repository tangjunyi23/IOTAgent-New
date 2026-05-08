// SDB-CGEN V1.8.3
// gcc -DMAIN=1 OLE2CONV.c ; ./a.out > OLE2CONV.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","GETFILTERINFO"}, 
  {"2","IMPORTGR"}, 
  {"3","GETFILTERPREF"}, 
  {"4","IMPORTEMBEDDEDGR"}, 
  {"5","QD2GDI"}, 
  {"6","STATUSPROC"}, 
  {"7","ENUMFONTFUNC"}, 
  {"8","WEP"}, 
  {"9","___EXPORTEDSTUB"}, 
  {NULL, NULL}
};
// 0x55f8c4cdeaa0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_OLE2CONV_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_OLE2CONV_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_OLE2CONV(x,y) gperf_OLE2CONV_hash(x)
const unsigned int gperf_OLE2CONV_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_OLE2CONV = {
  .name = "OLE2CONV",
  .get = &gperf_OLE2CONV_get,
  .hash = &gperf_OLE2CONV_hash,
  .foreach = &gperf_OLE2CONV_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_OLE2CONV.get)("foo");
	printf ("%s\n", s);
}
#endif
