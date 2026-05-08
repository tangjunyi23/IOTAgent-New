// SDB-CGEN V1.8.3
// gcc -DMAIN=1 PKPD.c ; ./a.out > PKPD.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"13","BOUNDINGRECTFROMPOINTS"}, 
  {"165","UPDATEPENINFOCACHE"}, 
  {"169","FILLRGPNT"}, 
  {"2","___EXPORTEDSTUB"}, 
  {"2000","FT_PDFTHKTHKCONNECTIONDATA"}, 
  {"2001","PDCTHKCONNECTIONDATASL"}, 
  {"208","CREATEPENDATAEX"}, 
  {"209","DESTROYPENDATA"}, 
  {"210","CREATEPENDATA"}, 
  {"211","GETPENDATAINFO"}, 
  {"212","ADDPOINTSPENDATA"}, 
  {"213","BEGINENUMSTROKES"}, 
  {"214","DRAWPENDATA"}, 
  {"215","METRICSCALEPENDATA"}, 
  {"216","OFFSETPENDATA"}, 
  {"217","ENDENUMSTROKES"}, 
  {"218","DUPLICATEPENDATA"}, 
  {"219","GETPENDATASTROKE"}, 
  {"220","GETPENDATAATTRIBUTES"}, 
  {"221","GETPOINTSFROMPENDATA"}, 
  {"222","RESIZEPENDATA"}, 
  {"223","COMPACTPENDATA"}, 
  {"224","INSERTPENDATA"}, 
  {"225","GETSTROKEATTRIBUTES"}, 
  {"226","SETSTROKEATTRIBUTES"}, 
  {"227","GETSTROKETABLEATTRIBUTES"}, 
  {"228","SETSTROKETABLEATTRIBUTES"}, 
  {"229","DRAWPENDATAEX"}, 
  {"234","INSERTPENDATAPOINTS"}, 
  {"235","INSERTPENDATASTROKE"}, 
  {"236","EXTRACTPENDATAPOINTS"}, 
  {"237","REMOVEPENDATASTROKES"}, 
  {"238","HITTESTPENDATA"}, 
  {"240","COMPRESSPENDATA"}, 
  {"241","TRIMPENDATA"}, 
  {"242","REDISPLAYPENDATA"}, 
  {"243","EXTRACTPENDATASTROKES"}, 
  {"247","PENDATAFROMBUFFER"}, 
  {"248","PENDATATOBUFFER"}, 
  {"581","CREATEPENDATAREGION"}, 
  {"630","ADDINKSETINTERVAL"}, 
  {"631","CREATEINKSET"}, 
  {"632","DESTROYINKSET"}, 
  {"633","GETINKSETINTERVAL"}, 
  {"634","GETINKSETINTERVALCOUNT"}, 
  {NULL, NULL}
};
// 0x565049d25090
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_PKPD_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_PKPD_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_PKPD(x,y) gperf_PKPD_hash(x)
const unsigned int gperf_PKPD_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_PKPD = {
  .name = "PKPD",
  .get = &gperf_PKPD_get,
  .hash = &gperf_PKPD_hash,
  .foreach = &gperf_PKPD_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_PKPD.get)("foo");
	printf ("%s\n", s);
}
#endif
