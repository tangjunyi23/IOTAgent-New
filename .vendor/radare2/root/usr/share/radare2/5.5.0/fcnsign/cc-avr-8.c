// SDB-CGEN V1.8.3
// gcc -DMAIN=1 cc_avr_8.c ; ./a.out > cc_avr_8.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"avr","cc"}, 
  {"cc.avr.arg0","r26"}, 
  {"cc.avr.arg1","r25"}, 
  {"cc.avr.arg2","r24"}, 
  {"cc.avr.arg3","r23"}, 
  {"cc.avr.arg4","r22"}, 
  {"cc.avr.arg5","r21"}, 
  {"cc.avr.arg6","r18"}, 
  {"cc.avr.argn","stack"}, 
  {"cc.avr.ret","r24"}, 
  {"default.cc","avr"}, 
  {NULL, NULL}
};
// 0x562f3e031d70
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_cc_avr_8_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_cc_avr_8_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_cc_avr_8(x,y) gperf_cc_avr_8_hash(x)
const unsigned int gperf_cc_avr_8_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_cc_avr_8 = {
  .name = "cc-avr-8",
  .get = &gperf_cc_avr_8_get,
  .hash = &gperf_cc_avr_8_hash,
  .foreach = &gperf_cc_avr_8_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_cc_avr_8.get)("foo");
	printf ("%s\n", s);
}
#endif
