// SDB-CGEN V1.8.3
// gcc -DMAIN=1 freebsd_x86_32.c ; ./a.out > freebsd_x86_32.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"_","0x80"}, 
  {"accept","0x80,30,4,"}, 
  {"access","0x80,33,2,"}, 
  {"acct","0x80,51,1,/*"}, 
  {"break","0x80,17,1,"}, 
  {"chdir","0x80,12,1,"}, 
  {"chflags","0x80,34,2,"}, 
  {"chmod","0x80,15,1,"}, 
  {"chown","0x80,16,1,"}, 
  {"chroot","0x80,61,1,"}, 
  {"clone","0x80,120,4,"}, 
  {"close","0x80,6,1,"}, 
  {"dup","0x80,41,2,"}, 
  {"execve","0x80,59,2,"}, 
  {"exit","0x80,1,1,"}, 
  {"exit_group","0x80,252,1,"}, 
  {"fchdir","0x80,13,1,"}, 
  {"fchflags","0x80,35,2,"}, 
  {"fcntl64","0x80,221,3,"}, 
  {"fork","0x80,2,0,"}, 
  {"fstat64","0x80,197,2,"}, 
  {"get_thread_area","0x80,244,2,"}, 
  {"getepid","0x80,43,0,"}, 
  {"getgid","0x80,47,0,"}, 
  {"getlogin","0x80,49,0,/*"}, 
  {"getpeername","0x80,31,3,"}, 
  {"getpid","0x80,20,0,"}, 
  {"getsockname","0x80,32,3,"}, 
  {"gettid","0x80,224,0,"}, 
  {"getuid","0x80,24,0,"}, 
  {"ioctl","0x80,54,3,"}, 
  {"kill","0x80,37,2,"}, 
  {"ktrace","0x80,45,4,"}, 
  {"link","0x80,9,2,"}, 
  {"mknod","0x80,14,1,"}, 
  {"mmap","0x80,90,6,"}, 
  {"mmap2","0x80,192,6,"}, 
  {"mount","0x80,21,0,"}, 
  {"mprotect","0x80,125,3,"}, 
  {"munmap","0x80,91,1,"}, 
  {"old_creat","0x80,8,2,"}, 
  {"old_execve","0x80,11,3,"}, 
  {"old_fsstat","0x80,18,1,"}, 
  {"old_lseek","0x80,19,1,"}, 
  {"open","0x80,5,3,"}, 
  {"pipe","0x80,42,1,"}, 
  {"profil","0x80,44,4,/*"}, 
  {"ptrace","0x80,26,4,"}, 
  {"read","0x80,3,3,"}, 
  {"readlink","0x80,58,1,"}, 
  {"reboot","0x80,55,1,"}, 
  {"recvfrom","0x80,29,4,"}, 
  {"recvmsg","0x80,27,4,"}, 
  {"revoke","0x80,56,1,/*"}, 
  {"rt_sigaction","0x80,174,3,"}, 
  {"rt_sigprocmask","0x80,175,3,"}, 
  {"sendmsg","0x80,28,4,"}, 
  {"set_thread_area","0x80,243,2,"}, 
  {"setlogin","0x80,50,1,/*"}, 
  {"setuid","0x80,23,1,"}, 
  {"sigaltstack","0x80,53,2,/*"}, 
  {"signal","0x80,48,2,"}, 
  {"sigreturn","0x80,119,1,"}, 
  {"socketcall","0x80,102,2,"}, 
  {"symlink","0x80,57,2,"}, 
  {"sync","0x80,36,0,"}, 
  {"syscall","0x80,0,4,sysnum"}, 
  {"sysctl","0x80,149,1,"}, 
  {"umask","0x80,60,1,"}, 
  {"unlink","0x80,10,1,"}, 
  {"unmount","0x80,22,0,"}, 
  {"wait4","0x80,7,3,"}, 
  {"write","0x80,4,3,"}, 
  {NULL, NULL}
};
// 0x55a56ba1ba30
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_freebsd_x86_32_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_freebsd_x86_32_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_freebsd_x86_32(x,y) gperf_freebsd_x86_32_hash(x)
const unsigned int gperf_freebsd_x86_32_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_freebsd_x86_32 = {
  .name = "freebsd-x86-32",
  .get = &gperf_freebsd_x86_32_get,
  .hash = &gperf_freebsd_x86_32_hash,
  .foreach = &gperf_freebsd_x86_32_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_freebsd_x86_32.get)("foo");
	printf ("%s\n", s);
}
#endif
