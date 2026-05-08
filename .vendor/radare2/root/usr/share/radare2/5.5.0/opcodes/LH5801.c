// SDB-CGEN V1.8.3
// gcc -DMAIN=1 LH5801.c ; ./a.out > LH5801.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"adc","add with carry"}, 
  {"adi","add immediate"}, 
  {"adr","add rreg"}, 
  {"aex","exchange accumulator"}, 
  {"am0","accumulator to tm and 0"}, 
  {"am1","accumulator to tm and 1"}, 
  {"and","and accumulator"}, 
  {"ani","and immediate"}, 
  {"atp","accumulator to port"}, 
  {"att","accumulator to t (status register)"}, 
  {"bcc","conditional branch"}, 
  {"bch","unconditional branch"}, 
  {"bii","bit test immediate"}, 
  {"bit","bit test"}, 
  {"cdv","clear divider"}, 
  {"cin","compare and increment"}, 
  {"cpa","compare accumulator"}, 
  {"cpi","compare immediate"}, 
  {"dca","decimal add"}, 
  {"dcs","decimal subtract"}, 
  {"dec","decrement"}, 
  {"drl","digit rotate left"}, 
  {"drr","digit rotate right"}, 
  {"eai","exclusive or accumulator, immediate"}, 
  {"eor","exclusive or"}, 
  {"hlt","halt"}, 
  {"inc","increment"}, 
  {"ita","in to accumulator"}, 
  {"jmp","jump"}, 
  {"lda","load accumulator"}, 
  {"lde","load and decrement"}, 
  {"ldi","load immediate"}, 
  {"ldx","load xreg"}, 
  {"lin","load and increment"}, 
  {"lop","loop"}, 
  {"nop","no operation"}, 
  {"off","reset bf"}, 
  {"ora","or accumulator"}, 
  {"ori","or immediate"}, 
  {"pop","pop"}, 
  {"psh","push"}, 
  {"rdp","reset display"}, 
  {"rec","reset carry flag"}, 
  {"rie","reset interrupt enable"}, 
  {"rol","rotate left"}, 
  {"ror","rotate right"}, 
  {"rpu","reset pu"}, 
  {"rpv","reset pv"}, 
  {"rti","return from interrupt"}, 
  {"rtn","return from subroutine"}, 
  {"sbc","subtract with carry"}, 
  {"sbi","subtract immediate"}, 
  {"sde","store and decrement"}, 
  {"sdp","set display"}, 
  {"sec","set carry flag"}, 
  {"shl","shift left"}, 
  {"shr","shift right"}, 
  {"sie","set interrupt enable"}, 
  {"sin","store and increment"}, 
  {"sjp","subroutine jump aka call"}, 
  {"spu","set pu"}, 
  {"spv","set pv"}, 
  {"sta","store accumulator"}, 
  {"stx","store xreg"}, 
  {"tin","transfer and increment"}, 
  {"tta","t status register to accumulator"}, 
  {"vcc","conditional vector subroutine jump"}, 
  {"vej","vector subroutine jump, short format"}, 
  {"vmj","vector subroutine jump, long format"}, 
  {NULL, NULL}
};
// 0x560c8af213b0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_LH5801_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_LH5801_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_LH5801(x,y) gperf_LH5801_hash(x)
const unsigned int gperf_LH5801_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_LH5801 = {
  .name = "LH5801",
  .get = &gperf_LH5801_get,
  .hash = &gperf_LH5801_hash,
  .foreach = &gperf_LH5801_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_LH5801.get)("foo");
	printf ("%s\n", s);
}
#endif
