// SDB-CGEN V1.8.3
// gcc -DMAIN=1 wsnmp32.c ; ./a.out > wsnmp32.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"0","SnmpGetTranslateMode"}, 
  {"1","SnmpSetTranslateMode"}, 
  {"100","SnmpStartup"}, 
  {"101","SnmpCleanup"}, 
  {"102","SnmpOpen"}, 
  {"103","SnmpClose"}, 
  {"104","SnmpSendMsg"}, 
  {"105","SnmpRecvMsg"}, 
  {"106","SnmpRegister"}, 
  {"120","SnmpCreateSession"}, 
  {"121","SnmpListen"}, 
  {"122","SnmpCancelMsg"}, 
  {"191","SnmpStartupEx"}, 
  {"192","SnmpCleanupEx"}, 
  {"193","SnmpListenEx"}, 
  {"2","SnmpGetRetransmitMode"}, 
  {"20","SnmpGetVendorInfo"}, 
  {"200","SnmpStrToEntity"}, 
  {"201","SnmpEntityToStr"}, 
  {"202","SnmpFreeEntity"}, 
  {"220","SnmpSetPort"}, 
  {"3","SnmpSetRetransmitMode"}, 
  {"300","SnmpStrToContext"}, 
  {"301","SnmpContextToStr"}, 
  {"302","SnmpFreeContext"}, 
  {"4","SnmpGetTimeout"}, 
  {"400","SnmpCreatePdu"}, 
  {"401","SnmpGetPduData"}, 
  {"402","SnmpSetPduData"}, 
  {"403","SnmpDuplicatePdu"}, 
  {"404","SnmpFreePdu"}, 
  {"5","SnmpSetTimeout"}, 
  {"500","SnmpCreateVbl"}, 
  {"501","SnmpDuplicateVbl"}, 
  {"502","SnmpFreeVbl"}, 
  {"503","SnmpCountVbl"}, 
  {"504","SnmpGetVb"}, 
  {"505","SnmpSetVb"}, 
  {"506","SnmpDeleteVb"}, 
  {"6","SnmpGetRetry"}, 
  {"7","SnmpSetRetry"}, 
  {"8","_SnmpConveyAgentAddress@4"}, 
  {"800","SnmpFreeDescriptor"}, 
  {"801","SnmpEncodeMsg"}, 
  {"802","SnmpDecodeMsg"}, 
  {"803","SnmpStrToOid"}, 
  {"804","SnmpOidToStr"}, 
  {"805","SnmpOidCopy"}, 
  {"806","SnmpOidCompare"}, 
  {"899","SnmpGetLastError"}, 
  {"9","_SnmpSetAgentAddress@4"}, 
  {NULL, NULL}
};
// 0x560818d015b0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_wsnmp32_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_wsnmp32_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_wsnmp32(x,y) gperf_wsnmp32_hash(x)
const unsigned int gperf_wsnmp32_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_wsnmp32 = {
  .name = "wsnmp32",
  .get = &gperf_wsnmp32_get,
  .hash = &gperf_wsnmp32_hash,
  .foreach = &gperf_wsnmp32_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_wsnmp32.get)("foo");
	printf ("%s\n", s);
}
#endif
