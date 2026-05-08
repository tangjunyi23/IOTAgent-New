// SDB-CGEN V1.8.3
// gcc -DMAIN=1 CMC.c ; ./a.out > CMC.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"10","CMC_LIST"}, 
  {"11","CMC_QUERY_CONFIGURATION"}, 
  {"12","CMC_FREE"}, 
  {"2","CMC_LOGOFF"}, 
  {"3","CMC_LOGON"}, 
  {"4","CMC_ACT_ON"}, 
  {"5","CMC_LOOK_UP"}, 
  {"6","___EXPORTEDSTUB"}, 
  {"7","CMC_SEND_DOCUMENTS"}, 
  {"8","CMC_READ"}, 
  {"9","CMC_SEND"}, 
  {NULL, NULL}
};
// 0x55cc4a3f3e30
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_CMC_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_CMC_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_CMC(x,y) gperf_CMC_hash(x)
const unsigned int gperf_CMC_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_CMC = {
  .name = "CMC",
  .get = &gperf_CMC_get,
  .hash = &gperf_CMC_hash,
  .foreach = &gperf_CMC_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_CMC.get)("foo");
	printf ("%s\n", s);
}
#endif
