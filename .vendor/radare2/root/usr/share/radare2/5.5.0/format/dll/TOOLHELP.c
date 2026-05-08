// SDB-CGEN V1.8.3
// gcc -DMAIN=1 TOOLHELP.c ; ./a.out > TOOLHELP.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"2","__GP"}, 
  {"3","DLLENTRYPOINT"}, 
  {"50","GLOBALHANDLETOSEL"}, 
  {"51","GLOBALFIRST"}, 
  {"52","GLOBALNEXT"}, 
  {"53","GLOBALINFO"}, 
  {"54","GLOBALENTRYHANDLE"}, 
  {"55","GLOBALENTRYMODULE"}, 
  {"56","LOCALINFO"}, 
  {"57","LOCALFIRST"}, 
  {"58","LOCALNEXT"}, 
  {"59","MODULEFIRST"}, 
  {"60","MODULENEXT"}, 
  {"61","MODULEFINDNAME"}, 
  {"62","MODULEFINDHANDLE"}, 
  {"63","TASKFIRST"}, 
  {"64","TASKNEXT"}, 
  {"65","TASKFINDHANDLE"}, 
  {"66","STACKTRACEFIRST"}, 
  {"67","STACKTRACECSIPFIRST"}, 
  {"68","STACKTRACENEXT"}, 
  {"69","CLASSFIRST"}, 
  {"70","CLASSNEXT"}, 
  {"71","SYSTEMHEAPINFO"}, 
  {"72","MEMMANINFO"}, 
  {"73","NOTIFYREGISTER"}, 
  {"74","NOTIFYUNREGISTER"}, 
  {"75","INTERRUPTREGISTER"}, 
  {"76","INTERRUPTUNREGISTER"}, 
  {"77","TERMINATEAPP"}, 
  {"78","MEMORYREAD"}, 
  {"79","MEMORYWRITE"}, 
  {"80","TIMERCOUNT"}, 
  {"81","TASKSETCSIP"}, 
  {"82","TASKGETCSIP"}, 
  {"83","TASKSWITCH"}, 
  {"84","LOCAL32INFO"}, 
  {"85","LOCAL32FIRST"}, 
  {"86","LOCAL32NEXT"}, 
  {NULL, NULL}
};
// 0x56052f39dcc0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_TOOLHELP_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_TOOLHELP_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_TOOLHELP(x,y) gperf_TOOLHELP_hash(x)
const unsigned int gperf_TOOLHELP_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_TOOLHELP = {
  .name = "TOOLHELP",
  .get = &gperf_TOOLHELP_get,
  .hash = &gperf_TOOLHELP_hash,
  .foreach = &gperf_TOOLHELP_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_TOOLHELP.get)("foo");
	printf ("%s\n", s);
}
#endif
