// SDB-CGEN V1.8.3
// gcc -DMAIN=1 urlmon.c ; ./a.out > urlmon.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"109","FileBearsMarkOfTheWeb"}, 
  {"110","GetPortFromUrlScheme"}, 
  {"118","GetPropertyFromName"}, 
  {"119","GetPropertyName"}, 
  {"120","IsDWORDProperty"}, 
  {"121","IsStringProperty"}, 
  {"122","AsyncGetClassBits"}, 
  {"123","AsyncInstallDistributionUnit"}, 
  {"124","BindAsyncMoniker"}, 
  {"125","CAuthenticateHostUI_CreateInstance"}, 
  {"126","CDLGetLongPathNameA"}, 
  {"127","CDLGetLongPathNameW"}, 
  {"128","CORPolicyProvider"}, 
  {"129","CoGetClassObjectFromURL"}, 
  {"130","CoInstall"}, 
  {"131","CoInternetCanonicalizeIUri"}, 
  {"132","CoInternetCombineIUri"}, 
  {"133","CoInternetCombineUrl"}, 
  {"134","CoInternetCombineUrlEx"}, 
  {"135","CoInternetCompareUrl"}, 
  {"136","CoInternetCreateSecurityManager"}, 
  {"137","CoInternetCreateZoneManager"}, 
  {"138","CoInternetFeatureSettingsChanged"}, 
  {"139","CoInternetGetMobileBrowserAppCompatMode"}, 
  {"140","CoInternetGetMobileBrowserForceDesktopMode"}, 
  {"141","CoInternetGetProtocolFlags"}, 
  {"142","CoInternetGetSecurityUrl"}, 
  {"143","CoInternetGetSecurityUrlEx"}, 
  {"144","CoInternetGetSession"}, 
  {"145","CoInternetIsFeatureEnabled"}, 
  {"146","CoInternetIsFeatureEnabledForIUri"}, 
  {"147","CoInternetIsFeatureEnabledForUrl"}, 
  {"148","CoInternetIsFeatureZoneElevationEnabled"}, 
  {"149","CoInternetParseIUri"}, 
  {"150","CoInternetParseUrl"}, 
  {"151","CoInternetQueryInfo"}, 
  {"152","CoInternetSetFeatureEnabled"}, 
  {"153","CoInternetSetMobileBrowserAppCompatMode"}, 
  {"154","CoInternetSetMobileBrowserForceDesktopMode"}, 
  {"155","CompareSecurityIds"}, 
  {"156","CompatFlagsFromClsid"}, 
  {"157","CopyBindInfo"}, 
  {"158","CopyStgMedium"}, 
  {"159","CreateAsyncBindCtx"}, 
  {"160","CreateAsyncBindCtxEx"}, 
  {"161","CreateFormatEnumerator"}, 
  {"162","CreateIUriBuilder"}, 
  {"163","CreateURLMoniker"}, 
  {"164","CreateURLMonikerEx2"}, 
  {"165","CreateURLMonikerEx"}, 
  {"166","CreateUri"}, 
  {"167","CreateUriFromMultiByteString"}, 
  {"168","CreateUriPriv"}, 
  {"169","CreateUriWithFragment"}, 
  {"170","DllCanUnloadNow"}, 
  {"171","DllGetClassObject"}, 
  {"172","DllInstall"}, 
  {"173","DllRegisterServer"}, 
  {"174","DllRegisterServerEx"}, 
  {"175","DllUnregisterServer"}, 
  {"176","Extract"}, 
  {"177","FaultInIEFeature"}, 
  {"178","FindMediaType"}, 
  {"179","FindMediaTypeClass"}, 
  {"180","FindMimeFromData"}, 
  {"181","GetAddSitesFileUrl"}, 
  {"182","GetClassFileOrMime"}, 
  {"183","GetClassURL"}, 
  {"184","GetComponentIDFromCLSSPEC"}, 
  {"185","GetIDNFlagsForUri"}, 
  {"186","GetIUriPriv2"}, 
  {"187","GetIUriPriv"}, 
  {"188","GetLabelsFromNamedHost"}, 
  {"189","GetMarkOfTheWeb"}, 
  {"190","GetSoftwareUpdateInfo"}, 
  {"191","GetUrlmonThreadNotificationHwnd"}, 
  {"192","GetZoneFromAlternateDataStreamEx"}, 
  {"193","HlinkGoBack"}, 
  {"194","HlinkGoForward"}, 
  {"195","HlinkNavigateMoniker"}, 
  {"196","HlinkNavigateString"}, 
  {"197","HlinkSimpleNavigateToMoniker"}, 
  {"198","HlinkSimpleNavigateToString"}, 
  {"199","IEDllLoader"}, 
  {"200","IEGetUserPrivateNamespaceName"}, 
  {"201","IEInstallScope"}, 
  {"202","IntlPercentEncodeNormalize"}, 
  {"203","IsAsyncMoniker"}, 
  {"204","IsIntranetAvailable"}, 
  {"205","IsJITInProgress"}, 
  {"206","IsLoggingEnabledA"}, 
  {"207","IsLoggingEnabledW"}, 
  {"208","IsValidURL"}, 
  {"209","LaunchEdgeForDebug"}, 
  {"210","MkParseDisplayNameEx"}, 
  {"211","ObtainUserAgentString"}, 
  {"212","PrivateCoInstall"}, 
  {"213","QueryAssociations"}, 
  {"214","QueryClsidAssociation"}, 
  {"215","RegisterBindStatusCallback"}, 
  {"216","RegisterFormatEnumerator"}, 
  {"217","RegisterMediaTypeClass"}, 
  {"218","RegisterMediaTypes"}, 
  {"219","RegisterWebPlatformPermanentSecurityManager"}, 
  {"220","ReleaseBindInfo"}, 
  {"221","RestrictHTTP2"}, 
  {"222","RevokeBindStatusCallback"}, 
  {"223","RevokeFormatEnumerator"}, 
  {"224","SetAccessForIEAppContainer"}, 
  {"225","SetSoftwareUpdateAdvertisementState"}, 
  {"226","ShouldDisplayPunycodeForUri"}, 
  {"227","ShouldShowIntranetWarningSecband"}, 
  {"228","ShowTrustAlertDialog"}, 
  {"229","URLDownloadA"}, 
  {"230","URLDownloadToCacheFileA"}, 
  {"231","URLDownloadToCacheFileW"}, 
  {"232","URLDownloadToFileA"}, 
  {"233","URLDownloadToFileW"}, 
  {"234","URLDownloadW"}, 
  {"235","URLOpenBlockingStreamA"}, 
  {"236","URLOpenBlockingStreamW"}, 
  {"237","URLOpenPullStreamA"}, 
  {"238","URLOpenPullStreamW"}, 
  {"239","URLOpenStreamA"}, 
  {"240","URLOpenStreamW"}, 
  {"241","UnregisterWebPlatformPermanentSecurityManager"}, 
  {"242","UrlMkBuildVersion"}, 
  {"243","UrlMkGetSessionOption"}, 
  {"244","UrlMkSetSessionOption"}, 
  {"245","UrlmonCleanupCurrentThread"}, 
  {"246","WriteHitLogging"}, 
  {"247","ZonesReInit"}, 
  {"322","IECompatLogCSSFix"}, 
  {NULL, NULL}
};
// 0x55c35e74a2d0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_urlmon_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_urlmon_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_urlmon(x,y) gperf_urlmon_hash(x)
const unsigned int gperf_urlmon_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_urlmon = {
  .name = "urlmon",
  .get = &gperf_urlmon_get,
  .hash = &gperf_urlmon_hash,
  .foreach = &gperf_urlmon_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_urlmon.get)("foo");
	printf ("%s\n", s);
}
#endif
