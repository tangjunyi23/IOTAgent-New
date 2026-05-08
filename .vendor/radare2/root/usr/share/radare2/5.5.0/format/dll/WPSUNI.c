// SDB-CGEN V1.8.3
// gcc -DMAIN=1 WPSUNI.c ; ./a.out > WPSUNI.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","DEVBITBLT"}, 
  {"10","REALIZEOBJECT"}, 
  {"11","STRBLT"}, 
  {"12","SCANLR"}, 
  {"13","DEVICEMODE"}, 
  {"14","JEXTTEXTOUT"}, 
  {"15","DEVGETCHARWIDTH"}, 
  {"16","DEVICEBITMAP"}, 
  {"17","FASTBORDER"}, 
  {"18","SETATTRIBUTE"}, 
  {"19","DIALOGFN"}, 
  {"2","COLORINFO"}, 
  {"20","ABORTDLGPROC"}, 
  {"21","DIBTODEVICE"}, 
  {"22","WEP"}, 
  {"23","LOWMEMDIALOG"}, 
  {"24","NEWDRIVERDIALOG"}, 
  {"25","ABOUTDIALOG"}, 
  {"26","JSTATICCONTROLPROC"}, 
  {"27","DEVSTRETCHBLT"}, 
  {"28","STRETCHDIB"}, 
  {"29","BASEOPTIONDIALOG"}, 
  {"3","CONTROL"}, 
  {"30","GRAPHICSDIALOG"}, 
  {"31","BASEPAPERDIALOG"}, 
  {"32","JBUTTONCONTROLPROC"}, 
  {"33","NOPRINTERMEMDIALOG"}, 
  {"34","RUNSETUPDIALOG"}, 
  {"35","NOHOSTMEMDIALOG"}, 
  {"36","LIBMAIN"}, 
  {"37","___EXPORTEDSTUB"}, 
  {"38","MISCDIALOG"}, 
  {"39","DUPSRCDIALOG"}, 
  {"4","DISABLE"}, 
  {"40","ENDDEVMODE"}, 
  {"41","FILTERFUNC"}, 
  {"5","ENABLE"}, 
  {"6","ENUMDFONTS"}, 
  {"7","ENUMOBJ"}, 
  {"8","OUTPUT"}, 
  {"9","PIXEL"}, 
  {"90","EXTDEVICEMODE"}, 
  {"91","DEVICECAPABILITIES"}, 
  {"95","EXTDEVICEMODEPROPSHEET"}, 
  {NULL, NULL}
};
// 0x5580ad6c6a50
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_WPSUNI_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_WPSUNI_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_WPSUNI(x,y) gperf_WPSUNI_hash(x)
const unsigned int gperf_WPSUNI_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_WPSUNI = {
  .name = "WPSUNI",
  .get = &gperf_WPSUNI_get,
  .hash = &gperf_WPSUNI_hash,
  .foreach = &gperf_WPSUNI_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_WPSUNI.get)("foo");
	printf ("%s\n", s);
}
#endif
