// SDB-CGEN V1.8.3
// gcc -DMAIN=1 DSKMAINT.c ; ./a.out > DSKMAINT.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"10","DMAINT_GETFIXOPTIONS"}, 
  {"11","DMAINT_FIXDRIVE"}, 
  {"12","DMAINT_GETOPTIMIZEOPTIONS"}, 
  {"13","DMAINT_OPTIMIZEDRIVE"}, 
  {"14","DMAINT_UNFORMATDRIVE"}, 
  {"15","DMAINT_CHECKDRIVESETUP"}, 
  {"2","DMAINT_GETENGINEDRIVEINFO"}, 
  {"3","DMAINT_GETFILESYSPARAMETERS"}, 
  {"4","DMAINT_READSECTOR"}, 
  {"5","DMAINT_WRITESECTOR"}, 
  {"6","DMAINT_READFILESYSSTRUC"}, 
  {"7","DMAINT_WRITEFILESYSSTRUC"}, 
  {"8","DMAINT_GETFORMATOPTIONS"}, 
  {"9","DMAINT_FORMATDRIVE"}, 
  {NULL, NULL}
};
// 0x5616fe4b6020
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_DSKMAINT_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_DSKMAINT_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_DSKMAINT(x,y) gperf_DSKMAINT_hash(x)
const unsigned int gperf_DSKMAINT_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_DSKMAINT = {
  .name = "DSKMAINT",
  .get = &gperf_DSKMAINT_get,
  .hash = &gperf_DSKMAINT_hash,
  .foreach = &gperf_DSKMAINT_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_DSKMAINT.get)("foo");
	printf ("%s\n", s);
}
#endif
