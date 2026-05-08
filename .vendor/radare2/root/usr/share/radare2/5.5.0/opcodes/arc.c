// SDB-CGEN V1.8.3
// gcc -DMAIN=1 arc.c ; ./a.out > arc.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"abs","absolute value"}, 
  {"abs_s","absolute value"}, 
  {"abss","absolute and saturate"}, 
  {"abssw","absolute and saturate of word"}, 
  {"adc","add with carry"}, 
  {"add","add"}, 
  {"add1","add with left shift by 1 bit"}, 
  {"add1_s","add with left shift by 1 bits"}, 
  {"add2","add with left shift by 2 bits"}, 
  {"add2_s","add with left shift by 2 bits"}, 
  {"add3","add with left shift by 3 bits"}, 
  {"add3_s","add with left shift by 3 bits"}, 
  {"add_s","add"}, 
  {"adds","add and saturate"}, 
  {"addsdw","add and saturate dual word"}, 
  {"and","logical and"}, 
  {"and_s","logical and"}, 
  {"asl","arithmetic shift left"}, 
  {"asl_s","arithmetic shift left"}, 
  {"asls","arithmetic shift left and saturate"}, 
  {"asr","arithmetic shift right"}, 
  {"asr_s","arithmetic shift right"}, 
  {"asrs","arithmetic shift right and saturate"}, 
  {"bbit0","branch if bit cleared to 0"}, 
  {"bbit1","branch if bit set to 1"}, 
  {"bcc","branch if condition true"}, 
  {"bcc_s","branch if condition true"}, 
  {"bclr","clear specified bit (to 0)"}, 
  {"bclr_s","clear specified bit (to 0)"}, 
  {"bic","bit-wise inverted and"}, 
  {"bic_s","bit-wise inverted and"}, 
  {"bl_s","branch and link"}, 
  {"blcc","branch and link"}, 
  {"bmsk","bit mask"}, 
  {"bmsk_s","bit mask"}, 
  {"brcc","branch on compare"}, 
  {"brcc_s","branch on compare"}, 
  {"brk","break (halt) processor"}, 
  {"brk_s","break (halt) processor"}, 
  {"bset","set specified bit (to 1)"}, 
  {"bset_s","set specified bit (to 1)"}, 
  {"btst","test value of specified bit"}, 
  {"btst_s","test value of specified bit"}, 
  {"bxor","bit xor"}, 
  {"cmp","compare"}, 
  {"cmp_s","compare"}, 
  {"divaw","division assist"}, 
  {"ex","atomic exchange"}, 
  {"ext","unsigned extend"}, 
  {"ext_s","unsigned extend"}, 
  {"flag","write to status register"}, 
  {"jcc","jump"}, 
  {"jcc_s","jump"}, 
  {"jl_s","jump and link"}, 
  {"jlcc","jump and link"}, 
  {"ld","load from memory"}, 
  {"ld_s","load from memory"}, 
  {"lpcc","loop (zero-overhead loops)"}, 
  {"lr","load from auxiliary memory"}, 
  {"lsr","logical shift left"}, 
  {"lsr_s","logical shift right"}, 
  {"max","return maximum"}, 
  {"min","return minimum"}, 
  {"mov","move (copy) to register"}, 
  {"mov_s","move (copy) to register"}, 
  {"mpy","32 x 32 signed multiply (low)"}, 
  {"mpyh","32 x 32 signed multiply (high)"}, 
  {"mpyhu","32 x 32 unsigned multiply (high)"}, 
  {"mpyu","32 x 32 unsigned multiply (low)"}, 
  {"mul64","32 x 32 signed multiply"}, 
  {"mul64_s","32 x 32 multiply"}, 
  {"mulu64","32 x 32 unsigned multiply"}, 
  {"neg","negate"}, 
  {"neg_s","negate"}, 
  {"negs","negate and saturate"}, 
  {"negsw","negate and saturate of word"}, 
  {"nop_s","no operation"}, 
  {"norm","normalize to 32 bits"}, 
  {"normw","normalize to 16 bits"}, 
  {"not","logical bit inversion"}, 
  {"not_s","logical bit inversion"}, 
  {"or","logical or"}, 
  {"or_s","logical or"}, 
  {"pop_s","restore register value from stack"}, 
  {"prefetch","prefetch from memory"}, 
  {"push_s","store register value on stack"}, 
  {"rcmp","reverse compare"}, 
  {"rlc","rotate left through carry"}, 
  {"rnd16","round to word"}, 
  {"ror","rotate right"}, 
  {"rrc","rotate right through carry"}, 
  {"rsub","reverse subtraction"}, 
  {"rtie","return from interrupt/exception"}, 
  {"sat16","saturate to word"}, 
  {"sbc","subtract with carry"}, 
  {"sex","signed extend"}, 
  {"sex_s","signed extend"}, 
  {"sleep","put processor in sleep mode"}, 
  {"sr","store to auxiliary memory"}, 
  {"st","store to memory"}, 
  {"st_s","store to memory"}, 
  {"sub","subtract"}, 
  {"sub1","subtract with left shift by 1 bit"}, 
  {"sub2","subtract with left shift by 2 bits"}, 
  {"sub3","subtract with left shift by 3 bits"}, 
  {"sub_s","subtract"}, 
  {"subs","subtract and saturate"}, 
  {"subsdw","subtract and saturate dual word"}, 
  {"swap","swap 16 x 16"}, 
  {"swi","software interrupt"}, 
  {"sync","synchronize"}, 
  {"trap0","raise exception with param. 0"}, 
  {"trap_s","raise exception"}, 
  {"tst","test"}, 
  {"tst_s","test"}, 
  {"unimp_s","unimplemented instruction"}, 
  {"xor","logical exclusive-or"}, 
  {"xor_s","logical exclusive-or"}, 
  {NULL, NULL}
};
// 0x55bde4302470
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_arc_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_arc_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_arc(x,y) gperf_arc_hash(x)
const unsigned int gperf_arc_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_arc = {
  .name = "arc",
  .get = &gperf_arc_get,
  .hash = &gperf_arc_hash,
  .foreach = &gperf_arc_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_arc.get)("foo");
	printf ("%s\n", s);
}
#endif
