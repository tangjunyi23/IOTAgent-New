// SDB-CGEN V1.8.3
// gcc -DMAIN=1 WINSOCK.c ; ./a.out > WINSOCK.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","ACCEPT"}, 
  {"10","INET_ADDR"}, 
  {"1001","WSCONTROL"}, 
  {"1002","WSTASKCLEANUP"}, 
  {"101","WSAASYNCSELECT"}, 
  {"102","WSAASYNCGETHOSTBYADDR"}, 
  {"103","WSAASYNCGETHOSTBYNAME"}, 
  {"104","WSAASYNCGETPROTOBYNUMBER"}, 
  {"105","WSAASYNCGETPROTOBYNAME"}, 
  {"106","WSAASYNCGETSERVBYPORT"}, 
  {"107","WSAASYNCGETSERVBYNAME"}, 
  {"108","WSACANCELASYNCREQUEST"}, 
  {"109","WSASETBLOCKINGHOOK"}, 
  {"11","INET_NTOA"}, 
  {"110","WSAUNHOOKBLOCKINGHOOK"}, 
  {"1100","INET_NETWORK"}, 
  {"1101","GETNETBYNAME"}, 
  {"1107","WSARECVEX"}, 
  {"111","WSAGETLASTERROR"}, 
  {"112","WSASETLASTERROR"}, 
  {"113","WSACANCELBLOCKINGCALL"}, 
  {"114","WSAISBLOCKING"}, 
  {"115","WSASTARTUP"}, 
  {"116","WSACLEANUP"}, 
  {"12","IOCTLSOCKET"}, 
  {"13","LISTEN"}, 
  {"14","NTOHL"}, 
  {"15","NTOHS"}, 
  {"151","__WSAFDISSET"}, 
  {"16","RECV"}, 
  {"17","RECVFROM"}, 
  {"18","SELECT"}, 
  {"19","SEND"}, 
  {"2","BIND"}, 
  {"20","SENDTO"}, 
  {"21","SETSOCKOPT"}, 
  {"22","SHUTDOWN"}, 
  {"23","SOCKET"}, 
  {"24","___EXPORTEDSTUB"}, 
  {"3","CLOSESOCKET"}, 
  {"4","CONNECT"}, 
  {"5","GETPEERNAME"}, 
  {"500","WEP"}, 
  {"51","GETHOSTBYADDR"}, 
  {"52","GETHOSTBYNAME"}, 
  {"53","GETPROTOBYNAME"}, 
  {"54","GETPROTOBYNUMBER"}, 
  {"55","GETSERVBYNAME"}, 
  {"56","GETSERVBYPORT"}, 
  {"57","GETHOSTNAME"}, 
  {"6","GETSOCKNAME"}, 
  {"7","GETSOCKOPT"}, 
  {"8","HTONL"}, 
  {"9","HTONS"}, 
  {NULL, NULL}
};
// 0x563d3f3f6510
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_WINSOCK_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_WINSOCK_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_WINSOCK(x,y) gperf_WINSOCK_hash(x)
const unsigned int gperf_WINSOCK_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_WINSOCK = {
  .name = "WINSOCK",
  .get = &gperf_WINSOCK_get,
  .hash = &gperf_WINSOCK_hash,
  .foreach = &gperf_WINSOCK_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_WINSOCK.get)("foo");
	printf ("%s\n", s);
}
#endif
