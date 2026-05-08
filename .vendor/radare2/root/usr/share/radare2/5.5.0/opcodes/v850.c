// SDB-CGEN V1.8.3
// gcc -DMAIN=1 v850.c ; ./a.out > v850.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"add","add immediate to register"}, 
  {"addf.s","add floating short"}, 
  {"addi","add immediate"}, 
  {"adf","add on condition flag"}, 
  {"and","and"}, 
  {"andbsu","and bit string upward"}, 
  {"andi","and immediate"}, 
  {"andnbsu","and not bit string upward"}, 
  {"bc","branch on condition"}, 
  {"be","branch if zero/equal"}, 
  {"bge","branch if greater/equal (signed)"}, 
  {"bgt","branch if greater than (signed)"}, 
  {"bh","branch if higher (unsigned)"}, 
  {"bl","branch if carry/less than"}, 
  {"ble","branch if less/equal (signed)"}, 
  {"blt","branch if less than (signed)"}, 
  {"bn","branch if negative"}, 
  {"bne","branch if not zero/equal"}, 
  {"bnh","branch if not higher (unsigned)"}, 
  {"bnl","branch if not carry/less than"}, 
  {"bnv","branch if not overflow"}, 
  {"bp","branch if positive"}, 
  {"br","branch always"}, 
  {"bsh","byte swap halfword"}, 
  {"bsw","byte swap word"}, 
  {"bv","branch if overflow"}, 
  {"callt","call interrupt table entry at given address"}, 
  {"caxi","compare and exchange interlocked"}, 
  {"cli","clear interrupt disable flag"}, 
  {"clr1","clear bit"}, 
  {"cmov","conditional move"}, 
  {"cmp","compare two registers and update flags"}, 
  {"cmpf.s","compare floating short"}, 
  {"ctret","return from callt"}, 
  {"cvt.sw","convert floating short to word"}, 
  {"cvt.ws","convert word to floating short"}, 
  {"di","disable interrupts"}, 
  {"dispose","function dispose"}, 
  {"div","divide signed"}, 
  {"divf.s","divide floating short"}, 
  {"divh","divide half word"}, 
  {"divq","divide quad word"}, 
  {"divu","divide unsigned"}, 
  {"ei","enable interrupts"}, 
  {"eiret","return from trap or interrupt"}, 
  {"feret","return from trap or interrupt"}, 
  {"fetrap","software trap"}, 
  {"halt","halt cpu"}, 
  {"hsh","halfword swap half word"}, 
  {"hsw","halfword swap word"}, 
  {"in.b","input byte"}, 
  {"in.h","input halfword"}, 
  {"in.w","input word"}, 
  {"jal","jump and link"}, 
  {"jarl","jump and register link"}, 
  {"jmp","jump register"}, 
  {"jr","jump relative"}, 
  {"ld.b","load signed byte"}, 
  {"ld.bu","load unsigned byte"}, 
  {"ld.h","load halfword"}, 
  {"ld.hu","load unsigned half word"}, 
  {"ld.w","load word"}, 
  {"ldsr","load into system register"}, 
  {"mac","multiply and add word"}, 
  {"mov","move"}, 
  {"movbsu","move bit string upward"}, 
  {"movea","add immediate"}, 
  {"movhi","add high halfword"}, 
  {"mpyhw","multiply halfword signed"}, 
  {"mul","multiply signed"}, 
  {"mulf.s","multiply floating short"}, 
  {"mulu","multiply unsigned"}, 
  {"nop","do nothing"}, 
  {"nop1","do nothing once"}, 
  {"not","not"}, 
  {"not1","bitwise NOT given bit"}, 
  {"notbsu","not bit string upward"}, 
  {"or","bitwise or"}, 
  {"orbsu","or bit string upward"}, 
  {"ori","or immediate"}, 
  {"ornbsu","or not bit string immediate"}, 
  {"out.b","output byte"}, 
  {"out.h","output halfword"}, 
  {"out.w","output word"}, 
  {"prepare","create stack frame"}, 
  {"reti","return from trap or interrupt"}, 
  {"rev","reverse bits"}, 
  {"rie","reserved instruction exception"}, 
  {"sar","shift arithmetic right"}, 
  {"sasf","shift and flag condition"}, 
  {"satadd","saturated addition"}, 
  {"satsub","saturated substraction"}, 
  {"satsubi","saturated substrcation"}, 
  {"satsubr","saturated reverse substract"}, 
  {"sbf","conditional substraction"}, 
  {"sch0bsd","search bit 0 downward"}, 
  {"sch0bsu","search bit 0 upward"}, 
  {"sch0l","search zero from left"}, 
  {"sch0r","search zero from right"}, 
  {"sch1bsd","search bit 1 downward"}, 
  {"sch1bsu","search bit 1 upward"}, 
  {"sch1l","search one from left"}, 
  {"sch1r","search one from right"}, 
  {"sei","set interrupt disable flag"}, 
  {"set1","set bit"}, 
  {"setf","set flag condition"}, 
  {"shl","shift left"}, 
  {"shr","shift right"}, 
  {"sst.b","store byte"}, 
  {"sst.h","store half word"}, 
  {"sst.w","store word"}, 
  {"st.b","store byte"}, 
  {"st.h","store halfword"}, 
  {"st.w","store word"}, 
  {"stsr","store from system register"}, 
  {"sub","subtract"}, 
  {"subf.s","subtract floating short"}, 
  {"subr","reverse substraction"}, 
  {"switch","jump with table lookup"}, 
  {"sxb","sign extend byte"}, 
  {"sxh","sign extend halfword"}, 
  {"synce","synchronize exceptions"}, 
  {"syncm","synchronize memory"}, 
  {"syncp","synchronize pipeline"}, 
  {"syscall","system call"}, 
  {"trap","trap"}, 
  {"trnc.sw","truncate floating short to word"}, 
  {"tst","test registers"}, 
  {"tst1","test bit"}, 
  {"xb","swap low bytes"}, 
  {"xh","swap halfwords"}, 
  {"xor","exclusive bitwise OR on registers"}, 
  {"xorbsu","exclusive or bit string upward"}, 
  {"xori","exclusive or immediate"}, 
  {"xornbsu","exclusive or not bit string upward"}, 
  {"zxb","zero extend byte"}, 
  {"zxh","zero extend half"}, 
  {NULL, NULL}
};
// 0x55ec665153a0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_v850_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_v850_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_v850(x,y) gperf_v850_hash(x)
const unsigned int gperf_v850_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_v850 = {
  .name = "v850",
  .get = &gperf_v850_get,
  .hash = &gperf_v850_hash,
  .foreach = &gperf_v850_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_v850.get)("foo");
	printf ("%s\n", s);
}
#endif
