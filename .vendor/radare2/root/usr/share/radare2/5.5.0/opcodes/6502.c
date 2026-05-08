// SDB-CGEN V1.8.3
// gcc -DMAIN=1 6502.c ; ./a.out > 6502.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"adc","add memory to accumulator with carry"}, 
  {"and","\""}, 
  {"asl","shift left one bit (memory or accumulator)"}, 
  {"bcc","branch on carry clear"}, 
  {"bcs","branch on carry set"}, 
  {"beq","branch on result zero"}, 
  {"bit","test bits in memory with accumulator"}, 
  {"bmi","branch on result minus"}, 
  {"bne","branch on result not zero"}, 
  {"bpl","branch on result plus"}, 
  {"brk","force break"}, 
  {"bvc","branch on overflow clear"}, 
  {"bvs","branch on overflow set"}, 
  {"clc","clear carry flag"}, 
  {"cld","clear decimal mode"}, 
  {"cli","clear interrupt disable bit"}, 
  {"clv","clear overflow flag"}, 
  {"cmp","compare memory and accumulator"}, 
  {"cpx","compare memory and index x"}, 
  {"cpy","compare memory and index y"}, 
  {"dec","decrement memory by one"}, 
  {"dex","decrement index x by one"}, 
  {"dey","decrement index y by one"}, 
  {"eor","\""}, 
  {"inc","increment memory by one"}, 
  {"inx","increment index x by one"}, 
  {"iny","increment index y by one"}, 
  {"jmp","jump to new location"}, 
  {"jsr","jump to new location saving return address"}, 
  {"lda","load accumulator with memory"}, 
  {"ldx","load index x with memory"}, 
  {"ldy","load index y with memory"}, 
  {"lsr","shift right one bit (memory or accumulator)"}, 
  {"nop","no operation"}, 
  {"ora","\""}, 
  {"pha","push accumulator on stack"}, 
  {"php","push processor status on stack"}, 
  {"pla","pull accumulator from stack"}, 
  {"plp","pull processor status from stack"}, 
  {"rol","rotate one bit left (memory or accumulator)"}, 
  {"ror","rotate one bit right (memory or accumulator)"}, 
  {"rti","return from interrupt"}, 
  {"rts","return from subroutine"}, 
  {"sbc","subtract memory from accumulator with borrow"}, 
  {"sec","set carry flag"}, 
  {"sed","set decimal mode"}, 
  {"sei","set interrupt disable status"}, 
  {"sta","store accumulator in memory"}, 
  {"stx","store index x in memory"}, 
  {"sty","store index y in memory"}, 
  {"tax","transfer accumulator to index x"}, 
  {"tay","transfer accumulator to index y"}, 
  {"tsx","transfer stack pointer to index x"}, 
  {"txa","transfer index x to accumulator"}, 
  {"txs","transfer index x to stack pointer"}, 
  {"tya","transfer index y to accumulator"}, 
  {NULL, NULL}
};
// 0x55b1883eaa30
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_6502_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_6502_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_6502(x,y) gperf_6502_hash(x)
const unsigned int gperf_6502_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_6502 = {
  .name = "6502",
  .get = &gperf_6502_get,
  .hash = &gperf_6502_hash,
  .foreach = &gperf_6502_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_6502.get)("foo");
	printf ("%s\n", s);
}
#endif
