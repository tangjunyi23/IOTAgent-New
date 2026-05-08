// SDB-CGEN V1.8.3
// gcc -DMAIN=1 activeds.c ; ./a.out > activeds.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"10","DllCanUnloadNow"}, 
  {"11","DllGetClassObject"}, 
  {"12","ADsSetLastError"}, 
  {"13","ADsGetLastError"}, 
  {"14","AllocADsMem"}, 
  {"15","FreeADsMem"}, 
  {"16","ReallocADsMem"}, 
  {"17","AllocADsStr"}, 
  {"18","FreeADsStr"}, 
  {"19","ReallocADsStr"}, 
  {"20","ADsEncodeBinaryData"}, 
  {"21","PropVariantToAdsType"}, 
  {"22","AdsTypeToPropVariant"}, 
  {"23","AdsFreeAdsValues"}, 
  {"24","ADsDecodeBinaryData"}, 
  {"25","AdsTypeToPropVariant2"}, 
  {"26","PropVariantToAdsType2"}, 
  {"27","ConvertSecDescriptorToVariant"}, 
  {"28","ConvertSecurityDescriptorToSecDes"}, 
  {"29","BinarySDToSecurityDescriptor"}, 
  {"3","ADsGetObject"}, 
  {"30","SecurityDescriptorToBinarySD"}, 
  {"31","ConvertTrusteeToSid"}, 
  {"4","ADsBuildEnumerator"}, 
  {"5","ADsFreeEnumerator"}, 
  {"6","ADsEnumerateNext"}, 
  {"7","ADsBuildVarArrayStr"}, 
  {"8","ADsBuildVarArrayInt"}, 
  {"9","ADsOpenObject"}, 
  {NULL, NULL}
};
// 0x55f9767d1360
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_activeds_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_activeds_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_activeds(x,y) gperf_activeds_hash(x)
const unsigned int gperf_activeds_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_activeds = {
  .name = "activeds",
  .get = &gperf_activeds_get,
  .hash = &gperf_activeds_hash,
  .foreach = &gperf_activeds_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_activeds.get)("foo");
	printf ("%s\n", s);
}
#endif
