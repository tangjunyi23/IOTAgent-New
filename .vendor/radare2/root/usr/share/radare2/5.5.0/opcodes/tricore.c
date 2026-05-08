// SDB-CGEN V1.8.3
// gcc -DMAIN=1 tricore.c ; ./a.out > tricore.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"add","add"}, 
  {"add.a","add address"}, 
  {"add.b","add packed byte"}, 
  {"add.h","add packed half word"}, 
  {"addc","add with carry"}, 
  {"addi","add immediate"}, 
  {"addih","add immediate high"}, 
  {"addih.a","add immediate high to address"}, 
  {"adds","add values with signed saturation"}, 
  {"adds.hu","add unsigned packed half word with saturation"}, 
  {"adds.u","add unsigned with saturation"}, 
  {"addsc.a","add scaled index to address"}, 
  {"addsc.at","add bit scaled index to address"}, 
  {"addx","add extended"}, 
  {"and","bitwise and"}, 
  {"call","call indirect"}, 
  {"cmov","conditional move"}, 
  {"isync","synchronize instructions"}, 
  {"j","jump unconditional"}, 
  {"ja","jump unsigned absolute"}, 
  {"jal","jump and link absolute"}, 
  {"jeq","jump if equal"}, 
  {"jeq.a","jump if equal address"}, 
  {"jge","jump if greater than or equal"}, 
  {"jge.u","jump if greater than or equal unsigned"}, 
  {"jgez","jump if greater than equal to zero"}, 
  {"jgtz","jump if greater than zero"}, 
  {"ji","jump indirect"}, 
  {"jl","jump and link"}, 
  {"jlez","jump if less than or equal to zero"}, 
  {"jli","jump and link indirect"}, 
  {"jlt","jump if less than"}, 
  {"jlt.u","jump if less than unsigned"}, 
  {"jltz","jump if less than zero"}, 
  {"jne","jump if not equal"}, 
  {"jne.a","jump if not equal address"}, 
  {"jned","jump if not equal and decrement"}, 
  {"jnei","jump if not equal and increment"}, 
  {"jnz","jump if not equal to zero"}, 
  {"jnz.a","jump if not equal to zero address"}, 
  {"jnz.t","jump if not equal to zero bit"}, 
  {"jz","jump if zero"}, 
  {"jz.a","jump if zero address"}, 
  {"jz.t","jump if zero bit"}, 
  {"ld.a","load word to address register"}, 
  {"ld.b","load byte"}, 
  {"ld.bu","load byte unsigned"}, 
  {"ld.d","load double world"}, 
  {"ld.da","load double word to address register"}, 
  {"ld.h","load half word"}, 
  {"ld.hu","load half word unsigned"}, 
  {"ld.q","load half word signed fraction"}, 
  {"ld.w","load word"}, 
  {"ldlcx","load lower context"}, 
  {"lea","load effective address"}, 
  {"mfcr","move from core register"}, 
  {"mov","move"}, 
  {"mov.a","move value to address register"}, 
  {"mov.aa","move address from address register"}, 
  {"mov.d","move address to data register"}, 
  {"mov.u","move unsigned"}, 
  {"movh","move high"}, 
  {"movh.a","move high to address"}, 
  {"mtcr","move to core register"}, 
  {"mul","multiply signed"}, 
  {"muls","multiply signed with saturation"}, 
  {"muls.u","multiply unsigned with saturation"}, 
  {"nop","nop operation"}, 
  {"or","bitwise or"}, 
  {"ret","return from call"}, 
  {"sh","shift"}, 
  {"sha","arithmetic shift"}, 
  {"st.a","store word from address register"}, 
  {"st.b","store byte"}, 
  {"st.d","store double word"}, 
  {"st.da","store double world from address registers"}, 
  {"st.h","store half word"}, 
  {"st.q","store half word signed fraction"}, 
  {"st.t","store bit"}, 
  {"st.w","store word"}, 
  {"sub","subtract"}, 
  {"sub.a","subtract address"}, 
  {"sub.b","subtract packed byte"}, 
  {"sub.h","subtract packed half word"}, 
  {"subc","subtract with carry"}, 
  {"subs","subtract signed with saturation"}, 
  {"subs.h","subtract packed half word with saturation"}, 
  {"subs.hu","subtract packed half word unsigned with saturation"}, 
  {"subs.u","subtract unsigned with saturation"}, 
  {"subx","subtract extended"}, 
  {"xor","bitwise xor"}, 
  {NULL, NULL}
};
// 0x55e3d7ddd870
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_tricore_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_tricore_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_tricore(x,y) gperf_tricore_hash(x)
const unsigned int gperf_tricore_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_tricore = {
  .name = "tricore",
  .get = &gperf_tricore_get,
  .hash = &gperf_tricore_hash,
  .foreach = &gperf_tricore_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_tricore.get)("foo");
	printf ("%s\n", s);
}
#endif
