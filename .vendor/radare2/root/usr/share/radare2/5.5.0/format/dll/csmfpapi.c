// SDB-CGEN V1.8.3
// gcc -DMAIN=1 csmfpapi.c ; ./a.out > csmfpapi.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","DllGetVersion"}, 
  {"100","FtpInitializeExW"}, 
  {"101","FtpUninitialize"}, 
  {"197","FtpAccountA"}, 
  {"198","FtpAccountW"}, 
  {"199","FtpAllocate"}, 
  {"200","FtpAsyncConnectA"}, 
  {"201","FtpAsyncConnectW"}, 
  {"202","FtpAsyncProxyConnectA"}, 
  {"203","FtpAsyncProxyConnectW"}, 
  {"204","FtpAttachThread"}, 
  {"205","FtpCancel"}, 
  {"206","FtpChangeDirectoryA"}, 
  {"207","FtpChangeDirectoryW"}, 
  {"208","FtpChangeDirectoryUp"}, 
  {"209","FtpCloseDirectory"}, 
  {"210","FtpCloseFile"}, 
  {"211","FtpCommandA"}, 
  {"212","FtpCommandW"}, 
  {"213","FtpConnectA"}, 
  {"214","FtpConnectW"}, 
  {"215","FtpCreateDirectoryA"}, 
  {"216","FtpCreateDirectoryW"}, 
  {"217","FtpCreateSecurityCredentialsA"}, 
  {"218","FtpCreateSecurityCredentialsW"}, 
  {"219","FtpDeleteFileA"}, 
  {"220","FtpDeleteFileW"}, 
  {"221","FtpDeleteSecurityCredentialsA"}, 
  {"222","FtpDeleteSecurityCredentialsW"}, 
  {"223","FtpDisableEvents"}, 
  {"224","FtpDisconnect"}, 
  {"225","FtpEnableEvents"}, 
  {"226","FtpEnableEventsEx"}, 
  {"227","FtpEnableFeature"}, 
  {"228","FtpEndOfFile"}, 
  {"229","FtpFileListA"}, 
  {"230","FtpFileListW"}, 
  {"231","FtpFreezeEvents"}, 
  {"232","FtpGetBufferSize"}, 
  {"233","FtpGetDataA"}, 
  {"234","FtpGetDataW"}, 
  {"235","FtpGetDirectoryA"}, 
  {"236","FtpGetDirectoryFormat"}, 
  {"237","FtpGetDirectoryW"}, 
  {"238","FtpGetErrorStringA"}, 
  {"239","FtpGetErrorStringW"}, 
  {"240","FtpGetFeatures"}, 
  {"241","FtpGetFileA"}, 
  {"242","FtpGetFileW"}, 
  {"243","FtpGetFileMaskA"}, 
  {"244","FtpGetFileMaskW"}, 
  {"245","FtpGetFilePermissionsA"}, 
  {"246","FtpGetFilePermissionsW"}, 
  {"247","FtpGetFileSizeA"}, 
  {"248","FtpGetFileSizeW"}, 
  {"249","FtpGetFileStatusA"}, 
  {"250","FtpGetFileStatusW"}, 
  {"251","FtpGetFileTimeA"}, 
  {"252","FtpGetFileTimeW"}, 
  {"253","FtpGetFirstFileA"}, 
  {"254","FtpGetFirstFileW"}, 
  {"255","FtpGetLastError"}, 
  {"256","FtpGetMultipleFilesA"}, 
  {"257","FtpGetMultipleFilesW"}, 
  {"258","FtpGetNextFileA"}, 
  {"259","FtpGetNextFileW"}, 
  {"260","FtpGetProxyType"}, 
  {"261","FtpGetResultCode"}, 
  {"262","FtpGetResultStringA"}, 
  {"263","FtpGetResultStringW"}, 
  {"264","FtpGetSecurityInformationA"}, 
  {"265","FtpGetSecurityInformationW"}, 
  {"266","FtpGetServerInformationA"}, 
  {"267","FtpGetServerInformationW"}, 
  {"268","FtpGetServerStatusA"}, 
  {"269","FtpGetServerStatusW"}, 
  {"270","FtpGetServerType"}, 
  {"271","FtpGetStatus"}, 
  {"272","FtpGetTimeout"}, 
  {"273","FtpGetTransferStatusA"}, 
  {"274","FtpGetTransferStatusW"}, 
  {"275","FtpIsBlocking"}, 
  {"276","FtpIsConnected"}, 
  {"277","FtpIsReadable"}, 
  {"278","FtpIsWritable"}, 
  {"279","FtpLoginA"}, 
  {"280","FtpLoginW"}, 
  {"281","FtpLogout"}, 
  {"282","FtpMountStructureA"}, 
  {"283","FtpMountStructureW"}, 
  {"284","FtpOpenDirectoryA"}, 
  {"285","FtpOpenDirectoryW"}, 
  {"286","FtpOpenFileA"}, 
  {"287","FtpOpenFileW"}, 
  {"288","FtpPasswordA"}, 
  {"289","FtpPasswordW"}, 
  {"290","FtpProxyConnectA"}, 
  {"291","FtpProxyConnectW"}, 
  {"292","FtpPutDataA"}, 
  {"293","FtpPutDataW"}, 
  {"294","FtpPutFileA"}, 
  {"295","FtpPutFileW"}, 
  {"296","FtpPutMultipleFilesA"}, 
  {"297","FtpPutMultipleFilesW"}, 
  {"298","FtpRead"}, 
  {"299","FtpRegisterEvent"}, 
  {"300","FtpRemoveDirectoryA"}, 
  {"301","FtpRemoveDirectoryW"}, 
  {"302","FtpRenameFileA"}, 
  {"303","FtpRenameFileW"}, 
  {"304","FtpReset"}, 
  {"305","FtpSetBufferSize"}, 
  {"306","FtpSetDirectoryFormat"}, 
  {"307","FtpSetFileMaskA"}, 
  {"308","FtpSetFileMaskW"}, 
  {"309","FtpSetFileMode"}, 
  {"310","FtpSetFilePermissionsA"}, 
  {"311","FtpSetFilePermissionsW"}, 
  {"312","FtpSetFileStructure"}, 
  {"313","FtpSetFileTimeA"}, 
  {"314","FtpSetFileTimeW"}, 
  {"315","FtpSetFileType"}, 
  {"316","FtpSetLastError"}, 
  {"317","FtpSetPassiveMode"}, 
  {"318","FtpSetTimeout"}, 
  {"319","FtpUsernameA"}, 
  {"320","FtpUsernameW"}, 
  {"321","FtpWrite"}, 
  {"322","FtpSetFeatures"}, 
  {"323","FtpConnectURLA"}, 
  {"324","FtpConnectURLW"}, 
  {"325","FtpDownloadFileA"}, 
  {"326","FtpDownloadFileW"}, 
  {"327","FtpUploadFileA"}, 
  {"328","FtpUploadFileW"}, 
  {"329","FtpGetChannelMode"}, 
  {"330","FtpSetChannelMode"}, 
  {"397","FtpEnableTraceA"}, 
  {"398","FtpEnableTraceW"}, 
  {"399","FtpDisableTrace"}, 
  {"97","FtpInitializeA"}, 
  {"98","FtpInitializeW"}, 
  {"99","FtpInitializeExA"}, 
  {NULL, NULL}
};
// 0x560b9f9fef60
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_csmfpapi_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_csmfpapi_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_csmfpapi(x,y) gperf_csmfpapi_hash(x)
const unsigned int gperf_csmfpapi_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_csmfpapi = {
  .name = "csmfpapi",
  .get = &gperf_csmfpapi_get,
  .hash = &gperf_csmfpapi_hash,
  .foreach = &gperf_csmfpapi_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_csmfpapi.get)("foo");
	printf ("%s\n", s);
}
#endif
