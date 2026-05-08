// SDB-CGEN V1.8.3
// gcc -DMAIN=1 i4004.c ; ./a.out > i4004.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"add","add content of register to accumulator with carry"}, 
  {"adm","add main memory"}, 
  {"bbl","branch back and load"}, 
  {"clb","clear both(accumulator and carry)"}, 
  {"clc","clear carry"}, 
  {"cma","complement accumulator"}, 
  {"cmc","complement carry"}, 
  {"daa","decimal adjust accumulator"}, 
  {"dac","decrement accumulator"}, 
  {"dcl","designate command line"}, 
  {"fim","fetch immediate"}, 
  {"fin","fetch indirect"}, 
  {"iac","increment accumulator"}, 
  {"inc","increment register"}, 
  {"isz","increment and skip"}, 
  {"jcn","jump conditional"}, 
  {"jin","jump indirect"}, 
  {"jms","jump to subroutine"}, 
  {"jun","jump uncoditional"}, 
  {"kbp","keybord process"}, 
  {"ld","load content of register to accumulator"}, 
  {"ldm","load immediate"}, 
  {"nop","no operation"}, 
  {"ral","rotate left"}, 
  {"rar","rotate right"}, 
  {"rd0","read accumulator status char 0"}, 
  {"rd1","read accumulator status char 1"}, 
  {"rd2","read accumulator status char 2"}, 
  {"rd3","read accumulator status char 3"}, 
  {"rdm","read main memory"}, 
  {"rdr","read rom port"}, 
  {"sbm","subtract main memory"}, 
  {"src","send register control"}, 
  {"stc","set carry"}, 
  {"sub","subtract content of register to accumulator with borrow"}, 
  {"tcc","transfer carry and clear"}, 
  {"tcs","transfer carry subtract"}, 
  {"wmp","write accumulator to ram port"}, 
  {"wpm","write accumulator to ram port"}, 
  {"wr0","write accumulator to status char 0"}, 
  {"wr1","write accumulator to status char 1"}, 
  {"wr2","write accumulator to status char 2"}, 
  {"wr3","write accumulator to status char 3"}, 
  {"wrm","write accumulator to main memory"}, 
  {"wrr","write accumulator to rom port"}, 
  {"xch","exchange register with accumulator"}, 
  {NULL, NULL}
};
// 0x55a33a09b150
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_i4004_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_i4004_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_i4004(x,y) gperf_i4004_hash(x)
const unsigned int gperf_i4004_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_i4004 = {
  .name = "i4004",
  .get = &gperf_i4004_get,
  .hash = &gperf_i4004_hash,
  .foreach = &gperf_i4004_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_i4004.get)("foo");
	printf ("%s\n", s);
}
#endif
