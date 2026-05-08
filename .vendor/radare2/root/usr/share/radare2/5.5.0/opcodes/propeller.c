// SDB-CGEN V1.8.3
// gcc -DMAIN=1 propeller.c ; ./a.out > propeller.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"abs","get absolute value of a number"}, 
  {"absneg","get the negative of a number’s absolute value"}, 
  {"add","add unsigned values"}, 
  {"addabs","add absolute value to another value"}, 
  {"adds","add signed values"}, 
  {"addsx","add signed values plus c"}, 
  {"addx","add unsigned values plus c"}, 
  {"and","bitwise and values"}, 
  {"andn","bitwise and value with not of another"}, 
  {"call","jump to address with intention to return to next instruction"}, 
  {"clkset","set clock mode at run time"}, 
  {"cmp","compare unsigned values"}, 
  {"cmps","compare signed values"}, 
  {"cmpsub","compare unsigned values, subtract second if it is lesser or equal"}, 
  {"cmpsx","compare signed values plus c"}, 
  {"cmpx","compare unsigned values plus c"}, 
  {"cogid","get current cog’s id"}, 
  {"coginit","re/start cog, id optional, to run propeller assembly or spin code"}, 
  {"cogstop","start a cog by id"}, 
  {"djnz","decrement value and jump to address if not zero"}, 
  {"hubop","perform a hub operation"}, 
  {"jmp","jump to address unconditionally"}, 
  {"jmpret","jump to address with intention to “return” to another address"}, 
  {"lockclr","clear semaphore to false and get its previous state"}, 
  {"locknew","check out new semaphore and get its id"}, 
  {"lockret","return semaphore back for future “new semaphore” requests"}, 
  {"lockset","set semaphore to true and get its previous state"}, 
  {"max","limit maximum of unsigned value to another unsigned value"}, 
  {"maxs","limit maximum of signed value to another signed value"}, 
  {"min","limit minimum of unsigned value to another unsigned value"}, 
  {"mins","limit minimum of signed value to another signed value"}, 
  {"mov","set register to a value"}, 
  {"movd","set register’s destination field to a value"}, 
  {"movi","set register’s instruction field to a value"}, 
  {"movs","set register’s source field to a value"}, 
  {"muxc","set discrete bits of value to state of c"}, 
  {"muxnc","set discrete bits of value to state of !c"}, 
  {"muxnz","set discrete bits of value to state of !z"}, 
  {"muxz","set discrete bits of value to state of z"}, 
  {"neg","get negative of a number"}, 
  {"negc","get value, or its additive inverse, based on c"}, 
  {"negnc","get value, or its additive inverse, based on !c"}, 
  {"negnz","get value, or its additive inverse, based on !z"}, 
  {"negz","get value, or its additive inverse, based on z"}, 
  {"nop","no operation, elapse four clock cycles"}, 
  {"or","bitwise or values"}, 
  {"rcl","rotate c left into value by specified number of bits"}, 
  {"rcr","rotate c right into value by specified number of bits"}, 
  {"rdbyte","read byte of main memory"}, 
  {"rdlong","read long of main memory"}, 
  {"rdword","read word of main memory"}, 
  {"ret","return to address"}, 
  {"rev","reverse lsbs of value and zero-extend"}, 
  {"rol","rotate value left by specified number of bits"}, 
  {"ror","rotate value right by specified number of bits"}, 
  {"sar","shift value arithmetically right by specified number of bits"}, 
  {"shl","shift value left by specified number of bits"}, 
  {"shr","shift value right by specified number of bits"}, 
  {"sub","subtract unsigned values"}, 
  {"subabs","subtract absolute value from another value"}, 
  {"subs","subtract signed values"}, 
  {"subsx","subtract signed value plus c from another signed value"}, 
  {"subx","subtract unsigned value plus c from another unsigned value"}, 
  {"sumc","sum signed value with another whose sign is inverted based on c"}, 
  {"sumnc","sum signed value with another whose sign is inverted based on !c"}, 
  {"sumnz","sum signed value with another whose sign is inverted based on !z"}, 
  {"sumz","sum signed value with another whose sign is inverted based on z"}, 
  {"test","bitwise and values to affect flags only"}, 
  {"testn","bitwise and value with not of another to affect flags only"}, 
  {"tjnz","test value and jump to address if not zero"}, 
  {"tjz","test value and jump to address if zero"}, 
  {"waitcnt","pause execution temporarily"}, 
  {"waitpeq","pause execution until i/o pin(s) match designated state(s)"}, 
  {"waitpne","pause execution until i/o pin(s) don’t match designated state(s)"}, 
  {"waitvid","pause execution until video generator can take pixel data"}, 
  {"wrbyte","write byte to main memory"}, 
  {"wrlong","write long to main memory"}, 
  {"wrword","write word to main memory"}, 
  {"xor","bitwise xor values"}, 
  {NULL, NULL}
};
// 0x561965efbea0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_propeller_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_propeller_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_propeller(x,y) gperf_propeller_hash(x)
const unsigned int gperf_propeller_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_propeller = {
  .name = "propeller",
  .get = &gperf_propeller_get,
  .hash = &gperf_propeller_hash,
  .foreach = &gperf_propeller_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_propeller.get)("foo");
	printf ("%s\n", s);
}
#endif
