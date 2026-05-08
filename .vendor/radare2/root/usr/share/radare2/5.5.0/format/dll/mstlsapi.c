// SDB-CGEN V1.8.3
// gcc -DMAIN=1 mstlsapi.c ; ./a.out > mstlsapi.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"10","TLSIssuePlatformChallenge"}, 
  {"101","RequestToTlsRequest"}, 
  {"103","TLSRequestTermServCert"}, 
  {"104","TLSRetrieveTermServCert"}, 
  {"105","TLSInstallCertificate"}, 
  {"106","TLSGetServerCertificate"}, 
  {"107","TLSRegisterLicenseKeyPack"}, 
  {"108","TLSGetLSPKCS10CertRequest"}, 
  {"109","TLSKeyPackAdd"}, 
  {"11","TLSIssueNewLicense"}, 
  {"110","TLSKeyPackSetStatus"}, 
  {"113","TLSReturnLicense"}, 
  {"114","TLSAnnounceServer"}, 
  {"115","TLSLookupServer"}, 
  {"116","TLSAnnounceLicensePack"}, 
  {"117","TLSReturnLicensedProduct"}, 
  {"118","TLSTelephoneRegisterLKP"}, 
  {"119","TLSChallengeServer"}, 
  {"12","TLSUpgradeLicense"}, 
  {"120","TLSResponseServerChallenge"}, 
  {"121","TLSGetTlsPrivateData"}, 
  {"123","TLSTriggerReGenKey"}, 
  {"124","TLSGetServerPID"}, 
  {"126","TLSGetServerSPK"}, 
  {"127","TLSDepositeServerSPK"}, 
  {"13","TLSAllocateConcurrentLicense"}, 
  {"130","TLSAllocateInternetLicenseEx"}, 
  {"131","TLSReturnInternetLicenseEx"}, 
  {"132","TLSIsBetaNTServer"}, 
  {"133","TLSIsLicenseEnforceEnable"}, 
  {"134","TLSInDomain"}, 
  {"135","TLSMarkLicense"}, 
  {"136","TLSGetSupportFlags"}, 
  {"138","TLSLookupServerFixed"}, 
  {"14","TLSGetLastError"}, 
  {"15","TLSKeyPackEnumBegin"}, 
  {"16","TLSKeyPackEnumNext"}, 
  {"17","TLSKeyPackEnumEnd"}, 
  {"18","TLSLicenseEnumBegin"}, 
  {"19","TLSLicenseEnumNext"}, 
  {"2","TLSGetVersion"}, 
  {"20","TLSLicenseEnumEnd"}, 
  {"21","TLSGetAvailableLicenses"}, 
  {"24","TLSConnectToLsServer"}, 
  {"25","TLSConnectToAnyLsServer"}, 
  {"26","TLSDisconnectFromServer"}, 
  {"27","FindEnterpriseServer"}, 
  {"28","GetAllEnterpriseServers"}, 
  {"29","TLSInit"}, 
  {"3","MIDL_user_allocate"}, 
  {"30","TLSGetTSCertificate"}, 
  {"31","LsCsp_GetServerData"}, 
  {"32","LsCsp_DecryptEnvelopedData"}, 
  {"33","LsCsp_EncryptHwid"}, 
  {"34","LsCsp_StoreSecret"}, 
  {"35","LsCsp_RetrieveSecret"}, 
  {"36","TLSStartDiscovery"}, 
  {"37","TLSStopDiscovery"}, 
  {"38","TLSShutdown"}, 
  {"39","TLSFreeTSCertificate"}, 
  {"4","MIDL_user_free"}, 
  {"40","TLSIssueNewLicenseEx"}, 
  {"41","TLSUpgradeLicenseEx"}, 
  {"42","TLSCheckLicenseMark"}, 
  {"43","TLSIssueNewLicenseExEx"}, 
  {"44","TLSGetServerNameEx"}, 
  {"45","TLSLicenseEnumNextEx"}, 
  {"46","TLSGetServerNameFixed"}, 
  {"47","TLSGetServerScopeFixed"}, 
  {"48","TLSGetLastErrorFixed"}, 
  {"49","GetLicenseServersFromReg"}, 
  {"5","EnumerateTlsServer"}, 
  {"50","TLSConnectToAnyLsServerNoCertInstall"}, 
  {"51","TLSIssuePerUserLicense"}, 
  {"52","TLSReportEnumBegin"}, 
  {"53","TLSReportEnumNext"}, 
  {"54","TLSReportEnumEnd"}, 
  {"55","TLSFetchReportBegin"}, 
  {"56","TLSFetchReportNext"}, 
  {"57","TLSFetchReportEnd"}, 
  {"58","TLSReportGenerateBegin"}, 
  {"59","TLSReportGenerateCancel"}, 
  {"6","TLSSendServerCertificate"}, 
  {"60","TLSReportDelete"}, 
  {"61","TLSIsFreeKeyPackInstalled"}, 
  {"62","TLSIsServerInDomain"}, 
  {"63","TLSIsLSPubished"}, 
  {"64","TLSPublishLS"}, 
  {"65","TLSUnpublishLS"}, 
  {"66","TLSChangeRole"}, 
  {"67","TLSIsGPEnabled"}, 
  {"68","TLSIsLocalGroupForGPPresent"}, 
  {"69","TLSCreateLocalGroupForGP"}, 
  {"7","TLSGetServerName"}, 
  {"70","TLSCanLSUpdateAD"}, 
  {"71","TLSAddLStoTSLSofDC"}, 
  {"72","TLSIsLSonDC"}, 
  {"73","TLSDatabasePath"}, 
  {"74","TLSIsUserAdmin"}, 
  {"75","TLSConnectToLsServerWithUserIdentity"}, 
  {"76","TLSRemoveLSFromTSLSOfAD"}, 
  {"77","TLSRemoveLocalGroupForGP"}, 
  {"78","EnumerateAllLicenseServers"}, 
  {"79","TLSIsPreventUpgGPEnabled"}, 
  {"8","TLSGetServerScope"}, 
  {"80","TLSRevokeLicense"}, 
  {NULL, NULL}
};
// 0x55b843e28920
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_mstlsapi_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_mstlsapi_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_mstlsapi(x,y) gperf_mstlsapi_hash(x)
const unsigned int gperf_mstlsapi_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_mstlsapi = {
  .name = "mstlsapi",
  .get = &gperf_mstlsapi_get,
  .hash = &gperf_mstlsapi_hash,
  .foreach = &gperf_mstlsapi_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_mstlsapi.get)("foo");
	printf ("%s\n", s);
}
#endif
