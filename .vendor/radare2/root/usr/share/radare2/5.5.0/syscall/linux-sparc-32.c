// SDB-CGEN V1.8.3
// gcc -DMAIN=1 linux_sparc_32.c ; ./a.out > linux_sparc_32.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"_","0x10"}, 
  {"access","0x10,33,2,"}, 
  {"brk","0x10,45,1,"}, 
  {"chdir","0x10,12,1,z"}, 
  {"clone","0x10,120,4,"}, 
  {"close","0x10,6,1,i"}, 
  {"creat","0x10,8,2,zx"}, 
  {"dup","0x10,41,2,"}, 
  {"execve","0x10,11,3,zzz"}, 
  {"exit","0x10,1,1,i"}, 
  {"fork","0x10,2,0,"}, 
  {"getpid","0x10,20,0,"}, 
  {"getuid","0x10,24,0,"}, 
  {"ioctl","0x10,54,3,"}, 
  {"kill","0x10,37,2,"}, 
  {"link","0x10,9,2,zz"}, 
  {"mmap","0x10,90,6,"}, 
  {"mmap2","0x10,192,6,"}, 
  {"mprotect","0x10,125,3,"}, 
  {"munmap","0x10,91,1,"}, 
  {"open","0x10,5,3,zxx"}, 
  {"ptrace","0x10,26,4,"}, 
  {"read","0x10,3,3,ipi"}, 
  {"rt_sigaction","0x10,174,3,"}, 
  {"rt_sigprocmask","0x10,175,3,"}, 
  {"setuid","0x10,23,1,i"}, 
  {"signal","0x10,48,2,"}, 
  {"sigreturn","0x10,119,1,"}, 
  {"socketcall","0x10,102,2,"}, 
  {"sysctl","0x10,149,1,"}, 
  {"unlink","0x10,10,1,z"}, 
  {"utime","0x10,30,2,"}, 
  {"waitpid","0x10,7,3,ipx"}, 
  {"write","0x10,4,3,izi"}, 
  {NULL, NULL}
};
// 0x5578d77375d0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_linux_sparc_32_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_linux_sparc_32_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_linux_sparc_32(x,y) gperf_linux_sparc_32_hash(x)
const unsigned int gperf_linux_sparc_32_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_linux_sparc_32 = {
  .name = "linux-sparc-32",
  .get = &gperf_linux_sparc_32_get,
  .hash = &gperf_linux_sparc_32_hash,
  .foreach = &gperf_linux_sparc_32_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_linux_sparc_32.get)("foo");
	printf ("%s\n", s);
}
#endif
