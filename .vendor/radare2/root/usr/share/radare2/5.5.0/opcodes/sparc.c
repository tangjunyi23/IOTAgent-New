// SDB-CGEN V1.8.3
// gcc -DMAIN=1 sparc.c ; ./a.out > sparc.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"add","addition"}, 
  {"addcc","adds to numbers and updates Z, N, V flags"}, 
  {"addx","add with carry"}, 
  {"and","binary and"}, 
  {"ba","branch always"}, 
  {"ba_a","branch always"}, 
  {"bcc","branch on carry clear"}, 
  {"bcc_a_pn","branch if carry bit is clear"}, 
  {"bcs","branch on carry set"}, 
  {"bcs_a_pn","branch if carry bit is set"}, 
  {"be","branch on equal"}, 
  {"be_pn","branch if equal"}, 
  {"bg","branch on greater"}, 
  {"bge","branch on greater or equal"}, 
  {"bgu","branch on greater unsigned"}, 
  {"bl","branch on less"}, 
  {"ble","branch on less or equal"}, 
  {"bleu","branch on less or equal unsigned"}, 
  {"bn","branch never"}, 
  {"bne","branch on not equal"}, 
  {"bne_pn","branch if not equal"}, 
  {"bneg","branch on negative"}, 
  {"bpos","branch on positive"}, 
  {"brgez","branch on register greater than or equal to zero"}, 
  {"brgz","branch on register greater than zero"}, 
  {"brlez","branch on register less than or equal to zero"}, 
  {"brlz","branch on register less than zero"}, 
  {"brnz","branch on register not zero"}, 
  {"brz","branch on register zero"}, 
  {"bvc","branch on overflow clear"}, 
  {"bvs","branch on overflow set"}, 
  {"call","call a subroutine, saving return address in o7"}, 
  {"cas","compare & swap"}, 
  {"casa","compare and swap word from alternate space"}, 
  {"casl","cas little-endian"}, 
  {"casx","cas extended"}, 
  {"casxa","compare and swap extended from alternate space"}, 
  {"casxl","cas little-endian, extended"}, 
  {"clruw","copy and clear upper word"}, 
  {"clrx","clear extended word"}, 
  {"cmp","sets appropriate condition codes"}, 
  {"fabsd","absolute value double"}, 
  {"fabsq","absolute value quad"}, 
  {"fbe","branch on equal"}, 
  {"fbg","branch on greater"}, 
  {"fbge","branch on greater or equal"}, 
  {"fbl","branch on less"}, 
  {"fble","branch on less or equal"}, 
  {"fblg","branch on less or greater"}, 
  {"fbn","branch always"}, 
  {"fbne","branch on not equal"}, 
  {"fbo","branch on ordered"}, 
  {"fbu","branch on unordered"}, 
  {"fbue","branch on unordered or equal"}, 
  {"fbug","branch on unordered or greater"}, 
  {"fbuge","branch on unordered or greater"}, 
  {"fbul","branch on unordered or less"}, 
  {"fbule","branch on unordered or less"}, 
  {"fdtoi","convert floating point to 32-bit integer"}, 
  {"fdtox","convert floating point to 64-bit integer"}, 
  {"fitod","convert 32-bit integer to floating"}, 
  {"fitoq","convert 32-bit integer to floating"}, 
  {"fitos","convert 32-bit integer to floating"}, 
  {"flushw","flush register windows"}, 
  {"fmova","move always"}, 
  {"fmovcc","move if carry clear"}, 
  {"fmovcs","move if carry set"}, 
  {"fmovd","move double"}, 
  {"fmove","move if equal"}, 
  {"fmovg","move if greater"}, 
  {"fmovge","move if greater or equal"}, 
  {"fmovgu","move if greater unsigned"}, 
  {"fmovl","move if less"}, 
  {"fmovle","move if less or equal"}, 
  {"fmovleu","move if less or equal unsigned"}, 
  {"fmovn","move never"}, 
  {"fmovne","move if not equal"}, 
  {"fmovneg","move if negative"}, 
  {"fmovpos","move if positive"}, 
  {"fmovq","move quad"}, 
  {"fmovrgez","move if register greater than or equal to zero"}, 
  {"fmovrgz","move if register greater than zero"}, 
  {"fmovrlez","move if register less than or equal zero"}, 
  {"fmovrlz","move if register less than zero"}, 
  {"fmovrne","move if register not zero"}, 
  {"fmovu","move if unordered"}, 
  {"fmovvc","move if overflow clear"}, 
  {"fmovvs","move if overflow set"}, 
  {"fnegd","negate double"}, 
  {"fnegq","negate quad"}, 
  {"fqtoi","convert floating point to 32-bit integer"}, 
  {"fqtox","convert floating point to 64-bit integer"}, 
  {"fstoi","convert floating point to 32-bit integer"}, 
  {"fstox","convert floating point to 64-bit integer"}, 
  {"fxtod","convert 64-bit integer to floating"}, 
  {"fxtoq","convert 64-bit integer to floating"}, 
  {"fxtos","convert 64-bit integer to floating"}, 
  {"iprefetch","instruction prefetch"}, 
  {"ld","load from memory into register"}, 
  {"lda","load floating-point register from alternate space"}, 
  {"ldda","load double floating-point register from alternate space"}, 
  {"ldqa","load quad floating-point register from alternate space"}, 
  {"ldsw","load a signed word"}, 
  {"ldswa","load signed word from alternate space"}, 
  {"ldub","load unsigned byte from addr"}, 
  {"lduh","load unsigned half word (16bit)"}, 
  {"ldx","load extended word"}, 
  {"ldxa","load extended word from alternate space"}, 
  {"membar","memory barrier"}, 
  {"mov","moves data from src to dst"}, 
  {"mova","move always"}, 
  {"movcc","move if carry clear (greater or equal, unsigned)"}, 
  {"movcs","move if carry set (less than, unsigned)"}, 
  {"move","move if equal"}, 
  {"movg","move if greater"}, 
  {"movge","move if greater or equal"}, 
  {"movgu","move if greater unsigned"}, 
  {"movl","move if less or greater"}, 
  {"movle","move if less or equal"}, 
  {"movleu","move less or equal unsigned"}, 
  {"movn","move never"}, 
  {"movne","move if not equal"}, 
  {"movneg","move if negative"}, 
  {"movpos","move if positive"}, 
  {"movre","move if register zero"}, 
  {"movrgez","move if register greater than or equal to zero"}, 
  {"movrgz","move if register greater than zero"}, 
  {"movrlez","move if register less than or equal to zero"}, 
  {"movrlz","move if register less than zero"}, 
  {"movrnz","move if register not zero"}, 
  {"movu","move if unordered or equal"}, 
  {"movug","move if unordered or greater or equal"}, 
  {"movule","move if unordered or less or equal"}, 
  {"movvc","move if overflow clear"}, 
  {"movvs","move if overflow set"}, 
  {"mulx","multiply"}, 
  {"nop","no operation"}, 
  {"or","binary or"}, 
  {"orn","binary nor"}, 
  {"popc","population"}, 
  {"prefetch","prefetch data"}, 
  {"prefetcha","prefetch data from alternate space"}, 
  {"restore","restore previous register window"}, 
  {"ret","return from subroutine"}, 
  {"retl","return from leaf procedure"}, 
  {"rett","return from trap instruction"}, 
  {"save","provide new register window"}, 
  {"sethi","sets upper 22 bits of rd with const"}, 
  {"signx","sign-extend 32-bit value to 64 bits"}, 
  {"sll","shift left logical"}, 
  {"smul","signed multiplication"}, 
  {"sra","arithmetic right-shift of rs1, shift by op2 and stores result"}, 
  {"srl","shift right logic"}, 
  {"st","stores word to addr"}, 
  {"sta","store floating-point register to alternate space"}, 
  {"stb","store byte"}, 
  {"stda","store double floating-point register to alternate space"}, 
  {"stqa","store quad floating-point register to alternate space"}, 
  {"stx","store extended word"}, 
  {"stxa","store extended word into alternate space"}, 
  {"stxfsr","store floating-point register (all 64-bits)"}, 
  {"sub","substract"}, 
  {"subx","substract with carry"}, 
  {"udivx","unsigned divide (64-bit)"}, 
  {"unimp","unimplemented instruction"}, 
  {NULL, NULL}
};
// 0x55f0330ef120
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_sparc_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_sparc_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_sparc(x,y) gperf_sparc_hash(x)
const unsigned int gperf_sparc_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_sparc = {
  .name = "sparc",
  .get = &gperf_sparc_get,
  .hash = &gperf_sparc_hash,
  .foreach = &gperf_sparc_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_sparc.get)("foo");
	printf ("%s\n", s);
}
#endif
