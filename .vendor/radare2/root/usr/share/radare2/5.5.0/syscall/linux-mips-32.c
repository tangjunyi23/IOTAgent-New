// SDB-CGEN V1.8.3
// gcc -DMAIN=1 linux_mips_32.c ; ./a.out > linux_mips_32.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"_","4000"}, 
  {"access","0xfa0,4033,2,"}, 
  {"brk","0xfa0,4045,1,"}, 
  {"chdir","0xfa0,4012,1,z"}, 
  {"chmod","0xfa0,4015,1,zx"}, 
  {"clone","0xfa0+120,4120,4,"}, 
  {"close","0xfa0,4006,1,i"}, 
  {"creat","0xfa0,4008,2,zx"}, 
  {"dup","0xfa0,4041,2,"}, 
  {"execve","0xfa0,4011,3,zzz"}, 
  {"exit","0xfa0,4001,1,i"}, 
  {"exit_group","0xfa0+252,4252,1,"}, 
  {"fcntl64","0xfa0+221,4221,3,"}, 
  {"fork","0xfa0,4002,0,"}, 
  {"fstat64","0xfa0+197,4197,2,"}, 
  {"get_thread_area","0xfa0+244,4244,2,"}, 
  {"getpid","0xfa0,4020,0,"}, 
  {"gettid","0xfa0+224,4224,0,"}, 
  {"getuid","0xfa0,4024,0,"}, 
  {"ioctl","0xfa0,4054,3,"}, 
  {"kill","0xfa0,4037,2,"}, 
  {"lchown","0xfa0,4016,1,zii"}, 
  {"link","0xfa0,4009,2,zz"}, 
  {"mknod","0xfa0,4014,1,zxi"}, 
  {"mmap","0xfa0,4090,6,"}, 
  {"mmap2","0xfa0+192,4192,6,"}, 
  {"mprotect","0xfa0+125,4125,3,"}, 
  {"munmap","0xfa0,4091,1,"}, 
  {"open","0xfa0,4005,3,zxx"}, 
  {"ptrace","0xfa0,4026,4,"}, 
  {"read","0xfa0,4003,3,ipi"}, 
  {"rt_sigaction","0xfa0+174,4174,3,"}, 
  {"rt_sigprocmask","0xfa0+175,4175,3,"}, 
  {"set_thread_area","0xfa0+243,4243,2,"}, 
  {"setuid","0xfa0,4023,1,i"}, 
  {"signal","0xfa0,4048,2,"}, 
  {"sigreturn","0xfa0+119,4119,1,"}, 
  {"socketcall","0xfa0+102,4102,2,"}, 
  {"syscall","0xfa0,4000,1,i"}, 
  {"sysctl","0xfa0+149,4149,1,"}, 
  {"time","0xfa0,4013,1,p"}, 
  {"unlink","0xfa0,4010,1,z"}, 
  {"utime","0xfa0,4030,2,"}, 
  {"waitpid","0xfa0,4007,3,ipx"}, 
  {"write","0xfa0,4004,3,izi"}, 
  {NULL, NULL}
};
// 0x563b38765e60
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_linux_mips_32_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_linux_mips_32_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_linux_mips_32(x,y) gperf_linux_mips_32_hash(x)
const unsigned int gperf_linux_mips_32_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_linux_mips_32 = {
  .name = "linux-mips-32",
  .get = &gperf_linux_mips_32_get,
  .hash = &gperf_linux_mips_32_hash,
  .foreach = &gperf_linux_mips_32_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_linux_mips_32.get)("foo");
	printf ("%s\n", s);
}
#endif
