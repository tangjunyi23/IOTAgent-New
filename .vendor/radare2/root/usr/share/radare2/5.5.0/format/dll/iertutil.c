// SDB-CGEN V1.8.3
// gcc -DMAIN=1 iertutil.c ; ./a.out > iertutil.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"102","IUriBuilderInternalCreateDomain"}, 
  {"103","ResetIDNLanguageData"}, 
  {"104","ResetIEExtensibility"}, 
  {"105","ResetIERegistrySettings"}, 
  {"106","UriFromHostAndScheme"}, 
  {"107","CreateIUriBuilder"}, 
  {"108","CreateUri"}, 
  {"109","CreateUriFromMultiByteString"}, 
  {"113","CreateUriPriv"}, 
  {"114","CreateUriWithFragment"}, 
  {"115","DllCanUnloadNow"}, 
  {"116","DllGetActivationFactory"}, 
  {"117","DllGetClassObject"}, 
  {"118","FastMimeGetFileExtension"}, 
  {"119","FastMimeGetIsMimeFilterEnabled"}, 
  {"120","FastMimeLookupKnownType"}, 
  {"121","FastMimeSetIsMimeFilterEnabled"}, 
  {"122","GetIUriPriv2"}, 
  {"148","GetIUriPriv"}, 
  {"149","GetPortFromUrlScheme"}, 
  {"178","GetPropertyFromName"}, 
  {"179","GetPropertyName"}, 
  {"180","IEDllLoader"}, 
  {"181","ImpersonateUser"}, 
  {"182","IntlPercentEncodeNormalize"}, 
  {"183","IsDWORDProperty"}, 
  {"184","IsStringProperty"}, 
  {"185","PrivateCoInternetCanonicalizeIUri"}, 
  {"186","PrivateCoInternetCombineIUri"}, 
  {"187","PrivateCoInternetParseIUri"}, 
  {"188","RevertImpersonate"}, 
  {"189","SetEdgeAppProfileForVSDebug"}, 
  {"22","CreateStringHashN"}, 
  {"23","GetIDNSettingsForIE"}, 
  {"27","IEGetFrameUtilExports"}, 
  {"31","IEGetProcessModule"}, 
  {"394","LCIECalculatePackedStringSize"}, 
  {"395","LCIEPackString"}, 
  {"396","LCIEUnpackString"}, 
  {"47","IEGetTabWindowExports"}, 
  {"900","RetiredOrdinal"}, 
  {NULL, NULL}
};
// 0x5615da5decd0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_iertutil_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_iertutil_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_iertutil(x,y) gperf_iertutil_hash(x)
const unsigned int gperf_iertutil_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_iertutil = {
  .name = "iertutil",
  .get = &gperf_iertutil_get,
  .hash = &gperf_iertutil_hash,
  .foreach = &gperf_iertutil_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_iertutil.get)("foo");
	printf ("%s\n", s);
}
#endif
