// SDB-CGEN V1.8.3
// gcc -DMAIN=1 cc_x86_16.c ; ./a.out > cc_x86_16.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"cc.fastcall.arg0","ax"}, 
  {"cc.fastcall.arg1","dx"}, 
  {"cc.fastcall.arg2","bx"}, 
  {"cc.fastcall.arg3","cx"}, 
  {"cc.fastcall.argn","stack"}, 
  {"cc.fastcall.ret","ax"}, 
  {"cc.ms.arg0","ax"}, 
  {"cc.ms.arg1","dx"}, 
  {"cc.ms.argn","stack"}, 
  {"cc.ms.ret","ax"}, 
  {"cc.msm.arg0","ax"}, 
  {"cc.msm.arg1","dx"}, 
  {"cc.msm.arg2","bx"}, 
  {"cc.msm.argn","stack"}, 
  {"cc.msm.ret","bx"}, 
  {"cc.turboc.arg0","ax"}, 
  {"cc.turboc.arg1","dx"}, 
  {"cc.turboc.arg2","bx"}, 
  {"cc.turboc.argn","stack"}, 
  {"cc.turboc.ret","ax"}, 
  {"cc.watcom.arg0","ax"}, 
  {"cc.watcom.arg1","dx"}, 
  {"cc.watcom.arg2","bx"}, 
  {"cc.watcom.arg3","cx"}, 
  {"cc.watcom.argn","stack"}, 
  {"cc.watcom.ret","si"}, 
  {"default.cc","fastcall"}, 
  {"fastcall","cc"}, 
  {"ms","cc"}, 
  {"msm","cc"}, 
  {"turboc","cc"}, 
  {"watcom","cc"}, 
  {NULL, NULL}
};
// 0x5612f97a83d0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_cc_x86_16_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_cc_x86_16_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_cc_x86_16(x,y) gperf_cc_x86_16_hash(x)
const unsigned int gperf_cc_x86_16_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_cc_x86_16 = {
  .name = "cc-x86-16",
  .get = &gperf_cc_x86_16_get,
  .hash = &gperf_cc_x86_16_hash,
  .foreach = &gperf_cc_x86_16_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_cc_x86_16.get)("foo");
	printf ("%s\n", s);
}
#endif
