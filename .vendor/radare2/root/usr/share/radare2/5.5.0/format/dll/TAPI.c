// SDB-CGEN V1.8.3
// gcc -DMAIN=1 TAPI.c ; ./a.out > TAPI.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"10","LINEREGISTERREQUESTRECIPIENT"}, 
  {"100","LINEGETTRANSLATECAPS"}, 
  {"101","TAPIREQUESTMEDIACALL"}, 
  {"102","LINEPICKUP"}, 
  {"103","LINEANSWER"}, 
  {"104","LINEGETADDRESSID"}, 
  {"105","LINEGENERATEDIGITS"}, 
  {"106","PHONEGETID"}, 
  {"107","LINESETDEVCONFIG"}, 
  {"108","LINESETTERMINAL"}, 
  {"109","LINESWAPHOLD"}, 
  {"11","LINEHANDOFF"}, 
  {"110","DESTROYABNORMALAPP"}, 
  {"111","LINEDEALLOCATECALL"}, 
  {"112","TAPIREQUESTDROP"}, 
  {"113","LINEUNHOLD"}, 
  {"114","PHONEGETDEVCAPS"}, 
  {"115","LINESETMEDIAMODE"}, 
  {"116","LINEGETDEVCAPS"}, 
  {"117","PHONEGETLAMP"}, 
  {"118","PHONESETLAMP"}, 
  {"119","PHONECLOSE"}, 
  {"12","LINECONFIGDIALOG"}, 
  {"120","TAPI32CONNECTIONDATASL"}, 
  {"121","___EXPORTEDSTUB"}, 
  {"122","NEWDATA2"}, 
  {"123","PROCESSINIFILECHANGE"}, 
  {"124","TAPITHKCONNECTIONDATALS"}, 
  {"125","_SEND_MSG_TO_FUN_APPS"}, 
  {"126","LOPENDIALASST"}, 
  {"127","TAPILINEASYNCCB"}, 
  {"128","LADDRPARAMSINITED"}, 
  {"129","LINEGETPROVIDERLIST"}, 
  {"13","LINETRANSLATEDIALOG"}, 
  {"130","PHONEEVENTPROC"}, 
  {"131","CLASSINSTALL"}, 
  {"132","NOTIFY_REGISTER_CALLBACK"}, 
  {"133","FT_TAPIFTHKTHKCONNECTIONDATA"}, 
  {"134","LOCNEWDLG"}, 
  {"135","LINECONFIGDIALOGEDIT"}, 
  {"136","TAPILINEEVENTCB"}, 
  {"137","REGISTERTAPIAPPTHREAD"}, 
  {"138","NEWDATA"}, 
  {"139","LINERELEASEUSERUSERINFO"}, 
  {"14","PHONENEGOTIATEEXTVERSION"}, 
  {"140","ISCWNDPROC"}, 
  {"141","LINEADDPROVIDER"}, 
  {"142","LINEREMOVEPROVIDER"}, 
  {"143","LINEGETCOUNTRY"}, 
  {"144","_LCIFUNCTION"}, 
  {"145","DEREGISTERTAPIAPPTHREAD"}, 
  {"15","LINEMONITORMEDIA"}, 
  {"16","PHONECONFIGDIALOG"}, 
  {"17","LINENEGOTIATEEXTVERSION"}, 
  {"18","VERIFYDATA"}, 
  {"19","LINETRANSLATEADDRESS"}, 
  {"2","LINESETCALLPARAMS"}, 
  {"20","ASYNCLINECOMPPROC"}, 
  {"21","LINEDEVSPECIFIC"}, 
  {"22","LINEDEVSPECIFICFEATURE"}, 
  {"23","LINEDROP"}, 
  {"24","LINEMONITORDIGITS"}, 
  {"25","LINEBLINDTRANSFER"}, 
  {"26","PHONESHUTDOWN"}, 
  {"27","PHONEGETHOOKSWITCH"}, 
  {"28","TAPIREQUESTMAKECALL"}, 
  {"29","LINEDIAL"}, 
  {"3","LINESETTOLLLIST"}, 
  {"30","LIBMAIN"}, 
  {"31","LINEMONITORTONES"}, 
  {"32","LINEMAKECALL"}, 
  {"33","LINEINITIALIZE"}, 
  {"34","LINEGETNEWCALLS"}, 
  {"35","PHONEINITIALIZE"}, 
  {"36","TAPIPHONEEVENTCB"}, 
  {"37","LINESETMEDIACONTROL"}, 
  {"38","LINEREDIRECT"}, 
  {"39","PHONEGETSTATUS"}, 
  {"4","PHONEGETBUTTONINFO"}, 
  {"40","LINEGETID"}, 
  {"41","LINEUNCOMPLETECALL"}, 
  {"42","PHONESETBUTTONINFO"}, 
  {"43","LINEREMOVEFROMCONFERENCE"}, 
  {"44","LINESETSTATUSMESSAGES"}, 
  {"45","LINEGETSTATUSMESSAGES"}, 
  {"46","LINEOPEN"}, 
  {"47","LINEADDTOCONFERENCE"}, 
  {"48","LINESETUPCONFERENCE"}, 
  {"49","LINEGETLINEDEVSTATUS"}, 
  {"5","LINEPARK"}, 
  {"50","LINEPREPAREADDTOCONFERENCE"}, 
  {"51","PHONESETHOOKSWITCH"}, 
  {"52","LINEGATHERDIGITS"}, 
  {"53","LINEGETICON"}, 
  {"54","PHONESETVOLUME"}, 
  {"55","PHONEGETSTATUSMESSAGES"}, 
  {"56","PHONESETSTATUSMESSAGES"}, 
  {"57","LINESECURECALL"}, 
  {"58","LINEGETAPPPRIORITY"}, 
  {"59","PHONEGETVOLUME"}, 
  {"6","LINEHOLD"}, 
  {"60","LINEGETADDRESSSTATUS"}, 
  {"61","LINESETNUMRINGS"}, 
  {"62","LINEGETNUMRINGS"}, 
  {"63","LINESENDUSERUSERINFO"}, 
  {"64","LINENEGOTIATEAPIVERSION"}, 
  {"65","LINESETUPTRANSFER"}, 
  {"66","LINESETAPPPRIORITY"}, 
  {"67","PHONESETGAIN"}, 
  {"68","PHONEGETGAIN"}, 
  {"69","PHONESETRING"}, 
  {"7","PHONENEGOTIATEAPIVERSION"}, 
  {"70","PHONEGETRING"}, 
  {"71","LINEGETADDRESSCAPS"}, 
  {"72","LINEGETCONFRELATEDCALLS"}, 
  {"73","LINECOMPLETETRANSFER"}, 
  {"74","PHONEGETICON"}, 
  {"75","LINECONFIGPROVIDER"}, 
  {"76","LINECOMPLETECALL"}, 
  {"77","LINEUNPARK"}, 
  {"78","LINECLOSE"}, 
  {"79","LINEGETDEVCONFIG"}, 
  {"8","LINESHUTDOWN"}, 
  {"80","LINEGENERATETONE"}, 
  {"81","LINESETCURRENTLOCATION"}, 
  {"82","LINEACCEPT"}, 
  {"83","PHONEGETDISPLAY"}, 
  {"84","TAPIDLLMSGPROC"}, 
  {"85","TAPIGETLOCATIONINFO"}, 
  {"86","LINEGETREQUEST"}, 
  {"87","LINEFORWARD"}, 
  {"88","LINESETAPPSPECIFIC"}, 
  {"89","PHONEOPEN"}, 
  {"9","PHONEDEVSPECIFIC"}, 
  {"90","LINEEVENTPROC"}, 
  {"91","TAPI_INITIALIZE_REAL"}, 
  {"92","PHONESETDATA"}, 
  {"93","PHONEGETDATA"}, 
  {"94","LINEGETCALLSTATUS"}, 
  {"95","LINESETCALLPRIVILEGE"}, 
  {"96","LOCWIZARDDLGPROC"}, 
  {"97","LINEGETCALLINFO"}, 
  {"98","PHONESETDISPLAY"}, 
  {"99","TAPIINITIALIZEERROR"}, 
  {NULL, NULL}
};
// 0x55c44161f060
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_TAPI_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_TAPI_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_TAPI(x,y) gperf_TAPI_hash(x)
const unsigned int gperf_TAPI_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_TAPI = {
  .name = "TAPI",
  .get = &gperf_TAPI_get,
  .hash = &gperf_TAPI_hash,
  .foreach = &gperf_TAPI_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_TAPI.get)("foo");
	printf ("%s\n", s);
}
#endif
