// SDB-CGEN V1.8.3
// gcc -DMAIN=1 csmtpapi.c ; ./a.out > csmtpapi.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","DllGetVersion"}, 
  {"100","SmtpInitializeExW"}, 
  {"101","SmtpUninitialize"}, 
  {"197","SmtpAddRecipientA"}, 
  {"198","SmtpAddRecipientW"}, 
  {"199","SmtpAppendMessageA"}, 
  {"200","SmtpAppendMessageW"}, 
  {"201","SmtpAsyncConnectA"}, 
  {"202","SmtpAsyncConnectW"}, 
  {"203","SmtpAttachThread"}, 
  {"204","SmtpAuthenticateA"}, 
  {"205","SmtpAuthenticateW"}, 
  {"206","SmtpCancel"}, 
  {"207","SmtpCloseMessage"}, 
  {"208","SmtpCommandA"}, 
  {"209","SmtpCommandW"}, 
  {"210","SmtpConnectA"}, 
  {"211","SmtpConnectW"}, 
  {"212","SmtpCreateMessageA"}, 
  {"213","SmtpCreateMessageW"}, 
  {"214","SmtpCreateSecurityCredentialsA"}, 
  {"215","SmtpCreateSecurityCredentialsW"}, 
  {"216","SmtpDeleteSecurityCredentialsA"}, 
  {"217","SmtpDeleteSecurityCredentialsW"}, 
  {"218","SmtpDisableEvents"}, 
  {"219","SmtpDisconnect"}, 
  {"220","SmtpEnableEvents"}, 
  {"221","SmtpEnableEventsEx"}, 
  {"222","SmtpExpandAddressA"}, 
  {"223","SmtpExpandAddressW"}, 
  {"224","SmtpFreezeEvents"}, 
  {"225","SmtpGetCurrentDateA"}, 
  {"226","SmtpGetCurrentDateW"}, 
  {"227","SmtpGetDeliveryOptions"}, 
  {"228","SmtpGetErrorStringA"}, 
  {"229","SmtpGetErrorStringW"}, 
  {"230","SmtpGetExtendedOptions"}, 
  {"231","SmtpGetLastError"}, 
  {"232","SmtpGetResultCode"}, 
  {"233","SmtpGetResultStringA"}, 
  {"234","SmtpGetResultStringW"}, 
  {"235","SmtpGetSecurityInformationA"}, 
  {"236","SmtpGetSecurityInformationW"}, 
  {"237","SmtpGetStatus"}, 
  {"238","SmtpGetTimeout"}, 
  {"239","SmtpGetTransferStatus"}, 
  {"240","SmtpIsBlocking"}, 
  {"241","SmtpIsReadable"}, 
  {"242","SmtpIsWritable"}, 
  {"243","SmtpRegisterEvent"}, 
  {"244","SmtpReset"}, 
  {"245","SmtpSendMessageA"}, 
  {"246","SmtpSendMessageW"}, 
  {"247","SmtpSetDeliveryOptions"}, 
  {"248","SmtpSetLastError"}, 
  {"249","SmtpSetTimeout"}, 
  {"250","SmtpVerifyAddressA"}, 
  {"251","SmtpVerifyAddressW"}, 
  {"252","SmtpWrite"}, 
  {"253","SmtpIsConnected"}, 
  {"397","SmtpEnableTraceA"}, 
  {"398","SmtpEnableTraceW"}, 
  {"399","SmtpDisableTrace"}, 
  {"97","SmtpInitializeA"}, 
  {"98","SmtpInitializeW"}, 
  {"99","SmtpInitializeExA"}, 
  {NULL, NULL}
};
// 0x555a0379e310
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_csmtpapi_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_csmtpapi_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_csmtpapi(x,y) gperf_csmtpapi_hash(x)
const unsigned int gperf_csmtpapi_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_csmtpapi = {
  .name = "csmtpapi",
  .get = &gperf_csmtpapi_get,
  .hash = &gperf_csmtpapi_hash,
  .foreach = &gperf_csmtpapi_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_csmtpapi.get)("foo");
	printf ("%s\n", s);
}
#endif
