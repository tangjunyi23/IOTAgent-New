// SDB-CGEN V1.8.3
// gcc -DMAIN=1 NETDI.c ; ./a.out > NETDI.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"100","NETCLASSDLG"}, 
  {"101","SELECTCLASSDLG"}, 
  {"102","MOREINFODLG"}, 
  {"103","HWRESDLG"}, 
  {"104","SHAREDLGPROC"}, 
  {"12","NDIISNDI"}, 
  {"13","NDICALLINSTALLER"}, 
  {"14","DEFNDIPROC"}, 
  {"15","NDIBIND"}, 
  {"16","NDIUNBIND"}, 
  {"17","NDIISBOUND"}, 
  {"18","NDIVALIDATE"}, 
  {"19","NDIINSTALL"}, 
  {"2","CLASSINSTALL"}, 
  {"200","NDIADDPROPERTYPAGES"}, 
  {"21","NDIPROPERTIES"}, 
  {"22","NDIREMOVE"}, 
  {"24","NDIGETTEXT"}, 
  {"25","NDISETTEXT"}, 
  {"26","NDIGETDEVICEINFO"}, 
  {"27","NDIFINDNDI"}, 
  {"28","NDIGETCLASS"}, 
  {"29","NDIGETPROPERTIES"}, 
  {"3","___EXPORTEDSTUB"}, 
  {"30","NDISETPROPERTIES"}, 
  {"31","NDIGETOWNERWINDOW"}, 
  {"32","NDIGETFIRST"}, 
  {"33","NDIGETNEXT"}, 
  {"34","NDITEST"}, 
  {"35","NDIREGOPENKEY"}, 
  {"37","NDIGETBINDING"}, 
  {"38","NDIREGQUERYVALUE"}, 
  {"39","NDIREGSETVALUE"}, 
  {"40","NDICOMPAREINTERFACE"}, 
  {"41","NDIGETINTERFACE"}, 
  {"42","NDIADDINTERFACE"}, 
  {"43","NDIREMOVEINTERFACE"}, 
  {"44","NDIREGCREATEKEY"}, 
  {"45","NDIGETDEVICEID"}, 
  {"46","NDIGETFLAGS"}, 
  {"47","NDIREGDELETEVALUE"}, 
  {"48","NDICPLPROPERTIES"}, 
  {"49","ENUMPROPPAGES"}, 
  {"50","NDICLEANUPB4REBOOT"}, 
  {"51","SBSTREECOPYNWBOOTDISK"}, 
  {"60","MSCLIENTNDIPROC"}, 
  {"61","NWCLIENTNDIPROC"}, 
  {"62","NWLINKNDIPROC"}, 
  {"63","THIRDPARTYCLIENTNDIPROC"}, 
  {"64","IBMDLCNDIPROC"}, 
  {"70","NDIFINDDEFNDI"}, 
  {"71","NDISETDEFNDI"}, 
  {"72","NDICHOOSECANDIDATEDEFNDI"}, 
  {"73","NDINEEDREBOOT"}, 
  {"74","CREATENDIFROMDEVICEID"}, 
  {"75","INITCHANGEPARAMETERS"}, 
  {"76","CHANGELINE"}, 
  {"77","NW_ISIPXMONOONLYCARD"}, 
  {NULL, NULL}
};
// 0x5642d5cd74f0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_NETDI_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_NETDI_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_NETDI(x,y) gperf_NETDI_hash(x)
const unsigned int gperf_NETDI_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_NETDI = {
  .name = "NETDI",
  .get = &gperf_NETDI_get,
  .hash = &gperf_NETDI_hash,
  .foreach = &gperf_NETDI_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_NETDI.get)("foo");
	printf ("%s\n", s);
}
#endif
