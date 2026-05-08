// SDB-CGEN V1.8.3
// gcc -DMAIN=1 sh.c ; ./a.out > sh.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"add","add binary"}, 
  {"addc","add with carry"}, 
  {"addv","add with (v flag) overflow check"}, 
  {"and","bitwise and"}, 
  {"and.b","bitise and (byte)"}, 
  {"bf","branch if false"}, 
  {"bf.s","branch if false with delay slot"}, 
  {"bf/s","branch if false with delay slot"}, 
  {"bra","branch"}, 
  {"braf","branch far"}, 
  {"bsr","branch to subroutine"}, 
  {"bsrf","branch to subroutine far"}, 
  {"bt","branch if true"}, 
  {"bt.s","branch if true with delay slot"}, 
  {"bt/s","branch if true with delay slot"}, 
  {"clrmac","clear mac register"}, 
  {"clrs","clear s bit"}, 
  {"clrt","clear t bit"}, 
  {"cmp/eq","compare rm,rn : set t if rn == rm"}, 
  {"cmp/ge","compare rm,rn : set t if rn >= rm (signed)"}, 
  {"cmp/gt","compare rm,rn : set t if rn > rm (signed)"}, 
  {"cmp/hi","compare rm,rn : set t if  rn > rm (unsigned)"}, 
  {"cmp/hs","compare rm,rn : set t if  rn >= rm (unsigned)"}, 
  {"cmp/pl","set t if rn > 0"}, 
  {"cmp/pz","set t if rn >= 0"}, 
  {"cmp/str","compare rm,rn : set t if any bytes are equal"}, 
  {"div0s","divide (step 0) as signed"}, 
  {"div0u","divide (step 0) as unsigned"}, 
  {"div1","divide 1 step"}, 
  {"dmuls.l","double-length multiply as signed"}, 
  {"dmulu.l","double-length multiply as unsigned"}, 
  {"dt","decrement and test"}, 
  {"exts.b","extend byte as signed"}, 
  {"exts.w","extend word as signed"}, 
  {"extu.b","extend byte as unsigned"}, 
  {"extu.w","extend word as unsigned"}, 
  {"fabs","floating-point absolute value"}, 
  {"fadd","floating-point add"}, 
  {"fcmp/eq","compare (float) frm, frn: set t if frm == frn"}, 
  {"fcmp/gt","compare (float) frm, frn: set t if frn > frm"}, 
  {"fcnvds","floating-point convert double to single precision"}, 
  {"fcnvsd","floating-point convert single to double precision"}, 
  {"fdiv","floating-point divide"}, 
  {"fipr","floating-point inner product"}, 
  {"fldi0","floating-point load immediate 0.0"}, 
  {"fldi1","floating-point loa immediate 1.0"}, 
  {"flds","floating-point load to system register"}, 
  {"float","floating-point convert from integer"}, 
  {"fmac","floating-point multiply and accumulate"}, 
  {"fmov","floating-point move"}, 
  {"fmov.s","floating-point move"}, 
  {"fmul","floating-point multiply"}, 
  {"fneg","floating-point negate value"}, 
  {"frchg","fr-bit change"}, 
  {"fschg","sz-bit change"}, 
  {"fsqrt","floating-point square root"}, 
  {"fsts","floating-point store system register"}, 
  {"fsub","floating-point subtract"}, 
  {"ftrc","floating-point truncate and convert to integer"}, 
  {"ftrv","floating-point transform vector"}, 
  {"jmp","jump"}, 
  {"jsr","jump to subroutine"}, 
  {"ldc","load to control register"}, 
  {"ldc.l","load to control register"}, 
  {"lds","load to fpu/system register"}, 
  {"lds.l","load to fpu/system register"}, 
  {"ldtlb","load pteh/ptel/ptea to tlb"}, 
  {"mac.l","multiply and accumulate long"}, 
  {"mac.w","multiply and accumulate word"}, 
  {"mov","move data"}, 
  {"mov.b","move byte"}, 
  {"mov.l","move longword"}, 
  {"mov.w","move word"}, 
  {"mova","move effective address"}, 
  {"movca.l","move with cache block allocation"}, 
  {"movt","move t bit to rn"}, 
  {"mul.l","multiply long"}, 
  {"muls.w","multiply as signed word"}, 
  {"mulu.w","multiply as unsigned word"}, 
  {"neg","negate"}, 
  {"negc","negate with carry"}, 
  {"nop","no operation"}, 
  {"not","not-logical complement"}, 
  {"ocbi","operand cache block invalidate"}, 
  {"ocbp","operand cache block purge"}, 
  {"ocbwb","operand cache block write back"}, 
  {"or","bitwise or (byte)"}, 
  {"pref","prefetch data to cache"}, 
  {"rotcl","rotate with carry left"}, 
  {"rotcr","rotate with carry right"}, 
  {"rotl","rotate left"}, 
  {"rotr","rotate right"}, 
  {"rte","return from exception"}, 
  {"rts","return from subroutine"}, 
  {"sets","set s bit"}, 
  {"sett","set t bit"}, 
  {"shad","shift arithmetic dynamically"}, 
  {"shal","shift arithmetic left"}, 
  {"shar","shift arithmetic right"}, 
  {"shld","shift logical dynamically"}, 
  {"shll","shift logical left"}, 
  {"shll16","shift logical left 16"}, 
  {"shll2","shift logical left 2"}, 
  {"shll8","shift logical left 8"}, 
  {"shlr","shift logical right"}, 
  {"shlr16","shift logical right 16"}, 
  {"shlr2","shift logical right 2"}, 
  {"shlr8","shift logical right 8"}, 
  {"sleep","sleep"}, 
  {"stc","store control register"}, 
  {"stc.l","store control register"}, 
  {"sts","store system/fpu register"}, 
  {"sts.l","store system/fpu register"}, 
  {"sub","subtract binary"}, 
  {"subc","subtract with carry"}, 
  {"subv","subtract with (v flag) underflow check"}, 
  {"swap.b","swap register lower bytes"}, 
  {"swap.w","swap register words"}, 
  {"tas.b","test and set byte"}, 
  {"trapa","trap always"}, 
  {"tst","test logical"}, 
  {"tst.b","test logical, byte"}, 
  {"xor","bitwise exclusive-or"}, 
  {"xor.b","bitwise exclusive-or (byte)"}, 
  {"xtrct","middle extraction from linked register"}, 
  {NULL, NULL}
};
// 0x5558f2962890
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_sh_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_sh_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_sh(x,y) gperf_sh_hash(x)
const unsigned int gperf_sh_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_sh = {
  .name = "sh",
  .get = &gperf_sh_get,
  .hash = &gperf_sh_hash,
  .foreach = &gperf_sh_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_sh.get)("foo");
	printf ("%s\n", s);
}
#endif
