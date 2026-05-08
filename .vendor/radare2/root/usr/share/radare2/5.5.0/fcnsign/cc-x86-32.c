// SDB-CGEN V1.8.3
// gcc -DMAIN=1 cc_x86_32.c ; ./a.out > cc_x86_32.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"borland","cc"}, 
  {"cc.borland.arg0","eax"}, 
  {"cc.borland.arg1","edx"}, 
  {"cc.borland.arg2","ecx"}, 
  {"cc.borland.argn","stack_rev"}, 
  {"cc.borland.ret","eax"}, 
  {"cc.cdecl-fastcall-ms.arg0","ecx"}, 
  {"cc.cdecl-fastcall-ms.argn","stack"}, 
  {"cc.cdecl-fastcall-ms.ret","eax"}, 
  {"cc.cdecl.argn","stack"}, 
  {"cc.cdecl.ret","eax"}, 
  {"cc.fastcall.arg0","ecx"}, 
  {"cc.fastcall.arg1","edx"}, 
  {"cc.fastcall.argn","stack"}, 
  {"cc.fastcall.ret","eax"}, 
  {"cc.optlink.arg0","eax"}, 
  {"cc.optlink.arg1","edx"}, 
  {"cc.optlink.arg2","ecx"}, 
  {"cc.optlink.argn","stack"}, 
  {"cc.optlink.ret","eax"}, 
  {"cc.pascal.argn","stack_rev"}, 
  {"cc.pascal.ret","eax"}, 
  {"cc.stdcall.argn","stack"}, 
  {"cc.stdcall.ret","eax"}, 
  {"cc.watcom.arg0","eax"}, 
  {"cc.watcom.arg1","edx"}, 
  {"cc.watcom.arg2","ebx"}, 
  {"cc.watcom.arg3","ecx"}, 
  {"cc.watcom.argn","stack"}, 
  {"cc.watcom.ret","eax"}, 
  {"cdecl","cc"}, 
  {"cdecl-fastcall-ms","cc"}, 
  {"default.cc","cdecl"}, 
  {"fastcall","cc"}, 
  {"optlink","cc"}, 
  {"pascal","cc"}, 
  {"stdcall","cc"}, 
  {"watcom","cc"}, 
  {NULL, NULL}
};
// 0x555b52f24a10
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_cc_x86_32_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_cc_x86_32_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_cc_x86_32(x,y) gperf_cc_x86_32_hash(x)
const unsigned int gperf_cc_x86_32_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_cc_x86_32 = {
  .name = "cc-x86-32",
  .get = &gperf_cc_x86_32_get,
  .hash = &gperf_cc_x86_32_hash,
  .foreach = &gperf_cc_x86_32_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_cc_x86_32.get)("foo");
	printf ("%s\n", s);
}
#endif
