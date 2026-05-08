// SDB-CGEN V1.8.3
// gcc -DMAIN=1 SYSTEM.c ; ./a.out > SYSTEM.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","INQUIRESYSTEM"}, 
  {"10","WEP"}, 
  {"13","INQUIRELONGINTS"}, 
  {"2","CREATESYSTEMTIMER"}, 
  {"20","A20_PROC"}, 
  {"21","KILLSYSTEMTIMERCS"}, 
  {"22","__GP"}, 
  {"3","KILLSYSTEMTIMER"}, 
  {"4","ENABLESYSTEMTIMERS"}, 
  {"5","DISABLESYSTEMTIMERS"}, 
  {"6","GETSYSTEMMSECCOUNT"}, 
  {"7","GET80X87SAVESIZE"}, 
  {"8","SAVE80X87STATE"}, 
  {"9","RESTORE80X87STATE"}, 
  {NULL, NULL}
};
// 0x55e6ae7b7ff0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_SYSTEM_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_SYSTEM_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_SYSTEM(x,y) gperf_SYSTEM_hash(x)
const unsigned int gperf_SYSTEM_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_SYSTEM = {
  .name = "SYSTEM",
  .get = &gperf_SYSTEM_get,
  .hash = &gperf_SYSTEM_hash,
  .foreach = &gperf_SYSTEM_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_SYSTEM.get)("foo");
	printf ("%s\n", s);
}
#endif
