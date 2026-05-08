// SDB-CGEN V1.8.3
// gcc -DMAIN=1 SHELL.c ; ./a.out > SHELL.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","REGOPENKEY"}, 
  {"101","DLLENTRYPOINT"}, 
  {"102","REGISTERSHELLHOOK"}, 
  {"11","DRAGQUERYFILE"}, 
  {"12","DRAGFINISH"}, 
  {"13","DRAGQUERYPOINT"}, 
  {"157","RESTARTDIALOG"}, 
  {"166","PICKICONDLG"}, 
  {"2","REGCREATEKEY"}, 
  {"20","SHELLEXECUTE"}, 
  {"21","FINDEXECUTABLE"}, 
  {"22","SHELLABOUT"}, 
  {"262","DRIVETYPE"}, 
  {"263","SH16TO32DRIVEIOCTL"}, 
  {"264","SH16TO32INT2526"}, 
  {"3","REGCLOSEKEY"}, 
  {"300","SHGETFILEINFO"}, 
  {"34","EXTRACTICON"}, 
  {"36","EXTRACTASSOCIATEDICON"}, 
  {"37","DOENVIRONMENTSUBST"}, 
  {"38","FINDENVIRONMENTSTRING"}, 
  {"39","INTERNALEXTRACTICON"}, 
  {"4","REGDELETEKEY"}, 
  {"40","EXTRACTICONEX"}, 
  {"400","SHFORMATDRIVE"}, 
  {"401","SHCHECKDRIVE"}, 
  {"402","_RUNDLLCHECKDRIVE"}, 
  {"5","REGSETVALUE"}, 
  {"6","REGQUERYVALUE"}, 
  {"7","REGENUMKEY"}, 
  {"8","WEP"}, 
  {"9","DRAGACCEPTFILES"}, 
  {"98","SHL3216_THUNKDATA16"}, 
  {"99","SHL1632_THUNKDATA16"}, 
  {NULL, NULL}
};
// 0x55cf57a32350
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_SHELL_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_SHELL_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_SHELL(x,y) gperf_SHELL_hash(x)
const unsigned int gperf_SHELL_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_SHELL = {
  .name = "SHELL",
  .get = &gperf_SHELL_get,
  .hash = &gperf_SHELL_hash,
  .foreach = &gperf_SHELL_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_SHELL.get)("foo");
	printf ("%s\n", s);
}
#endif
