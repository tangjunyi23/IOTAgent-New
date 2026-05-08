// SDB-CGEN V1.8.3
// gcc -DMAIN=1 tms320.c ; ./a.out > tms320.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"ABS","absolute value"}, 
  {"ADD","addition"}, 
  {"AND","bitwise and"}, 
  {"B","branch"}, 
  {"CALL","function call"}, 
  {"CLR","assign the value to 0"}, 
  {"CMP","compare"}, 
  {"CNT","count"}, 
  {"EXP","exponent"}, 
  {"MAC","multiply and accumulate"}, 
  {"MAR","modify auxiliary register content"}, 
  {"MAS","multiply and subtract"}, 
  {"MAX","maximum"}, 
  {"MIN","minimum"}, 
  {"MOV","move data"}, 
  {"MPY","multiply"}, 
  {"NEG","negate (2s complement)"}, 
  {"NOT","bitwise complement (1s complement)"}, 
  {"OR","bitwise or"}, 
  {"POP","pop from top of the stack"}, 
  {"PSH","push to top of the stack"}, 
  {"RET","return"}, 
  {"ROL","rotate left"}, 
  {"ROR","rotate right"}, 
  {"RPT","repeat"}, 
  {"SAT","saturate"}, 
  {"SET","assign the value to 1"}, 
  {"SFT","shift (left or right depending on sign of shift count)"}, 
  {"SQA","square and add"}, 
  {"SQR","square"}, 
  {"SQS","square and subtract"}, 
  {"SUB","subtraction"}, 
  {"SWAP","swap register contents"}, 
  {"TST","test bit"}, 
  {"XOR","bitwise exclusive-or (xor)"}, 
  {"XPA","expand"}, 
  {"XTR","extract"}, 
  {NULL, NULL}
};
// 0x55c791990aa0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_tms320_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_tms320_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_tms320(x,y) gperf_tms320_hash(x)
const unsigned int gperf_tms320_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_tms320 = {
  .name = "tms320",
  .get = &gperf_tms320_get,
  .hash = &gperf_tms320_hash,
  .foreach = &gperf_tms320_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_tms320.get)("foo");
	printf ("%s\n", s);
}
#endif
