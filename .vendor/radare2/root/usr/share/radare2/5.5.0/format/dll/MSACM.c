// SDB-CGEN V1.8.3
// gcc -DMAIN=1 MSACM.c ; ./a.out > MSACM.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"10","ACMDRIVERENUM"}, 
  {"11","ACMDRIVERDETAILS"}, 
  {"12","ACMDRIVERADD"}, 
  {"13","ACMDRIVERREMOVE"}, 
  {"14","ACMDRIVEROPEN"}, 
  {"15","ACMDRIVERCLOSE"}, 
  {"150","ACMAPPLICATIONEXIT"}, 
  {"16","ACMDRIVERMESSAGE"}, 
  {"17","ACMDRIVERID"}, 
  {"175","ACMHUGEPAGELOCK"}, 
  {"176","ACMHUGEPAGEUNLOCK"}, 
  {"18","ACMDRIVERPRIORITY"}, 
  {"2","DRIVERPROC"}, 
  {"200","ACMOPENCONVERSION"}, 
  {"201","ACMCLOSECONVERSION"}, 
  {"202","ACMCONVERT"}, 
  {"203","ACMCHOOSEFORMAT"}, 
  {"3","DLLENTRYPOINT"}, 
  {"30","ACMFORMATTAGDETAILS"}, 
  {"31","ACMFORMATTAGENUM"}, 
  {"4","___EXPORTEDSTUB"}, 
  {"40","ACMFORMATCHOOSE"}, 
  {"41","ACMFORMATDETAILS"}, 
  {"42","ACMFORMATENUM"}, 
  {"45","ACMFORMATSUGGEST"}, 
  {"5","ACMT32C_THUNKDATA16"}, 
  {"50","ACMFILTERTAGDETAILS"}, 
  {"51","ACMFILTERTAGENUM"}, 
  {"60","ACMFILTERCHOOSE"}, 
  {"61","ACMFILTERDETAILS"}, 
  {"62","ACMFILTERENUM"}, 
  {"7","ACMGETVERSION"}, 
  {"70","ACMSTREAMOPEN"}, 
  {"71","ACMSTREAMCLOSE"}, 
  {"72","ACMSTREAMSIZE"}, 
  {"75","ACMSTREAMCONVERT"}, 
  {"76","ACMSTREAMRESET"}, 
  {"77","ACMSTREAMPREPAREHEADER"}, 
  {"78","ACMSTREAMUNPREPAREHEADER"}, 
  {"8","ACMMETRICS"}, 
  {NULL, NULL}
};
// 0x55d8a421bd90
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_MSACM_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_MSACM_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_MSACM(x,y) gperf_MSACM_hash(x)
const unsigned int gperf_MSACM_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_MSACM = {
  .name = "MSACM",
  .get = &gperf_MSACM_get,
  .hash = &gperf_MSACM_hash,
  .foreach = &gperf_MSACM_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_MSACM.get)("foo");
	printf ("%s\n", s);
}
#endif
