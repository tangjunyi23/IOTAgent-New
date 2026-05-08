// SDB-CGEN V1.8.3
// gcc -DMAIN=1 olesvr32.c ; ./a.out > olesvr32.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"10","OleSavedServerDoc"}, 
  {"11","OleRevokeObject"}, 
  {"12","OleQueryServerVersion"}, 
  {"2","OleRegisterServer"}, 
  {"21","SrvrWndProc"}, 
  {"22","DocWndProc"}, 
  {"23","ItemWndProc"}, 
  {"24","SendDataMsg"}, 
  {"25","FindItemWnd"}, 
  {"26","ItemCallBack"}, 
  {"27","TerminateClients"}, 
  {"28","TerminateDocClients"}, 
  {"29","DeleteClientInfo"}, 
  {"3","OleRevokeServer"}, 
  {"30","SendRenameMsg"}, 
  {"31","EnumForTerminate"}, 
  {"4","OleBlockServer"}, 
  {"5","OleUnblockServer"}, 
  {"6","OleRegisterServerDoc"}, 
  {"7","OleRevokeServerDoc"}, 
  {"8","OleRenameServerDoc"}, 
  {"9","OleRevertServerDoc"}, 
  {NULL, NULL}
};
// 0x558b01789a00
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_olesvr32_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_olesvr32_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_olesvr32(x,y) gperf_olesvr32_hash(x)
const unsigned int gperf_olesvr32_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_olesvr32 = {
  .name = "olesvr32",
  .get = &gperf_olesvr32_get,
  .hash = &gperf_olesvr32_hash,
  .foreach = &gperf_olesvr32_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_olesvr32.get)("foo");
	printf ("%s\n", s);
}
#endif
