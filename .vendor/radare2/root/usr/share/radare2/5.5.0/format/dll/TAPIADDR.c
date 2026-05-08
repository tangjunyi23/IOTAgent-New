// SDB-CGEN V1.8.3
// gcc -DMAIN=1 TAPIADDR.c ; ./a.out > TAPIADDR.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"10","TAPIADDR_INICHANGED"}, 
  {"100","GETDIALANDDISPLAYDLG"}, 
  {"2","TAPIADDR_SETCURRENTLOCATION"}, 
  {"3","TAPIADDR_SETTOLLLIST"}, 
  {"4","TAPIADDR_TRANSLATEADDRESS"}, 
  {"5","TAPIADDR_GETTRANSLATECAPS"}, 
  {"6","LGETCOUNTRYCODEFROMID"}, 
  {"7","___EXPORTEDSTUB"}, 
  {"8","GETTOLLPREFIX"}, 
  {NULL, NULL}
};
// 0x5576550ecb10
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_TAPIADDR_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_TAPIADDR_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_TAPIADDR(x,y) gperf_TAPIADDR_hash(x)
const unsigned int gperf_TAPIADDR_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_TAPIADDR = {
  .name = "TAPIADDR",
  .get = &gperf_TAPIADDR_get,
  .hash = &gperf_TAPIADDR_hash,
  .foreach = &gperf_TAPIADDR_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_TAPIADDR.get)("foo");
	printf ("%s\n", s);
}
#endif
