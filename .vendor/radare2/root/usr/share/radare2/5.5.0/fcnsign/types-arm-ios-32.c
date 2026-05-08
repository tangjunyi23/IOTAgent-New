// SDB-CGEN V1.8.3
// gcc -DMAIN=1 types_arm_ios_32.c ; ./a.out > types_arm_ios_32.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"__assert_rtn","func"}, 
  {"__stack_chk_fail","func"}, 
  {"_exit","func"}, 
  {"abort","func"}, 
  {"err","func"}, 
  {"errc","func"}, 
  {"errx","func"}, 
  {"exit","func"}, 
  {"func.__assert_rtn.arg.0","const char *,assertion"}, 
  {"func.__assert_rtn.arg.1","const char *,file"}, 
  {"func.__assert_rtn.arg.2","unsigned int,line"}, 
  {"func.__assert_rtn.arg.3","const char *,function"}, 
  {"func.__assert_rtn.args","4"}, 
  {"func.__assert_rtn.cc","amd64"}, 
  {"func.__assert_rtn.noreturn","true"}, 
  {"func.__assert_rtn.ret","void"}, 
  {"func.__stack_chk_fail.args","0"}, 
  {"func.__stack_chk_fail.cc","amd64"}, 
  {"func.__stack_chk_fail.noreturn","true"}, 
  {"func.__stack_chk_fail.ret","void"}, 
  {"func._exit.arg.0","int,status"}, 
  {"func._exit.args","1"}, 
  {"func._exit.cc","amd64"}, 
  {"func._exit.noreturn","true"}, 
  {"func._exit.ret","void"}, 
  {"func.abort.args","0"}, 
  {"func.abort.cc","amd64"}, 
  {"func.abort.noreturn","true"}, 
  {"func.abort.ret","void"}, 
  {"func.err.arg.0","int,eval"}, 
  {"func.err.arg.1","const char *,fmt"}, 
  {"func.err.args","1"}, 
  {"func.err.noreturn","true"}, 
  {"func.err.ret","void"}, 
  {"func.errc.arg.0","int,eval"}, 
  {"func.errc.arg.1","int,code"}, 
  {"func.errc.arg.2","const char *,fmt"}, 
  {"func.errc.args","1"}, 
  {"func.errc.noreturn","true"}, 
  {"func.errc.ret","void"}, 
  {"func.errx.arg.0","int,eval"}, 
  {"func.errx.arg.1","const char *,fmt"}, 
  {"func.errx.args","1"}, 
  {"func.errx.noreturn","true"}, 
  {"func.errx.ret","void"}, 
  {"func.exit.arg.0","int,status"}, 
  {"func.exit.args","1"}, 
  {"func.exit.cc","amd64"}, 
  {"func.exit.noreturn","true"}, 
  {"func.exit.ret","void"}, 
  {"func.sym.imp.err.arg.0","int,eval"}, 
  {"func.sym.imp.err.arg.1","const char *,msg"}, 
  {"func.sym.imp.err.args","2"}, 
  {"func.sym.imp.err.cc","amd64"}, 
  {"func.sym.imp.err.noreturn","true"}, 
  {"func.sym.imp.err.ret","void"}, 
  {"sym.imp.err","func"}, 
  {NULL, NULL}
};
// 0x56033568c440
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_types_arm_ios_32_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_types_arm_ios_32_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_types_arm_ios_32(x,y) gperf_types_arm_ios_32_hash(x)
const unsigned int gperf_types_arm_ios_32_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_types_arm_ios_32 = {
  .name = "types-arm-ios-32",
  .get = &gperf_types_arm_ios_32_get,
  .hash = &gperf_types_arm_ios_32_hash,
  .foreach = &gperf_types_arm_ios_32_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_types_arm_ios_32.get)("foo");
	printf ("%s\n", s);
}
#endif
