// SDB-CGEN V1.8.3
// gcc -DMAIN=1 DCIMAN.c ; ./a.out > DCIMAN.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","DCIOPENPROVIDER"}, 
  {"10","WINWATCHOPEN"}, 
  {"11","WINWATCHCLOSE"}, 
  {"12","WINWATCHDIDSTATUSCHANGE"}, 
  {"13","WINWATCHNOTIFY"}, 
  {"14","WINWATCHGETCLIPLIST"}, 
  {"15","DLLENTRYPOINT"}, 
  {"16","DCITHK_THUNKDATA16"}, 
  {"2","DCICLOSEPROVIDER"}, 
  {"20","GETWINDOWREGIONDATA"}, 
  {"21","GETDCREGIONDATA"}, 
  {"3","DCICREATEPRIMARY"}, 
  {"30","DCIDESTROY"}, 
  {"31","DCIENDACCESS"}, 
  {"32","DCIBEGINACCESS"}, 
  {"33","DCIDRAW"}, 
  {"34","DCISETCLIPLIST"}, 
  {"35","DCISETDESTINATION"}, 
  {"4","DCICREATEOFFSCREEN"}, 
  {"40","DCICREATEPRIMARY32"}, 
  {"5","DCICREATEOVERLAY"}, 
  {"6","DCIENUM"}, 
  {"7","DCISENDCOMMAND"}, 
  {"8","DCISETSRCDESTCLIP"}, 
  {"9","WEP"}, 
  {NULL, NULL}
};
// 0x556d97e9cb40
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_DCIMAN_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_DCIMAN_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_DCIMAN(x,y) gperf_DCIMAN_hash(x)
const unsigned int gperf_DCIMAN_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_DCIMAN = {
  .name = "DCIMAN",
  .get = &gperf_DCIMAN_get,
  .hash = &gperf_DCIMAN_hash,
  .foreach = &gperf_DCIMAN_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_DCIMAN.get)("foo");
	printf ("%s\n", s);
}
#endif
