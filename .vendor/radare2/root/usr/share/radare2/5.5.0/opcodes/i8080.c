// SDB-CGEN V1.8.3
// gcc -DMAIN=1 i8080.c ; ./a.out > i8080.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"aci","add immediate to a with carry"}, 
  {"adc","add register to a with carry"}, 
  {"add","add register to a"}, 
  {"adi","add immediate to a"}, 
  {"ana","and register with a"}, 
  {"ani","and immediate with a"}, 
  {"call","unconditional subroutine call"}, 
  {"cccc","conditional subroutine call"}, 
  {"cma","compliment a"}, 
  {"cmc","compliment carry flag"}, 
  {"cmp","compare register with a"}, 
  {"cpi","compare immediate with a"}, 
  {"daa","decimal adjust accumulator"}, 
  {"dad","add register pair to hl (16 bit add)"}, 
  {"dcr","decrement register"}, 
  {"dcx","decrement register pair"}, 
  {"di","disable interrupts"}, 
  {"ei","enable interrupts"}, 
  {"hlt","halt processor"}, 
  {"in","read input port into a"}, 
  {"inr","increment register"}, 
  {"inx","increment register pair"}, 
  {"jccc","conditional jump"}, 
  {"jmp","unconditional jump"}, 
  {"lda","load a from memory"}, 
  {"ldax","load indirect through bc or de"}, 
  {"lhld","load h:l from memory"}, 
  {"lxi","load register pair immediate"}, 
  {"mov","move register to register"}, 
  {"mvi","move immediate to register"}, 
  {"nop","no operation"}, 
  {"ora","or  register with a"}, 
  {"ori","or  immediate with a"}, 
  {"out","write a to output port"}, 
  {"pchl","jump to address in h:l"}, 
  {"pop","pop  register pair from the stack"}, 
  {"push","push register pair on the stack"}, 
  {"ral","rotate a left through carry"}, 
  {"rar","rotate a right through carry"}, 
  {"rccc","conditional return from subroutine"}, 
  {"ret","unconditional return from subroutine"}, 
  {"rlc","rotate a left"}, 
  {"rrc","rotate a right"}, 
  {"rst","restart (call n*8)"}, 
  {"sbb","subtract register from a with borrow"}, 
  {"sbi","subtract immediate from a with borrow"}, 
  {"shld","store h:l to memory"}, 
  {"sphl","set sp to content of h:l"}, 
  {"sta","store a to memory"}, 
  {"stax","store indirect through bc or de"}, 
  {"stc","set carry flag"}, 
  {"sub","subtract register from a"}, 
  {"sui","subtract immediate from a"}, 
  {"xchg","de and hl content"}, 
  {"xra","exclusive or register with a"}, 
  {"xri","exclusiveor immediate with a"}, 
  {"xthl","swap h:l with top word on stack"}, 
  {NULL, NULL}
};
// 0x55dae0a5ea80
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_i8080_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_i8080_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_i8080(x,y) gperf_i8080_hash(x)
const unsigned int gperf_i8080_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_i8080 = {
  .name = "i8080",
  .get = &gperf_i8080_get,
  .hash = &gperf_i8080_hash,
  .foreach = &gperf_i8080_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_i8080.get)("foo");
	printf ("%s\n", s);
}
#endif
