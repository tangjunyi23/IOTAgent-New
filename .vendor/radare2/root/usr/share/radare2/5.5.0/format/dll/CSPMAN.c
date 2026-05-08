// SDB-CGEN V1.8.3
// gcc -DMAIN=1 CSPMAN.c ; ./a.out > CSPMAN.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"10","CSPACQUIREDEVICE"}, 
  {"11","CSPLOADDEVICE"}, 
  {"12","CSPDOWNLOADFILE"}, 
  {"13","CSPRELEASEDEVICE"}, 
  {"14","CSPENABLECONTROL"}, 
  {"15","CSPSETCONTROLPARAM"}, 
  {"16","CSPGETCONTROLPARAM"}, 
  {"17","CSPSTARTDEVICE"}, 
  {"18","CSPSTOPDEVICE"}, 
  {"19","CSPPAUSEDEVICE"}, 
  {"2","LIBMAIN"}, 
  {"20","CSPRESTARTDEVICE"}, 
  {"21","CSPGETVULEVEL"}, 
  {"22","CSPSETCODECPARAM"}, 
  {"3","CISAGETVERSION"}, 
  {"30","WDVWAVEINOPEN"}, 
  {"31","WDVWAVEINCLOSE"}, 
  {"32","WDVWAVEOUTOPEN"}, 
  {"33","WDVWAVEOUTCLOSE"}, 
  {"35","WDVGETDMABITSPERSAMPLE"}, 
  {"36","WDVGETSRCBUFSIZE"}, 
  {"37","WDVGETDSTBUFSIZE"}, 
  {"38","WDVRESTARTCSP"}, 
  {"39","WDVGETVULEVEL"}, 
  {"44","WDVISCSPINTERRUPT"}, 
  {"45","WDVSTARTCSP"}, 
  {"46","WDVPAUSECSP"}, 
  {"47","WDVISCSPPRESENT"}, 
  {"48","WDVNEWDEVNODE"}, 
  {"50","EFMSETUPHANDLER"}, 
  {"51","EFMGETHANDLERINFO"}, 
  {"70","CISAENABLEEFFECT"}, 
  {"71","CISADISABLEEFFECT"}, 
  {"72","CISASETEFFECTPARAM"}, 
  {"73","CISAGETEFFECTPARAM"}, 
  {"80","ACVISHWPRESENT"}, 
  {"90","WDVGETXFERADDR"}, 
  {"91","WDVCOPYDMATOAPPEX"}, 
  {"92","WDVCOPYAPPTODMAEX"}, 
  {"93","WDVWAVEOUTRESET"}, 
  {"94","WDVWAVEINRESET"}, 
  {NULL, NULL}
};
// 0x55eee9f3ab00
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_CSPMAN_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_CSPMAN_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_CSPMAN(x,y) gperf_CSPMAN_hash(x)
const unsigned int gperf_CSPMAN_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_CSPMAN = {
  .name = "CSPMAN",
  .get = &gperf_CSPMAN_get,
  .hash = &gperf_CSPMAN_hash,
  .foreach = &gperf_CSPMAN_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_CSPMAN.get)("foo");
	printf ("%s\n", s);
}
#endif
