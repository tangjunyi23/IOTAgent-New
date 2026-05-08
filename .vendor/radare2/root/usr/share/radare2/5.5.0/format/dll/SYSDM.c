// SDB-CGEN V1.8.3
// gcc -DMAIN=1 SYSDM.c ; ./a.out > SYSDM.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","CPLAPPLET"}, 
  {"10","DMFIRSTTIMESETUP"}, 
  {"11","SELECTREPORTHOOKPROC"}, 
  {"12","GETCFGDLGPROC"}, 
  {"13","PROFILEDLGPROC"}, 
  {"14","DEVMGRDLGPROC"}, 
  {"15","INSTALLDEVICE_RUNDLL"}, 
  {"16","DISPLAYREALMODEWARNING"}, 
  {"17","ENABLEPCMCIA_RUNDLL"}, 
  {"18","NOINFDLGPROC"}, 
  {"19","VIRTUALMEMORYDLGPROC"}, 
  {"2","DMSETUPDEVNODE"}, 
  {"20","EDITRANGEDLGPROC"}, 
  {"21","SYSTEMINFODLGPROC"}, 
  {"3","DMREDETECT"}, 
  {"4","DMPROCESSMWD"}, 
  {"5","DMASKFORCONFIG"}, 
  {"6","DMREGISTRYERROR"}, 
  {"7","DMWAITFORUNDOCK"}, 
  {"8","DMREMOVEROMOKAY"}, 
  {"9","DMPRIVATEPROBLEM"}, 
  {"999","WEP"}, 
  {NULL, NULL}
};
// 0x55b8192736e0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_SYSDM_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_SYSDM_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_SYSDM(x,y) gperf_SYSDM_hash(x)
const unsigned int gperf_SYSDM_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_SYSDM = {
  .name = "SYSDM",
  .get = &gperf_SYSDM_get,
  .hash = &gperf_SYSDM_hash,
  .foreach = &gperf_SYSDM_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_SYSDM.get)("foo");
	printf ("%s\n", s);
}
#endif
