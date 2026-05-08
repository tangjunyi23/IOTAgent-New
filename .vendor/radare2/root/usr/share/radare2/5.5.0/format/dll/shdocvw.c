// SDB-CGEN V1.8.3
// gcc -DMAIN=1 shdocvw.c ; ./a.out > shdocvw.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"106","AddUrlToFavorites"}, 
  {"107","DllCanUnloadNow"}, 
  {"108","DllGetClassObject"}, 
  {"109","DllGetVersion"}, 
  {"112","DllRegisterWindowClasses"}, 
  {"113","DoAddToFavDlg"}, 
  {"114","DoAddToFavDlgW"}, 
  {"124","DoFileDownload"}, 
  {"126","DoFileDownloadEx"}, 
  {"127","DoOrganizeFavDlg"}, 
  {"128","DoOrganizeFavDlgW"}, 
  {"129","DoPrivacyDlg"}, 
  {"132","HlinkFindFrame"}, 
  {"133","HlinkFrameNavigate"}, 
  {"134","HlinkFrameNavigateNHL"}, 
  {"144","ImportPrivacySettings"}, 
  {"154","OpenURL"}, 
  {"155","SHGetIDispatchForFolder"}, 
  {"156","SetQueryNetSessionCount"}, 
  {"157","SetShellOfflineState"}, 
  {"163","SHAddSubscribeFavorite"}, 
  {"166","SoftwareUpdateMessageBox"}, 
  {"168","URLQualifyA"}, 
  {"182","URLQualifyW"}, 
  {NULL, NULL}
};
// 0x55bf052e9b50
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_shdocvw_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_shdocvw_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_shdocvw(x,y) gperf_shdocvw_hash(x)
const unsigned int gperf_shdocvw_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_shdocvw = {
  .name = "shdocvw",
  .get = &gperf_shdocvw_get,
  .hash = &gperf_shdocvw_hash,
  .foreach = &gperf_shdocvw_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_shdocvw.get)("foo");
	printf ("%s\n", s);
}
#endif
