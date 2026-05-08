// SDB-CGEN V1.8.3
// gcc -DMAIN=1 lm32.c ; ./a.out > lm32.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"add","add"}, 
  {"addgotoff","add got offset"}, 
  {"addi","add immediate"}, 
  {"and","and"}, 
  {"andhii","and high immediate"}, 
  {"andi","and immediate"}, 
  {"b","branch"}, 
  {"be","branch equal"}, 
  {"bg","branch greater"}, 
  {"bge","branch greater or equal"}, 
  {"bgeu","branch greater or equal unsigned"}, 
  {"bgu","branch greater unsigned"}, 
  {"bi","branch immediate"}, 
  {"bne","branch not equal"}, 
  {"break","breakpoint"}, 
  {"bret","return from breakpoint"}, 
  {"call","call"}, 
  {"calli","call immediate"}, 
  {"cmpe","compare equal"}, 
  {"cmpei","compare equal immediate"}, 
  {"cmpg","compare greater than"}, 
  {"cmpge","compare greater or equal"}, 
  {"cmpgei","compare greater or equal immediate"}, 
  {"cmpgeu","compare greater or equal unsigned"}, 
  {"cmpgeui","compare greater or equal unsigned immediate"}, 
  {"cmpgi","compare greater than immediate"}, 
  {"cmpgu","compare greater than unsigned"}, 
  {"cmpgui","compare greater than unsigned immediate"}, 
  {"cmpne","compare not equal"}, 
  {"cmpnei","compare not equal immediate"}, 
  {"divu","unsigned divide"}, 
  {"eret","return from exception"}, 
  {"lb","load byte"}, 
  {"lbgotoff","load byte got offset"}, 
  {"lbgprel","load byte gp relative"}, 
  {"lbu","load byte unsigned"}, 
  {"lbugotoff","load byte got offset unsigned"}, 
  {"lbugprel","load byte unsigned gp relative"}, 
  {"lh","load halfword"}, 
  {"lhgotoff","load half word got offset"}, 
  {"lhgprel","load halfword gp relative"}, 
  {"lhu","load halfword unsigned"}, 
  {"lhugotoff","load half word got offset unsigned"}, 
  {"lhugprel","load halfword unsigned gp relative"}, 
  {"lw","load word"}, 
  {"lwgotoff","load word got offset"}, 
  {"lwgotrel","load word got relative"}, 
  {"lwgprel","load word gp relative"}, 
  {"modu","unsigned modulus"}, 
  {"mul","mulitply"}, 
  {"muli","multiply immediate"}, 
  {"mv","move"}, 
  {"mva","move address"}, 
  {"mvhi","move high immediate"}, 
  {"mvi","move immediate"}, 
  {"mvui","move unsigned immediate"}, 
  {"nop","nop"}, 
  {"nor","nor"}, 
  {"nori","nor immediate"}, 
  {"not","not"}, 
  {"or","or"}, 
  {"orhigotoffi","or high got offset immediate"}, 
  {"orhii","or high immediate"}, 
  {"ori","or immediate"}, 
  {"rcsr","read control or status register"}, 
  {"ret","return"}, 
  {"sb","store byte"}, 
  {"sbgotoff","store byte got offset"}, 
  {"sbgprel","store byte gp relative"}, 
  {"scall","system call"}, 
  {"sextb","sign extend byte"}, 
  {"sexth","sign extend half-word"}, 
  {"sh","store halfword"}, 
  {"shgotoff","store half word got offset"}, 
  {"shgprel","store halfword gp relative"}, 
  {"sl","shift left"}, 
  {"sli","shift left immediate"}, 
  {"sr","shift right"}, 
  {"sri","shift right immediate"}, 
  {"sru","shift right unsigned"}, 
  {"srui","shift right unsigned immediate"}, 
  {"sub","subtract"}, 
  {"sw","store word"}, 
  {"swgotoff","store word got offset"}, 
  {"swgprel","store word gp relative"}, 
  {"user","user defined instruction"}, 
  {"wcsr","write control or status register"}, 
  {"xnor","xnor"}, 
  {"xnori","xnor immediate"}, 
  {"xor","xor"}, 
  {"xori","xor immediate"}, 
  {NULL, NULL}
};
// 0x55839364a8a0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_lm32_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_lm32_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_lm32(x,y) gperf_lm32_hash(x)
const unsigned int gperf_lm32_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_lm32 = {
  .name = "lm32",
  .get = &gperf_lm32_get,
  .hash = &gperf_lm32_hash,
  .foreach = &gperf_lm32_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_lm32.get)("foo");
	printf ("%s\n", s);
}
#endif
