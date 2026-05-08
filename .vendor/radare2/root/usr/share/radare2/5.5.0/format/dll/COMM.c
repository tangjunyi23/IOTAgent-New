// SDB-CGEN V1.8.3
// gcc -DMAIN=1 COMM.c ; ./a.out > COMM.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","INICOM"}, 
  {"10","CFLUSH"}, 
  {"100","ENABLENOTIFICATION"}, 
  {"11","CEVT"}, 
  {"12","CEVTGET"}, 
  {"13","CSETBRK"}, 
  {"14","CCLRBRK"}, 
  {"15","GETDCB"}, 
  {"16","WEP"}, 
  {"19","COMMWRITESTRING"}, 
  {"2","SETCOM"}, 
  {"20","READCOMMSTRING"}, 
  {"3","SETQUE"}, 
  {"4","RECCOM"}, 
  {"5","SNDCOM"}, 
  {"6","CTX"}, 
  {"7","TRMCOM"}, 
  {"8","STACOM"}, 
  {"9","CEXTFCN"}, 
  {NULL, NULL}
};
// 0x55f276872530
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_COMM_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_COMM_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_COMM(x,y) gperf_COMM_hash(x)
const unsigned int gperf_COMM_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_COMM = {
  .name = "COMM",
  .get = &gperf_COMM_get,
  .hash = &gperf_COMM_hash,
  .foreach = &gperf_COMM_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_COMM.get)("foo");
	printf ("%s\n", s);
}
#endif
