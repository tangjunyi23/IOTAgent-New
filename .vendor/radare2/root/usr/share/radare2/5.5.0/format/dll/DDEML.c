// SDB-CGEN V1.8.3
// gcc -DMAIN=1 DDEML.c ; ./a.out > DDEML.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"10","DDESETUSERHANDLE"}, 
  {"11","DDECLIENTTRANSACTION"}, 
  {"12","DDEABANDONTRANSACTION"}, 
  {"13","DDEPOSTADVISE"}, 
  {"14","DDECREATEDATAHANDLE"}, 
  {"15","DDEADDDATA"}, 
  {"16","DDEGETDATA"}, 
  {"17","DDEACCESSDATA"}, 
  {"18","DDEUNACCESSDATA"}, 
  {"19","DDEFREEDATAHANDLE"}, 
  {"2","DDEINITIALIZE"}, 
  {"20","DDEGETLASTERROR"}, 
  {"21","DDECREATESTRINGHANDLE"}, 
  {"22","DDEFREESTRINGHANDLE"}, 
  {"23","DDEQUERYSTRING"}, 
  {"24","DDEKEEPSTRINGHANDLE"}, 
  {"26","DDEENABLECALLBACK"}, 
  {"27","DDENAMESERVICE"}, 
  {"28","CLIENTWNDPROC"}, 
  {"29","SERVERWNDPROC"}, 
  {"3","DDEUNINITIALIZE"}, 
  {"30","SUBFRAMEWNDPROC"}, 
  {"31","DMGWNDPROC"}, 
  {"32","CONVLISTWNDPROC"}, 
  {"33","MONITORWNDPROC"}, 
  {"34","DDESENDHOOKPROC"}, 
  {"35","DDEPOSTHOOKPROC"}, 
  {"36","DDECMPSTRINGHANDLES"}, 
  {"37","DDERECONNECT"}, 
  {"38","INITENUM"}, 
  {"39","TERMDLGPROC"}, 
  {"4","DDECONNECTLIST"}, 
  {"40","EMPTYQTIMERPROC"}, 
  {"5","DDEQUERYNEXTSERVER"}, 
  {"6","DDEDISCONNECTLIST"}, 
  {"7","DDECONNECT"}, 
  {"8","DDEDISCONNECT"}, 
  {"9","DDEQUERYCONVINFO"}, 
  {NULL, NULL}
};
// 0x560dbdc69890
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_DDEML_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_DDEML_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_DDEML(x,y) gperf_DDEML_hash(x)
const unsigned int gperf_DDEML_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_DDEML = {
  .name = "DDEML",
  .get = &gperf_DDEML_get,
  .hash = &gperf_DDEML_hash,
  .foreach = &gperf_DDEML_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_DDEML.get)("foo");
	printf ("%s\n", s);
}
#endif
