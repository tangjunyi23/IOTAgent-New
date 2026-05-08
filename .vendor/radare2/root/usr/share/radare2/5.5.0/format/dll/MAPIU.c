// SDB-CGEN V1.8.3
// gcc -DMAIN=1 MAPIU.c ; ./a.out > MAPIU.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"109","FINDCLOSE"}, 
  {"118","GETSYSTEMTIME"}, 
  {"119","GETFILESIZE"}, 
  {"131","WRITEFILE"}, 
  {"137","GETLASTERROR"}, 
  {"138","HRALLOCADVISESINK"}, 
  {"147","FINDFIRSTFILE"}, 
  {"148","CREATEFILE"}, 
  {"163","CLOSEHANDLE"}, 
  {"166","_OPENTNEFSTREAM"}, 
  {"19","SETFILEPOINTER"}, 
  {"2","FBADREADPTR"}, 
  {"3","___EXPORTEDSTUB"}, 
  {"31","SYSTEMTIMETOFILETIME"}, 
  {"35","CREATEDIRECTORY"}, 
  {"46","FILETIMETOLOCALFILETIME"}, 
  {"56","GETFULLPATHNAME"}, 
  {"57","DELETEFILE"}, 
  {"59","READFILE"}, 
  {"6","_OPENSTREAMONFILE"}, 
  {"60","FINDNEXTFILE"}, 
  {"68","LOCALFILETIMETOFILETIME"}, 
  {"77","FILETIMETODOSDATETIME"}, 
  {"83","ULADDREF"}, 
  {"89","SETTIMEZONEINFORMATION"}, 
  {NULL, NULL}
};
// 0x5633addbac90
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_MAPIU_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_MAPIU_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_MAPIU(x,y) gperf_MAPIU_hash(x)
const unsigned int gperf_MAPIU_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_MAPIU = {
  .name = "MAPIU",
  .get = &gperf_MAPIU_get,
  .hash = &gperf_MAPIU_hash,
  .foreach = &gperf_MAPIU_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_MAPIU.get)("foo");
	printf ("%s\n", s);
}
#endif
