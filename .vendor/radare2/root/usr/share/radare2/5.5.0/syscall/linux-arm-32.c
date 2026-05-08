// SDB-CGEN V1.8.3
// gcc -DMAIN=1 linux_arm_32.c ; ./a.out > linux_arm_32.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"_","0x900000"}, 
  {"access","0x900000,33,2,"}, 
  {"brk","0x900000,45,1,"}, 
  {"chdir","0x900000,12,1,z"}, 
  {"chmod","0x900000,15,1,zx"}, 
  {"clone","0x900000,120,4,"}, 
  {"close","0x900000,6,1,i"}, 
  {"creat","0x900000,8,2,zx"}, 
  {"dup","0x900000,41,2,"}, 
  {"execve","0x900000,11,3,zzz"}, 
  {"exit","0x900000,1,1,i"}, 
  {"exit_group","0x900000,252,1,"}, 
  {"fcntl64","0x900000,221,3,"}, 
  {"fork","0x900000,2,0,"}, 
  {"fstat64","0x900000,197,2,"}, 
  {"get_thread_area","0x900000,244,2,"}, 
  {"getpid","0x900000,20,0,"}, 
  {"gettid","0x900000,224,0,"}, 
  {"getuid","0x900000,24,0,"}, 
  {"ioctl","0x900000,54,3,"}, 
  {"kill","0x900000,37,2,"}, 
  {"lchown","0x900000,16,1,zii"}, 
  {"link","0x900000,9,2,zz"}, 
  {"mknod","0x900000,14,1,zxi"}, 
  {"mmap","0x900000,90,6,"}, 
  {"mmap2","0x900000,192,6,"}, 
  {"mprotect","0x900000,125,3,"}, 
  {"munmap","0x900000,91,1,"}, 
  {"open","0x900000,5,3,zxx"}, 
  {"ptrace","0x900000,26,4,"}, 
  {"read","0x900000,3,3,ipi"}, 
  {"rt_sigaction","0x900000,174,3,"}, 
  {"rt_sigprocmask","0x900000,175,3,"}, 
  {"set_thread_area","0x900000,243,2,"}, 
  {"setuid","0x900000,23,1,i"}, 
  {"signal","0x900000,48,2,"}, 
  {"sigreturn","0x900000,119,1,"}, 
  {"socketcall","0x900000,102,2,"}, 
  {"sysctl","0x900000,149,1,"}, 
  {"time","0x900000,13,1,p"}, 
  {"unlink","0x900000,10,1,z"}, 
  {"utime","0x900000,30,2,"}, 
  {"vfork","0x900000,1071,0,"}, 
  {"waitpid","0x900000,7,3,ipx"}, 
  {"write","0x900000,4,3,izi"}, 
  {NULL, NULL}
};
// 0x564043c6ce60
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_linux_arm_32_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_linux_arm_32_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_linux_arm_32(x,y) gperf_linux_arm_32_hash(x)
const unsigned int gperf_linux_arm_32_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_linux_arm_32 = {
  .name = "linux-arm-32",
  .get = &gperf_linux_arm_32_get,
  .hash = &gperf_linux_arm_32_hash,
  .foreach = &gperf_linux_arm_32_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_linux_arm_32.get)("foo");
	printf ("%s\n", s);
}
#endif
