// SDB-CGEN V1.8.3
// gcc -DMAIN=1 v810.c ; ./a.out > v810.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"add","add"}, 
  {"addf.s","add floating short"}, 
  {"addi","add immediate"}, 
  {"and","and"}, 
  {"andbsu","and bit string upward"}, 
  {"andi","and immediate"}, 
  {"andnbsu","and not bit string upward"}, 
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
  {"bv","branch if overflow"}, 
  {"caxi","compare and exchange interlocked"}, 
  {"cli","clear interrupt disable flag"}, 
  {"cmp","compare"}, 
  {"cmpf.s","compare floating short"}, 
  {"cvt.sw","convert floating short to word"}, 
  {"cvt.ws","convert word to floating short"}, 
  {"div","divide signed"}, 
  {"divf.s","divide floating short"}, 
  {"divu","divide unsigned"}, 
  {"halt","halt cpu"}, 
  {"in.b","input byte"}, 
  {"in.h","input halfword"}, 
  {"in.w","input word"}, 
  {"jal","jump and link"}, 
  {"jmp","jump register"}, 
  {"jr","jump relative"}, 
  {"ld.b","load byte"}, 
  {"ld.h","load halfword"}, 
  {"ld.w","load word"}, 
  {"ldsr","load into system register"}, 
  {"mov","move"}, 
  {"movbsu","move bit string upward"}, 
  {"movea","add immediate"}, 
  {"movhi","add high halfword"}, 
  {"mpyhw","multiply halfword signed"}, 
  {"mul","multiply signed"}, 
  {"mulf.s","multiply floating short"}, 
  {"mulu","multiply unsigned"}, 
  {"not","not"}, 
  {"notbsu","not bit string upward"}, 
  {"or","or"}, 
  {"orbsu","or bit string upward"}, 
  {"ori","or immediate"}, 
  {"ornbsu","or not bit string immediate"}, 
  {"out.b","output byte"}, 
  {"out.h","output halfword"}, 
  {"out.w","output word"}, 
  {"reti","return from trap/irq"}, 
  {"rev","reverse bits"}, 
  {"sar","shift arithmetic right"}, 
  {"sch0bsd","search bit 0 downward"}, 
  {"sch0bsu","search bit 0 upward"}, 
  {"sch1bsd","search bit 1 downward"}, 
  {"sch1bsu","search bit 1 upward"}, 
  {"sei","set interrupt disable flag"}, 
  {"setf","set flag condition"}, 
  {"shl","shift left"}, 
  {"shr","shift right"}, 
  {"st.b","store byte"}, 
  {"st.h","store halfword"}, 
  {"st.w","store word"}, 
  {"stsr","store from system register"}, 
  {"sub","subtract"}, 
  {"subf.s","subtract floating short"}, 
  {"trap","trap"}, 
  {"trnc.sw","truncate floating short to word"}, 
  {"xb","swap low bytes"}, 
  {"xh","swap halfwords"}, 
  {"xor","exclusive or register"}, 
  {"xorbsu","exclusive or bit string upward"}, 
  {"xori","exclusive or immediate"}, 
  {"xornbsu","exclusive or not bit string upward"}, 
  {NULL, NULL}
};
// 0x55b57dbc7b30
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_v810_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_v810_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_v810(x,y) gperf_v810_hash(x)
const unsigned int gperf_v810_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_v810 = {
  .name = "v810",
  .get = &gperf_v810_get,
  .hash = &gperf_v810_hash,
  .foreach = &gperf_v810_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_v810.get)("foo");
	printf ("%s\n", s);
}
#endif
