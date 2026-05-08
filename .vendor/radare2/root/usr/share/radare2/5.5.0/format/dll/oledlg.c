// SDB-CGEN V1.8.3
// gcc -DMAIN=1 oledlg.c ; ./a.out > oledlg.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","OleUIAddVerbMenuA"}, 
  {"10","OleUIPromptUserA"}, 
  {"11","OleUIObjectPropertiesA"}, 
  {"12","OleUIChangeSourceA"}, 
  {"13","OleUIAddVerbMenuW"}, 
  {"14","OleUIBusyW"}, 
  {"15","OleUIChangeIconW"}, 
  {"16","OleUIChangeSourceW"}, 
  {"17","OleUIConvertW"}, 
  {"18","OleUIEditLinksW"}, 
  {"19","OleUIInsertObjectW"}, 
  {"2","OleUICanConvertOrActivateAs"}, 
  {"20","OleUIObjectPropertiesW"}, 
  {"21","OleUIPasteSpecialW"}, 
  {"22","OleUIPromptUserW"}, 
  {"23","OleUIUpdateLinksW"}, 
  {"3","OleUIInsertObjectA"}, 
  {"4","OleUIPasteSpecialA"}, 
  {"5","OleUIEditLinksA"}, 
  {"6","OleUIChangeIconA"}, 
  {"7","OleUIConvertA"}, 
  {"8","OleUIBusyA"}, 
  {"9","OleUIUpdateLinksA"}, 
  {NULL, NULL}
};
// 0x55bd49958c10
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_oledlg_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_oledlg_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_oledlg(x,y) gperf_oledlg_hash(x)
const unsigned int gperf_oledlg_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_oledlg = {
  .name = "oledlg",
  .get = &gperf_oledlg_get,
  .hash = &gperf_oledlg_hash,
  .foreach = &gperf_oledlg_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_oledlg.get)("foo");
	printf ("%s\n", s);
}
#endif
