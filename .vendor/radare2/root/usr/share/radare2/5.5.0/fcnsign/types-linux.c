// SDB-CGEN V1.8.3
// gcc -DMAIN=1 types_linux.c ; ./a.out > types_linux.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"_Exit","func"}, 
  {"__assert_fail","func"}, 
  {"__cxa_throw","func"}, 
  {"__libc_init","func"}, 
  {"__libc_init_array","func"}, 
  {"__libc_start_main","func"}, 
  {"__stack_chk_fail","func"}, 
  {"__uClibc_main","func"}, 
  {"_exit","func"}, 
  {"abort","func"}, 
  {"access","func"}, 
  {"atexit","func"}, 
  {"err","func"}, 
  {"errc","func"}, 
  {"errx","func"}, 
  {"exit","func"}, 
  {"func._Exit.arg.0","int,status"}, 
  {"func._Exit.args","1"}, 
  {"func._Exit.noreturn","true"}, 
  {"func._Exit.ret","void"}, 
  {"func.__assert_fail.arg.0","const char *,assertion"}, 
  {"func.__assert_fail.arg.1","const char *,file"}, 
  {"func.__assert_fail.arg.2","unsigned int,line"}, 
  {"func.__assert_fail.arg.3","const char *,function"}, 
  {"func.__assert_fail.args","4"}, 
  {"func.__assert_fail.noreturn","true"}, 
  {"func.__assert_fail.ret","void"}, 
  {"func.__cxa_throw.arg.0","void *,thrown_exception"}, 
  {"func.__cxa_throw.arg.1","struct std::type_info *,tinfo"}, 
  {"func.__cxa_throw.arg.2","void *,dest"}, 
  {"func.__cxa_throw.args","3"}, 
  {"func.__cxa_throw.noreturn","true"}, 
  {"func.__cxa_throw.ret","void"}, 
  {"func.__libc_init.arg.0","int,argc"}, 
  {"func.__libc_init.arg.1","char **,argv"}, 
  {"func.__libc_init.arg.2","char **,envp"}, 
  {"func.__libc_init.args","3"}, 
  {"func.__libc_init.noreturn","true"}, 
  {"func.__libc_init.ret","void"}, 
  {"func.__libc_init_array.args","0"}, 
  {"func.__libc_init_array.ret","void"}, 
  {"func.__libc_start_main.arg.0","func,main"}, 
  {"func.__libc_start_main.arg.1","int,argc"}, 
  {"func.__libc_start_main.arg.2","char **,ubp_av"}, 
  {"func.__libc_start_main.arg.3","func,init"}, 
  {"func.__libc_start_main.arg.4","func,fini"}, 
  {"func.__libc_start_main.arg.5","func,rtld_fini"}, 
  {"func.__libc_start_main.arg.6","void *,stack_end"}, 
  {"func.__libc_start_main.args","7"}, 
  {"func.__libc_start_main.noreturn","true"}, 
  {"func.__libc_start_main.ret","int"}, 
  {"func.__stack_chk_fail.args","0"}, 
  {"func.__stack_chk_fail.noreturn","true"}, 
  {"func.__stack_chk_fail.ret","void"}, 
  {"func.__uClibc_main.arg.0","func,main"}, 
  {"func.__uClibc_main.arg.1","int,argc"}, 
  {"func.__uClibc_main.arg.2","char **,argv"}, 
  {"func.__uClibc_main.arg.3","func,app_init"}, 
  {"func.__uClibc_main.arg.4","func,app_fini"}, 
  {"func.__uClibc_main.arg.5","func,rtld_fini"}, 
  {"func.__uClibc_main.arg.6","void *,stack_end"}, 
  {"func.__uClibc_main.args","7"}, 
  {"func.__uClibc_main.noreturn","true"}, 
  {"func.__uClibc_main.ret","int"}, 
  {"func._exit.arg.0","int,status"}, 
  {"func._exit.args","1"}, 
  {"func._exit.noreturn","true"}, 
  {"func._exit.ret","void"}, 
  {"func.abort.args","0"}, 
  {"func.abort.noreturn","true"}, 
  {"func.abort.ret","void"}, 
  {"func.access.arg.0","const char *,path"}, 
  {"func.access.arg.1","int,mode"}, 
  {"func.access.args","2"}, 
  {"func.access.ret","int"}, 
  {"func.atexit.arg.0","func,function"}, 
  {"func.atexit.args","1"}, 
  {"func.atexit.ret","int"}, 
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
  {"func.exit.noreturn","true"}, 
  {"func.exit.ret","void"}, 
  {"func.getsockname.arg.0","int,sockfd"}, 
  {"func.getsockname.arg.1","struct sockaddr *,addr"}, 
  {"func.getsockname.arg.2","socklen_t *,addrlen"}, 
  {"func.getsockname.args","3"}, 
  {"func.getsockname.ret","int"}, 
  {"func.getsockopt.arg.0","int,sockfd"}, 
  {"func.getsockopt.arg.1","int,level"}, 
  {"func.getsockopt.arg.2","int,optname"}, 
  {"func.getsockopt.arg.3","void *,optval"}, 
  {"func.getsockopt.arg.4","socklen_t *,optlen"}, 
  {"func.getsockopt.args","5"}, 
  {"func.getsockopt.ret","int"}, 
  {"func.nanosleep.arg.0","const struct timespec *,req"}, 
  {"func.nanosleep.arg.1","struct timespec *,rem"}, 
  {"func.nanosleep.args","2"}, 
  {"func.nanosleep.ret","int"}, 
  {"func.prctl.arg.0","int,option"}, 
  {"func.prctl.arg.1","unsigned long,v2"}, 
  {"func.prctl.arg.2","unsigned long,v3"}, 
  {"func.prctl.arg.3","unsigned long,v4"}, 
  {"func.prctl.arg.4","unsigned long,v5"}, 
  {"func.prctl.args","5"}, 
  {"func.prctl.ret","int"}, 
  {"func.select.arg.0","int,nfds"}, 
  {"func.select.arg.1","fd_set *,readfds"}, 
  {"func.select.arg.2","fd_set *,writefds"}, 
  {"func.select.arg.3","fd_set *,exceptfds"}, 
  {"func.select.arg.4","struct timeval *,timeout"}, 
  {"func.select.args","5"}, 
  {"func.select.ret","int"}, 
  {"func.setsockopt.arg.0","int,sockfd"}, 
  {"func.setsockopt.arg.1","int,level"}, 
  {"func.setsockopt.arg.2","int,optname"}, 
  {"func.setsockopt.arg.3","void *,optval"}, 
  {"func.setsockopt.arg.4","socklen_t,optlen"}, 
  {"func.setsockopt.args","5"}, 
  {"func.setsockopt.ret","int"}, 
  {"func.sigaction.arg.0","int,signum"}, 
  {"func.sigaction.arg.1","const struct sigaction *,act"}, 
  {"func.sigaction.arg.2","struct sigaction *,oldact"}, 
  {"func.sigaction.args","3"}, 
  {"func.sigaction.ret","int"}, 
  {"func.wait.arg.0","int *,wstatus"}, 
  {"func.wait.args","1"}, 
  {"func.wait.ret","pid_t"}, 
  {"func.waitid.arg.0","idtype_t,idtype"}, 
  {"func.waitid.arg.1","id_t,id"}, 
  {"func.waitid.arg.2","siginfo_t *,infop"}, 
  {"func.waitid.arg.3","int,options"}, 
  {"func.waitid.args","4"}, 
  {"func.waitid.ret","int"}, 
  {"func.waitpid.arg.0","pid_t,pid"}, 
  {"func.waitpid.arg.1","int *,wstatus"}, 
  {"func.waitpid.arg.2","int,options"}, 
  {"func.waitpid.args","3"}, 
  {"func.waitpid.ret","pid_t"}, 
  {"getsockname","func"}, 
  {"getsockopt","func"}, 
  {"nanosleep","func"}, 
  {"prctl","func"}, 
  {"select","func"}, 
  {"setsockopt","func"}, 
  {"sigaction","func"}, 
  {"wait","func"}, 
  {"waitid","func"}, 
  {"waitpid","func"}, 
  {NULL, NULL}
};
// 0x55676e146c80
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_types_linux_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_types_linux_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_types_linux(x,y) gperf_types_linux_hash(x)
const unsigned int gperf_types_linux_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_types_linux = {
  .name = "types-linux",
  .get = &gperf_types_linux_get,
  .hash = &gperf_types_linux_hash,
  .foreach = &gperf_types_linux_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_types_linux.get)("foo");
	printf ("%s\n", s);
}
#endif
