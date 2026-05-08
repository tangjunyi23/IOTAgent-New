// SDB-CGEN V1.8.3
// gcc -DMAIN=1 8051.c ; ./a.out > 8051.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"acall","absolute call"}, 
  {"add","add"}, 
  {"addc","add with carry"}, 
  {"ajmp","absolute jump"}, 
  {"anl","logical and"}, 
  {"cjne","compare and jump if not equal"}, 
  {"clr","clear"}, 
  {"cpl","complement"}, 
  {"da","decimal-adjust accumulator after addition"}, 
  {"dec","decrement"}, 
  {"div","divide accumulator by b register"}, 
  {"djnz","decrement and jump if not zero"}, 
  {"inc","increment"}, 
  {"jb","jump if bit set"}, 
  {"jbc","jump if bit is set and clear bit"}, 
  {"jc","jump if carry is set"}, 
  {"jmp","jump indirect"}, 
  {"jnb","jump if bit not set"}, 
  {"jnc","jump if carry not set"}, 
  {"jnz","jump if accumulator not zero"}, 
  {"jz","jump if accumulator zero"}, 
  {"lcall","long call"}, 
  {"ljmp","long jump"}, 
  {"mov","move "}, 
  {"movc","move from code or program memory to accumulator"}, 
  {"movx","move between external memory and accumulator"}, 
  {"mul","multiply accumulator and b register"}, 
  {"nop","no operation"}, 
  {"orl","logical or"}, 
  {"pop","pop from stack"}, 
  {"push","push onto stack"}, 
  {"ret","return from subroutine"}, 
  {"reti","return from interrupt"}, 
  {"rl","rotate accumulator left"}, 
  {"rlc","rotate accumulator left through carry"}, 
  {"rr","rotate accumulator right"}, 
  {"rrc","rotate accumulator right through carry"}, 
  {"setb","set bit"}, 
  {"sjmp","short jump (relative addr)"}, 
  {"subb","subtract with borrow"}, 
  {"swap","swap nibbles within the accumulator"}, 
  {"xch","exchange"}, 
  {"xchd","exchange low-order nibbles between accumulator and RAM location"}, 
  {"xrl","logical exclusive-or"}, 
  {NULL, NULL}
};
// 0x5608ff5a8ec0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_8051_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_8051_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_8051(x,y) gperf_8051_hash(x)
const unsigned int gperf_8051_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_8051 = {
  .name = "8051",
  .get = &gperf_8051_get,
  .hash = &gperf_8051_hash,
  .foreach = &gperf_8051_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_8051.get)("foo");
	printf ("%s\n", s);
}
#endif
