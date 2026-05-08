// SDB-CGEN V1.8.3
// gcc -DMAIN=1 atl.c ; ./a.out > atl.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"10","AtlAdvise"}, 
  {"11","AtlUnadvise"}, 
  {"12","AtlFreeMarshalStream"}, 
  {"13","AtlMarshalPtrInProc"}, 
  {"14","AtlUnmarshalPtr"}, 
  {"15","AtlModuleGetClassObject"}, 
  {"16","AtlModuleInit"}, 
  {"17","AtlModuleRegisterClassObjects"}, 
  {"18","AtlModuleRegisterServer"}, 
  {"19","AtlModuleRegisterTypeLib"}, 
  {"20","AtlModuleRevokeClassObjects"}, 
  {"21","AtlModuleTerm"}, 
  {"22","AtlModuleUnregisterServer"}, 
  {"23","AtlModuleUpdateRegistryFromResourceD"}, 
  {"24","AtlWaitWithMessageLoop"}, 
  {"25","AtlSetErrorInfo"}, 
  {"26","AtlCreateTargetDC"}, 
  {"27","AtlHiMetricToPixel"}, 
  {"28","AtlPixelToHiMetric"}, 
  {"29","AtlDevModeW2A"}, 
  {"30","AtlComPtrAssign"}, 
  {"31","AtlComQIPtrAssign"}, 
  {"32","AtlInternalQueryInterface"}, 
  {"33","DllCanUnloadNow"}, 
  {"34","AtlGetVersion"}, 
  {"35","AtlAxDialogBoxW"}, 
  {"36","AtlAxDialogBoxA"}, 
  {"37","AtlAxCreateDialogW"}, 
  {"38","AtlAxCreateDialogA"}, 
  {"39","AtlAxCreateControl"}, 
  {"40","AtlAxCreateControlEx"}, 
  {"41","AtlAxAttachControl"}, 
  {"42","AtlAxWinInit"}, 
  {"43","AtlModuleAddCreateWndData"}, 
  {"44","AtlModuleExtractCreateWndData"}, 
  {"45","AtlModuleRegisterWndClassInfoW"}, 
  {"46","AtlModuleRegisterWndClassInfoA"}, 
  {"47","AtlAxGetControl"}, 
  {"48","AtlAxGetHost"}, 
  {"49","AtlRegisterClassCategoriesHelper"}, 
  {"50","AtlIPersistStreamInit_Load"}, 
  {"51","AtlIPersistStreamInit_Save"}, 
  {"52","AtlIPersistPropertyBag_Load"}, 
  {"53","AtlIPersistPropertyBag_Save"}, 
  {"54","AtlGetObjectSourceInterface"}, 
  {"55","AtlModuleUnRegisterTypeLib"}, 
  {"56","AtlModuleLoadTypeLib"}, 
  {"57","AtlModuleUnregisterServerEx"}, 
  {"58","AtlModuleAddTermFunc"}, 
  {"59","AtlSetErrorInfo2"}, 
  {"60","AtlIPersistStreamInit_GetSizeMax"}, 
  {"61","DllGetClassObject"}, 
  {"62","DllRegisterServer"}, 
  {"63","DllUnregisterServer"}, 
  {NULL, NULL}
};
// 0x55ada12488f0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_atl_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_atl_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_atl(x,y) gperf_atl_hash(x)
const unsigned int gperf_atl_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_atl = {
  .name = "atl",
  .get = &gperf_atl_get,
  .hash = &gperf_atl_hash,
  .foreach = &gperf_atl_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_atl.get)("foo");
	printf ("%s\n", s);
}
#endif
