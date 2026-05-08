// SDB-CGEN V1.8.3
// gcc -DMAIN=1 COMMDLG.c ; ./a.out > COMMDLG.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","GETOPENFILENAME"}, 
  {"11","FINDTEXT"}, 
  {"12","REPLACETEXT"}, 
  {"15","CHOOSEFONT"}, 
  {"16","FORMATCHARDLGPROC"}, 
  {"2","GETSAVEFILENAME"}, 
  {"20","PRINTDLG"}, 
  {"26","COMMDLGEXTENDEDERROR"}, 
  {"27","GETFILETITLE"}, 
  {"28","WEP"}, 
  {"40","DLGTHKCONNECTIONDATALS"}, 
  {"5","CHOOSECOLOR"}, 
  {"9","LOADALTERBITMAP"}, 
  {NULL, NULL}
};
// 0x5602f03bbfe0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_COMMDLG_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_COMMDLG_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_COMMDLG(x,y) gperf_COMMDLG_hash(x)
const unsigned int gperf_COMMDLG_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_COMMDLG = {
  .name = "COMMDLG",
  .get = &gperf_COMMDLG_get,
  .hash = &gperf_COMMDLG_hash,
  .foreach = &gperf_COMMDLG_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_COMMDLG.get)("foo");
	printf ("%s\n", s);
}
#endif
