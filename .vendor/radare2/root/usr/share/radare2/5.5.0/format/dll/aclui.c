// SDB-CGEN V1.8.3
// gcc -DMAIN=1 aclui.c ; ./a.out > aclui.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","CreateSecurityPage"}, 
  {"16","IID_ISecurityInformation"}, 
  {"2","EditSecurity"}, 
  {"3","EditSecurityAdvanced"}, 
  {"4","EditResourceCondition"}, 
  {"5","EditConditionalAceClaims"}, 
  {"6","GetLocalizedStringForCondition"}, 
  {"7","GetTlsIndexForClaimDictionary"}, 
  {NULL, NULL}
};
// 0x5596a8043a40
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_aclui_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_aclui_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_aclui(x,y) gperf_aclui_hash(x)
const unsigned int gperf_aclui_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_aclui = {
  .name = "aclui",
  .get = &gperf_aclui_get,
  .hash = &gperf_aclui_hash,
  .foreach = &gperf_aclui_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_aclui.get)("foo");
	printf ("%s\n", s);
}
#endif
