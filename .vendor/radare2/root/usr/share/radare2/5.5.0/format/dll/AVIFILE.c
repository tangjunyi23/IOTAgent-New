// SDB-CGEN V1.8.3
// gcc -DMAIN=1 AVIFILE.c ; ./a.out > AVIFILE.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"10","_IID_IAVISTREAM"}, 
  {"100","AVIFILEINIT"}, 
  {"101","AVIFILEEXIT"}, 
  {"102","AVIFILEOPEN"}, 
  {"103","AVISTREAMOPENFROMFILE"}, 
  {"104","AVISTREAMCREATE"}, 
  {"105","AVIMAKECOMPRESSEDSTREAM"}, 
  {"106","AVIMAKEFILEFROMSTREAMS"}, 
  {"107","AVIMAKESTREAMFROMCLIPBOARD"}, 
  {"11","_IID_IAVIFILE"}, 
  {"110","AVISTREAMGETFRAME"}, 
  {"111","AVISTREAMGETFRAMECLOSE"}, 
  {"112","AVISTREAMGETFRAMEOPEN"}, 
  {"12","_IID_IAVIEDITSTREAM"}, 
  {"120","_AVISAVE"}, 
  {"121","AVISAVEV"}, 
  {"122","AVISAVEOPTIONS"}, 
  {"123","AVIBUILDFILTER"}, 
  {"124","AVISAVEOPTIONSFREE"}, 
  {"13","_IID_IGETFRAME"}, 
  {"130","AVISTREAMSTART"}, 
  {"131","AVISTREAMLENGTH"}, 
  {"132","AVISTREAMTIMETOSAMPLE"}, 
  {"133","AVISTREAMSAMPLETOTIME"}, 
  {"14","_CLSID_AVISIMPLEUNMARSHAL"}, 
  {"140","AVIFILEADDREF"}, 
  {"141","AVIFILERELEASE"}, 
  {"142","AVIFILEINFO"}, 
  {"143","AVIFILEGETSTREAM"}, 
  {"144","AVIFILECREATESTREAM"}, 
  {"146","AVIFILEWRITEDATA"}, 
  {"147","AVIFILEREADDATA"}, 
  {"148","AVIFILEENDRECORD"}, 
  {"160","AVISTREAMADDREF"}, 
  {"161","AVISTREAMRELEASE"}, 
  {"162","AVISTREAMINFO"}, 
  {"163","AVISTREAMFINDSAMPLE"}, 
  {"164","AVISTREAMREADFORMAT"}, 
  {"165","AVISTREAMREADDATA"}, 
  {"166","AVISTREAMWRITEDATA"}, 
  {"167","AVISTREAMREAD"}, 
  {"168","AVISTREAMWRITE"}, 
  {"169","AVISTREAMSETFORMAT"}, 
  {"180","EDITSTREAMCOPY"}, 
  {"181","EDITSTREAMCUT"}, 
  {"182","EDITSTREAMPASTE"}, 
  {"184","CREATEEDITABLESTREAM"}, 
  {"185","AVIPUTFILEONCLIPBOARD"}, 
  {"187","AVIGETFROMCLIPBOARD"}, 
  {"188","AVICLEARCLIPBOARD"}, 
  {"190","EDITSTREAMCLONE"}, 
  {"191","EDITSTREAMSETNAME"}, 
  {"192","EDITSTREAMSETINFO"}, 
  {"2","DLLGETCLASSOBJECT"}, 
  {"200","AVISTREAMBEGINSTREAMING"}, 
  {"201","AVISTREAMENDSTREAMING"}, 
  {"3","DLLCANUNLOADNOW"}, 
  {"4","___EXPORTEDSTUB"}, 
  {NULL, NULL}
};
// 0x55a6521b2a70
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_AVIFILE_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_AVIFILE_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_AVIFILE(x,y) gperf_AVIFILE_hash(x)
const unsigned int gperf_AVIFILE_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_AVIFILE = {
  .name = "AVIFILE",
  .get = &gperf_AVIFILE_get,
  .hash = &gperf_AVIFILE_hash,
  .foreach = &gperf_AVIFILE_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_AVIFILE.get)("foo");
	printf ("%s\n", s);
}
#endif
