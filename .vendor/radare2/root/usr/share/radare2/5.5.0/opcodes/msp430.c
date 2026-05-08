// SDB-CGEN V1.8.3
// gcc -DMAIN=1 msp430.c ; ./a.out > msp430.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"adc","add constant"}, 
  {"adc.b","add carry to destination"}, 
  {"add","add source to destination"}, 
  {"addc","add source and carry to destinatio"}, 
  {"and","logical and"}, 
  {"bic","bit clear"}, 
  {"bis","bit set"}, 
  {"bit","test bits of source and destination"}, 
  {"br","branch to"}, 
  {"call","subroutine call"}, 
  {"clr","clear destination"}, 
  {"clr.b","clear destination"}, 
  {"clrn","clear negative bit"}, 
  {"clrz","clear zero bit"}, 
  {"cmp","compare"}, 
  {"dadc","decimal add carry to destination"}, 
  {"dadc.b","decimal add carry to destination"}, 
  {"dadd","decimal add source to destination (with carry)"}, 
  {"dec","decrement destination"}, 
  {"dec.b","decrement destination"}, 
  {"decd","decrement destination twice"}, 
  {"decd.b","decrement destination twice"}, 
  {"dint","disable interrupts"}, 
  {"eint","enable interrupts"}, 
  {"inc","increment destination"}, 
  {"inc.b","increment destination"}, 
  {"incd","increment destination twice"}, 
  {"incd.b","increment destination twice"}, 
  {"inv","invert bits in destination"}, 
  {"inv.b","invert bits in destination"}, 
  {"jc","jump if carry/higher or same"}, 
  {"jeq","jump if equal/zero"}, 
  {"jge","jump if greater or equal"}, 
  {"jl","jump if less"}, 
  {"jmp","jump"}, 
  {"jn","jump if negative"}, 
  {"jnc","jump if no carry/lower"}, 
  {"jnz","jump if not equal/zero"}, 
  {"mov","move source to destination"}, 
  {"nop","no operation"}, 
  {"pop","pop word from stack"}, 
  {"pop.b","pop byte from stack"}, 
  {"push","push value onto stac"}, 
  {"ret","return from subroutine"}, 
  {"reti","return from interrup"}, 
  {"rla","rotate left"}, 
  {"rla.b","rotate left"}, 
  {"rlc","rotate left through carry"}, 
  {"rlc.b","rotate left through carry"}, 
  {"rra","rotate right arithmetiс"}, 
  {"rrc","rotate right through carry"}, 
  {"sbc","subtract source and borrow"}, 
  {"sbc.b","subtract source and borrow"}, 
  {"setc","set carry flag"}, 
  {"setn","set negative flag"}, 
  {"setz","set zero flag"}, 
  {"sub","subtract source from destination"}, 
  {"subc","subtract source from destination (with carry)"}, 
  {"swpb","swap bytes"}, 
  {"sxt","sign extend byte to word"}, 
  {"tst","test destination"}, 
  {"tst.b","test destination"}, 
  {"xor","exclusive or"}, 
  {NULL, NULL}
};
// 0x56388eab9370
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_msp430_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_msp430_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_msp430(x,y) gperf_msp430_hash(x)
const unsigned int gperf_msp430_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_msp430 = {
  .name = "msp430",
  .get = &gperf_msp430_get,
  .hash = &gperf_msp430_hash,
  .foreach = &gperf_msp430_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_msp430.get)("foo");
	printf ("%s\n", s);
}
#endif
