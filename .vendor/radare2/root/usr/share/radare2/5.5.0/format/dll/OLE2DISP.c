// SDB-CGEN V1.8.3
// gcc -DMAIN=1 OLE2DISP.c ; ./a.out > OLE2DISP.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","DLLGETCLASSOBJECT"}, 
  {"10","VARIANTCOPY"}, 
  {"100","VARBOOLFROMI4"}, 
  {"101","VARBOOLFROMR4"}, 
  {"102","VARBOOLFROMR8"}, 
  {"103","VARBOOLFROMDATE"}, 
  {"104","VARBOOLFROMCY"}, 
  {"105","VARBOOLFROMSTR"}, 
  {"106","VARBOOLFROMDISP"}, 
  {"107","DOINVOKEMETHOD"}, 
  {"108","VARIANTCHANGETYPEEX"}, 
  {"109","SAFEARRAYPTROFINDEX"}, 
  {"11","VARIANTCOPYIND"}, 
  {"110","SETERRORINFO"}, 
  {"111","GETERRORINFO"}, 
  {"112","CREATEERRORINFO"}, 
  {"113","_IID_IERRORINFO"}, 
  {"114","_IID_ICREATEERRORINFO"}, 
  {"115","_IID_ISUPPORTERRORINFO"}, 
  {"116","VARUI1FROMI2"}, 
  {"117","VARUI1FROMI4"}, 
  {"118","VARUI1FROMR4"}, 
  {"119","VARUI1FROMR8"}, 
  {"12","VARIANTCHANGETYPE"}, 
  {"120","VARUI1FROMCY"}, 
  {"121","VARUI1FROMDATE"}, 
  {"122","VARUI1FROMSTR"}, 
  {"123","VARUI1FROMDISP"}, 
  {"124","VARUI1FROMBOOL"}, 
  {"125","VARI2FROMUI1"}, 
  {"126","VARI4FROMUI1"}, 
  {"127","VARR4FROMUI1"}, 
  {"128","VARR8FROMUI1"}, 
  {"129","VARDATEFROMUI1"}, 
  {"13","VARIANTTIMETODOSDATETIME"}, 
  {"130","VARCYFROMUI1"}, 
  {"131","VARBSTRFROMUI1"}, 
  {"132","VARBOOLFROMUI1"}, 
  {"133","DLLCANUNLOADNOW"}, 
  {"134","WEP"}, 
  {"135","___EXPORTEDSTUB"}, 
  {"14","DOSDATETIMETOVARIANTTIME"}, 
  {"15","SAFEARRAYCREATE"}, 
  {"16","SAFEARRAYDESTROY"}, 
  {"17","SAFEARRAYGETDIM"}, 
  {"18","SAFEARRAYGETELEMSIZE"}, 
  {"19","SAFEARRAYGETUBOUND"}, 
  {"2","SYSALLOCSTRING"}, 
  {"20","SAFEARRAYGETLBOUND"}, 
  {"21","SAFEARRAYLOCK"}, 
  {"22","SAFEARRAYUNLOCK"}, 
  {"23","SAFEARRAYACCESSDATA"}, 
  {"24","SAFEARRAYUNACCESSDATA"}, 
  {"25","SAFEARRAYGETELEMENT"}, 
  {"26","SAFEARRAYPUTELEMENT"}, 
  {"27","SAFEARRAYCOPY"}, 
  {"28","DISPGETPARAM"}, 
  {"29","DISPGETIDSOFNAMES"}, 
  {"3","SYSREALLOCSTRING"}, 
  {"30","DISPINVOKE"}, 
  {"31","CREATEDISPTYPEINFO"}, 
  {"32","CREATESTDDISPATCH"}, 
  {"33","_IID_IDISPATCH"}, 
  {"34","_IID_IENUMVARIANT"}, 
  {"35","REGISTERACTIVEOBJECT"}, 
  {"36","REVOKEACTIVEOBJECT"}, 
  {"37","GETACTIVEOBJECT"}, 
  {"38","SAFEARRAYALLOCDESCRIPTOR"}, 
  {"39","SAFEARRAYALLOCDATA"}, 
  {"4","SYSALLOCSTRINGLEN"}, 
  {"40","SAFEARRAYDESTROYDESCRIPTOR"}, 
  {"41","SAFEARRAYDESTROYDATA"}, 
  {"42","SAFEARRAYREDIM"}, 
  {"43","VARI2FROMI4"}, 
  {"44","VARI2FROMR4"}, 
  {"45","VARI2FROMR8"}, 
  {"46","VARI2FROMCY"}, 
  {"47","VARI2FROMDATE"}, 
  {"48","VARI2FROMSTR"}, 
  {"49","VARI2FROMDISP"}, 
  {"5","SYSREALLOCSTRINGLEN"}, 
  {"50","VARI2FROMBOOL"}, 
  {"51","VARI4FROMI2"}, 
  {"52","VARI4FROMR4"}, 
  {"53","VARI4FROMR8"}, 
  {"54","VARI4FROMCY"}, 
  {"55","VARI4FROMDATE"}, 
  {"56","VARI4FROMSTR"}, 
  {"57","VARI4FROMDISP"}, 
  {"58","VARI4FROMBOOL"}, 
  {"59","VARR4FROMI2"}, 
  {"6","SYSFREESTRING"}, 
  {"60","VARR4FROMI4"}, 
  {"61","VARR4FROMR8"}, 
  {"62","VARR4FROMCY"}, 
  {"63","VARR4FROMDATE"}, 
  {"64","VARR4FROMSTR"}, 
  {"65","VARR4FROMDISP"}, 
  {"66","VARR4FROMBOOL"}, 
  {"67","VARR8FROMI2"}, 
  {"68","VARR8FROMI4"}, 
  {"69","VARR8FROMR4"}, 
  {"7","SYSSTRINGLEN"}, 
  {"70","VARR8FROMCY"}, 
  {"71","VARR8FROMDATE"}, 
  {"72","VARR8FROMSTR"}, 
  {"73","VARR8FROMDISP"}, 
  {"74","VARR8FROMBOOL"}, 
  {"75","VARDATEFROMI2"}, 
  {"76","VARDATEFROMI4"}, 
  {"77","VARDATEFROMR4"}, 
  {"78","VARDATEFROMR8"}, 
  {"79","VARDATEFROMCY"}, 
  {"8","VARIANTINIT"}, 
  {"80","VARDATEFROMSTR"}, 
  {"81","VARDATEFROMDISP"}, 
  {"82","VARDATEFROMBOOL"}, 
  {"83","VARCYFROMI2"}, 
  {"84","VARCYFROMI4"}, 
  {"85","VARCYFROMR4"}, 
  {"86","VARCYFROMR8"}, 
  {"87","VARCYFROMDATE"}, 
  {"88","VARCYFROMSTR"}, 
  {"89","VARCYFROMDISP"}, 
  {"9","VARIANTCLEAR"}, 
  {"90","VARCYFROMBOOL"}, 
  {"91","VARBSTRFROMI2"}, 
  {"92","VARBSTRFROMI4"}, 
  {"93","VARBSTRFROMR4"}, 
  {"94","VARBSTRFROMR8"}, 
  {"95","VARBSTRFROMCY"}, 
  {"96","VARBSTRFROMDATE"}, 
  {"97","VARBSTRFROMDISP"}, 
  {"98","VARBSTRFROMBOOL"}, 
  {"99","VARBOOLFROMI2"}, 
  {NULL, NULL}
};
// 0x557717879db0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_OLE2DISP_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_OLE2DISP_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_OLE2DISP(x,y) gperf_OLE2DISP_hash(x)
const unsigned int gperf_OLE2DISP_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_OLE2DISP = {
  .name = "OLE2DISP",
  .get = &gperf_OLE2DISP_get,
  .hash = &gperf_OLE2DISP_hash,
  .foreach = &gperf_OLE2DISP_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_OLE2DISP.get)("foo");
	printf ("%s\n", s);
}
#endif
