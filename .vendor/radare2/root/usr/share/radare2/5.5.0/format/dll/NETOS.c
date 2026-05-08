// SDB-CGEN V1.8.3
// gcc -DMAIN=1 NETOS.c ; ./a.out > NETOS.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"10","NW_DETECTBTRIEVE"}, 
  {"11","NW_DETECTPERSONALNETWARE"}, 
  {"12","NW_DETECTTHIRDPARTYTCPSTACK"}, 
  {"13","NW_DETECTNACS"}, 
  {"14","NW_DETECTTERMINALEMULATOR"}, 
  {"15","NW_DETECTAPPLETALK"}, 
  {"16","NW_DETECTNETBIOS"}, 
  {"17","NW_DETECTRPRINTER"}, 
  {"18","NW_DETECTSNMPAGENTS"}, 
  {"19","NW_DETECTNOVELLTSA"}, 
  {"2","DETECTNETWORK"}, 
  {"20","NW_DETECTCHEYENNEARCSERVE"}, 
  {"21","NW_DETECTLEGATO"}, 
  {"22","NW_DETECTARCADA"}, 
  {"23","NW_GETNWINFO"}, 
  {"24","DETECTMICROSOFTNETWORK"}, 
  {"25","GETLASTDRIVEFROMDOS"}, 
  {"26","TSR_DETECT"}, 
  {"27","GETBANNEWREVVER"}, 
  {"28","NW_ISNDSINUSE"}, 
  {"29","GETNOVELLCONNECTIONS"}, 
  {"3","LSL_ISLSLLOADED"}, 
  {"30","ISNWREDIRLOADED"}, 
  {"31","DETECTNOVELL_MACHINENAME"}, 
  {"4","LSL_GETNETCFGPATH"}, 
  {"5","LSL_GETMLIDINFO"}, 
  {"6","TSR_FINDINTHOOKER"}, 
  {"7","___EXPORTEDSTUB"}, 
  {NULL, NULL}
};
// 0x558e3823a0c0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_NETOS_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_NETOS_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_NETOS(x,y) gperf_NETOS_hash(x)
const unsigned int gperf_NETOS_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_NETOS = {
  .name = "NETOS",
  .get = &gperf_NETOS_get,
  .hash = &gperf_NETOS_hash,
  .foreach = &gperf_NETOS_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_NETOS.get)("foo");
	printf ("%s\n", s);
}
#endif
