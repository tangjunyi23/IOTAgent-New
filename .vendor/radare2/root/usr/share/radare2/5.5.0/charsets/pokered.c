// SDB-CGEN V1.8.3
// gcc -DMAIN=1 pokered.c ; ./a.out > pokered.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"0x00","<NULL>"}, 
  {"0x49","<PAGE>"}, 
  {"0x4a","<pkmn>"}, 
  {"0x4b","<_CONT>"}, 
  {"0x4c","<SCROLL>"}, 
  {"0x4e","<NEXT>"}, 
  {"0x4f","<LINE>"}, 
  {"0x50","@"}, 
  {"0x51","<PARA>"}, 
  {"0x52","<PLAYER>"}, 
  {"0x53","<RIVAL>"}, 
  {"0x54","#"}, 
  {"0x55","<CONT>"}, 
  {"0x56","<……>"}, 
  {"0x57","<DONE>"}, 
  {"0x58","<PROMPT>"}, 
  {"0x59","<TARGET>"}, 
  {"0x5a","<USER>"}, 
  {"0x5b","<PC>"}, 
  {"0x5c","<TM>"}, 
  {"0x5d","<TRAINER>"}, 
  {"0x5e","<ROCKET>"}, 
  {"0x5f","<DEXDEND>"}, 
  {"0x60","<BOLD_A>"}, 
  {"0x61","<BOLD_B>"}, 
  {"0x62","<BOLD_C>"}, 
  {"0x63","<BOLD_D>"}, 
  {"0x64","<BOLD_E>"}, 
  {"0x65","<BOLD_F>"}, 
  {"0x66","<BOLD_G>"}, 
  {"0x67","<BOLD_H>"}, 
  {"0x68","<BOLD_I>"}, 
  {"0x69","<BOLD_V>"}, 
  {"0x6a","<BOLD_S>"}, 
  {"0x6b","<BOLD_L>"}, 
  {"0x6c","<BOLD_M>"}, 
  {"0x6d","<COLON>"}, 
  {"0x7f","-"}, 
  {"0x80","A"}, 
  {"0x81","B"}, 
  {"0x82","C"}, 
  {"0x83","D"}, 
  {"0x84","E"}, 
  {"0x85","F"}, 
  {"0x86","G"}, 
  {"0x87","H"}, 
  {"0x88","I"}, 
  {"0x89","J"}, 
  {"0x8a","K"}, 
  {"0x8b","L"}, 
  {"0x8c","M"}, 
  {"0x8d","N"}, 
  {"0x8e","O"}, 
  {"0x8f","P"}, 
  {"0x90","Q"}, 
  {"0x91","R"}, 
  {"0x92","S"}, 
  {"0x93","T"}, 
  {"0x94","U"}, 
  {"0x95","V"}, 
  {"0x96","W"}, 
  {"0x97","X"}, 
  {"0x98","Y"}, 
  {"0x99","Z"}, 
  {"0x9a","("}, 
  {"0x9b",")"}, 
  {"0x9c",":"}, 
  {"0x9d",";"}, 
  {"0x9e","["}, 
  {"0x9f","]"}, 
  {"0xa0","a"}, 
  {"0xa1","b"}, 
  {"0xa2","c"}, 
  {"0xa3","d"}, 
  {"0xa4","e"}, 
  {"0xa5","f"}, 
  {"0xa6","g"}, 
  {"0xa7","h"}, 
  {"0xa8","i"}, 
  {"0xa9","j"}, 
  {"0xaa","k"}, 
  {"0xab","l"}, 
  {"0xac","m"}, 
  {"0xad","n"}, 
  {"0xae","o"}, 
  {"0xaf","p"}, 
  {"0xb0","q"}, 
  {"0xb1","r"}, 
  {"0xb2","s"}, 
  {"0xb3","t"}, 
  {"0xb4","u"}, 
  {"0xb5","v"}, 
  {"0xb6","w"}, 
  {"0xb7","x"}, 
  {"0xb8","y"}, 
  {"0xb9","z"}, 
  {"0xbb","'d"}, 
  {"0xbc","'l"}, 
  {"0xbd","'s"}, 
  {"0xe0","é"}, 
  {"0xe3","-"}, 
  {"0xe4","'r"}, 
  {"0xe6","?"}, 
  {"0xe7","!"}, 
  {"0xf6","0"}, 
  {"0xf7","1"}, 
  {"0xf8","2"}, 
  {"0xf9","3"}, 
  {"0xfa","4"}, 
  {"0xfb","5"}, 
  {"0xfc","6"}, 
  {"0xfd","7"}, 
  {"0xfe","8"}, 
  {"0xff","9"}, 
  {NULL, NULL}
};
// 0x563a03fd6100
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_pokered_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_pokered_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_pokered(x,y) gperf_pokered_hash(x)
const unsigned int gperf_pokered_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_pokered = {
  .name = "pokered",
  .get = &gperf_pokered_get,
  .hash = &gperf_pokered_hash,
  .foreach = &gperf_pokered_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_pokered.get)("foo");
	printf ("%s\n", s);
}
#endif
