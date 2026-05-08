// SDB-CGEN V1.8.3
// gcc -DMAIN=1 MODEMUI.c ; ./a.out > MODEMUI.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"10","MDM_COMMCONFIGDIALOG"}, 
  {"12","ENUMPROPPAGES"}, 
  {"20","DRVCOMMCONFIGDIALOG"}, 
  {"21","DRVSETDEFAULTCOMMCONFIG"}, 
  {"22","DRVGETDEFAULTCOMMCONFIG"}, 
  {NULL, NULL}
};
// 0x564793111710
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_MODEMUI_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_MODEMUI_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_MODEMUI(x,y) gperf_MODEMUI_hash(x)
const unsigned int gperf_MODEMUI_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_MODEMUI = {
  .name = "MODEMUI",
  .get = &gperf_MODEMUI_get,
  .hash = &gperf_MODEMUI_hash,
  .foreach = &gperf_MODEMUI_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_MODEMUI.get)("foo");
	printf ("%s\n", s);
}
#endif
