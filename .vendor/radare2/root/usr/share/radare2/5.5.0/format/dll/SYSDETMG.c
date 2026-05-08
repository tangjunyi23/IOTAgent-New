// SDB-CGEN V1.8.3
// gcc -DMAIN=1 SYSDETMG.c ; ./a.out > SYSDETMG.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"100","SDSOPEN"}, 
  {"101","SDSCLOSE"}, 
  {"102","SDSDETECT"}, 
  {"103","SDSREGAVOIDRES"}, 
  {"104","SDSGETERRMSG"}, 
  {"105","SDSENUMDETFUNC"}, 
  {"106","SDSGETDETFUNCSTATE"}, 
  {"107","SDSSETDETFUNCSTATE"}, 
  {"108","SDSENUMSKIPPEDCLASSES"}, 
  {"109","SDSSETCLASSSTATE"}, 
  {"2","_WRITEDETLOG"}, 
  {"200","DMSINP"}, 
  {"201","DMSINPW"}, 
  {"202","DMSINPDW"}, 
  {"203","DMSOUTP"}, 
  {"204","DMSOUTPW"}, 
  {"205","DMSOUTPDW"}, 
  {"206","DMSINT86X"}, 
  {"207","DMSREGHW"}, 
  {"208","DMSQUERYIOMEM"}, 
  {"209","DMSQUERYIRQDMA"}, 
  {"210","DMSQUERYVERIFYKEY"}, 
  {"211","DMSQUERYSYSENV"}, 
  {"212","DMSQUERYDOSDEV"}, 
  {"213","DMSQUERYDOSTSR"}, 
  {"214","DMSDETECTIRQ"}, 
  {"215","DMSTIMEOUT"}, 
  {"216","DMSDELAYTICKS"}, 
  {"217","DMSGETMEMALIAS"}, 
  {"218","DMSFREEMEMALIAS"}, 
  {"219","DMSFINDMEMSTR"}, 
  {"220","DMSGETIHVEISADEVSLOTS"}, 
  {"221","DMSGETSLOTEISAID"}, 
  {"222","DMSGETEISAFUNCCONFIG"}, 
  {"223","DMSGETEISACARDCONFIG"}, 
  {"224","DMSGETMCADEVSLOTS"}, 
  {"225","DMSGETSLOTMCAID"}, 
  {"226","DMSCATPATH"}, 
  {"227","DMSGETWINDIR"}, 
  {"228","DMSREGRING0PROC"}, 
  {"229","DMSFREERING0PROC"}, 
  {"230","DMSCALLRMPROC"}, 
  {"231","DMSSETVAR"}, 
  {"232","DMSGETVAR"}, 
  {"233","DMSFINDIOROMSTR"}, 
  {"234","DMSPARSECFGSYSDEV"}, 
  {"235","DMSPARSERES"}, 
  {"236","DMSGETHWND"}, 
  {"237","DMSGETPATHITEM"}, 
  {"238","DMSPARSEINIDEV"}, 
  {"239","DMSPARSEENVDEV"}, 
  {"240","DMSGETWINBOOTPATH"}, 
  {"241","DMSREGAVOIDRES"}, 
  {"242","DMSMAKEVERIFYKEY"}, 
  {"243","DMSREGSKIPLIST"}, 
  {"244","DMSCHECKINT86XCRASH"}, 
  {"245","DMSGETCODEALIAS"}, 
  {"246","DMSFREECODEALIAS"}, 
  {"247","DMSFINDMEMPATTERN"}, 
  {"248","DMSGETCOMPAQMACHINEID"}, 
  {"249","DMSGETPNPBIOSTABLE"}, 
  {"250","DMSMATCHINFLIST"}, 
  {"3","_CATMSG"}, 
  {"4","_ENTERPROC"}, 
  {"5","_EXITPROC"}, 
  {"6","_PRINTTRACE"}, 
  {"7","PROGDLGPROC"}, 
  {"8","___EXPORTEDSTUB"}, 
  {NULL, NULL}
};
// 0x56524e3fa450
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_SYSDETMG_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_SYSDETMG_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_SYSDETMG(x,y) gperf_SYSDETMG_hash(x)
const unsigned int gperf_SYSDETMG_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_SYSDETMG = {
  .name = "SYSDETMG",
  .get = &gperf_SYSDETMG_get,
  .hash = &gperf_SYSDETMG_hash,
  .foreach = &gperf_SYSDETMG_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_SYSDETMG.get)("foo");
	printf ("%s\n", s);
}
#endif
