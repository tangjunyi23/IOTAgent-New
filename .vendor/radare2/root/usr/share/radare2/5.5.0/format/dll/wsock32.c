// SDB-CGEN V1.8.3
// gcc -DMAIN=1 wsock32.c ; ./a.out > wsock32.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","accept"}, 
  {"10","inet_addr"}, 
  {"1000","WSApSetPostRoutine"}, 
  {"101","WSAAsyncSelect"}, 
  {"102","WSAAsyncGetHostByAddr"}, 
  {"103","WSAAsyncGetHostByName"}, 
  {"104","WSAAsyncGetProtoByNumber"}, 
  {"105","WSAAsyncGetProtoByName"}, 
  {"106","WSAAsyncGetServByPort"}, 
  {"107","WSAAsyncGetServByName"}, 
  {"108","WSACancelAsyncRequest"}, 
  {"109","WSASetBlockingHook"}, 
  {"11","inet_ntoa"}, 
  {"110","WSAUnhookBlockingHook"}, 
  {"1100","inet_network"}, 
  {"1101","getnetbyname"}, 
  {"1102","rcmd"}, 
  {"1103","rexec"}, 
  {"1104","rresvport"}, 
  {"1105","sethostname"}, 
  {"1106","dn_expand"}, 
  {"1107","WSARecvEx"}, 
  {"1108","s_perror"}, 
  {"1109","GetAddressByNameA"}, 
  {"111","WSAGetLastError"}, 
  {"1110","GetAddressByNameW"}, 
  {"1111","EnumProtocolsA"}, 
  {"1112","EnumProtocolsW"}, 
  {"1113","GetTypeByNameA"}, 
  {"1114","GetTypeByNameW"}, 
  {"1115","GetNameByTypeA"}, 
  {"1116","GetNameByTypeW"}, 
  {"1117","SetServiceA"}, 
  {"1118","SetServiceW"}, 
  {"1119","GetServiceA"}, 
  {"112","WSASetLastError"}, 
  {"1120","GetServiceW"}, 
  {"113","WSACancelBlockingCall"}, 
  {"1130","NPLoadNameSpaces"}, 
  {"114","WSAIsBlocking"}, 
  {"1140","TransmitFile"}, 
  {"1141","AcceptEx"}, 
  {"1142","GetAcceptExSockaddrs"}, 
  {"115","WSAStartup"}, 
  {"116","WSACleanup"}, 
  {"12","ioctlsocket"}, 
  {"13","listen"}, 
  {"14","ntohl"}, 
  {"15","ntohs"}, 
  {"151","__WSAFDIsSet"}, 
  {"16","recv"}, 
  {"17","recvfrom"}, 
  {"18","select"}, 
  {"19","send"}, 
  {"2","bind"}, 
  {"20","sendto"}, 
  {"21","setsockopt"}, 
  {"22","shutdown"}, 
  {"23","socket"}, 
  {"24","MigrateWinsockConfiguration"}, 
  {"3","closesocket"}, 
  {"4","connect"}, 
  {"5","getpeername"}, 
  {"500","WEP"}, 
  {"51","gethostbyaddr"}, 
  {"52","gethostbyname"}, 
  {"53","getprotobyname"}, 
  {"54","getprotobynumber"}, 
  {"55","getservbyname"}, 
  {"56","getservbyport"}, 
  {"57","gethostname"}, 
  {"6","getsockname"}, 
  {"7","getsockopt"}, 
  {"8","htonl"}, 
  {"9","htons"}, 
  {NULL, NULL}
};
// 0x557871e5f8f0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_wsock32_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_wsock32_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_wsock32(x,y) gperf_wsock32_hash(x)
const unsigned int gperf_wsock32_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_wsock32 = {
  .name = "wsock32",
  .get = &gperf_wsock32_get,
  .hash = &gperf_wsock32_hash,
  .foreach = &gperf_wsock32_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_wsock32.get)("foo");
	printf ("%s\n", s);
}
#endif
