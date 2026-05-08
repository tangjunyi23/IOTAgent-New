// SDB-CGEN V1.8.3
// gcc -DMAIN=1 SOUND.c ; ./a.out > SOUND.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","OPENSOUND"}, 
  {"10","STOPSOUND"}, 
  {"11","WAITSOUNDSTATE"}, 
  {"12","SYNCALLVOICES"}, 
  {"13","COUNTVOICENOTES"}, 
  {"14","GETTHRESHOLDEVENT"}, 
  {"15","GETTHRESHOLDSTATUS"}, 
  {"16","SETVOICETHRESHOLD"}, 
  {"17","DOBEEP"}, 
  {"18","WEP"}, 
  {"2","CLOSESOUND"}, 
  {"3","SETVOICEQUEUESIZE"}, 
  {"4","SETVOICENOTE"}, 
  {"5","SETVOICEACCENT"}, 
  {"6","SETVOICEENVELOPE"}, 
  {"7","SETSOUNDNOISE"}, 
  {"8","SETVOICESOUND"}, 
  {"9","STARTSOUND"}, 
  {NULL, NULL}
};
// 0x556171f90520
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_SOUND_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_SOUND_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_SOUND(x,y) gperf_SOUND_hash(x)
const unsigned int gperf_SOUND_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_SOUND = {
  .name = "SOUND",
  .get = &gperf_SOUND_get,
  .hash = &gperf_SOUND_hash,
  .foreach = &gperf_SOUND_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_SOUND.get)("foo");
	printf ("%s\n", s);
}
#endif
