// SDB-CGEN V1.8.3
// gcc -DMAIN=1 avr.c ; ./a.out > avr.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"adc","add with carry"}, 
  {"add","add without carry"}, 
  {"adiw","add immediate to word"}, 
  {"and","logical AND"}, 
  {"andi","logical AND with immediate"}, 
  {"asr","arithmetic shift right"}, 
  {"bclr","bit clear in SREG"}, 
  {"bld","bit load from T flag in SREG to a bit in register"}, 
  {"brbc","branch if bit in SREG is cleared"}, 
  {"brbs","branch if bit in SREG is set"}, 
  {"brcc","branch if carry flag is cleared"}, 
  {"brcs","branch if carry flag is set"}, 
  {"break","break"}, 
  {"breq","branch if equal"}, 
  {"brge","branch if greater or equal (signed)"}, 
  {"brhc","branch if half carry flag is cleared"}, 
  {"brhs","branch if half carry flag is set"}, 
  {"brid","branch if global interrupt is disabled"}, 
  {"brie","branch if global interrupt is enabled"}, 
  {"brlo","branch if lower (unsigned)"}, 
  {"brlt","branch if less than (signed)"}, 
  {"brmi","branch if minus"}, 
  {"brne","branch if not equal"}, 
  {"brpl","branch if plus"}, 
  {"brsh","branch if same or higher (unsigned)"}, 
  {"brtc","branch if T flag is cleared"}, 
  {"brts","branch if T flag is set"}, 
  {"brvc","branch if overflow flag is cleared"}, 
  {"brvs","branch if overflow flag is set"}, 
  {"bset","bit set in SREG"}, 
  {"bst","bit store from bit in register to T flag in SREG"}, 
  {"call","long call to a subroutine"}, 
  {"cbi","clear bit in I/O register"}, 
  {"cbr","clear bit(s) in register"}, 
  {"clc","clear carry flag"}, 
  {"clh","clear half carry flag"}, 
  {"cli","clear global interrupt flag"}, 
  {"cln","clear negative flag"}, 
  {"clr","clear register"}, 
  {"cls","clear signed flag"}, 
  {"clt","clear T flag"}, 
  {"clv","clear overflow flag"}, 
  {"clz","clear zero flag"}, 
  {"com","one's complement"}, 
  {"cp","compare"}, 
  {"cpc","compare with carry"}, 
  {"cpi","compare with immediate"}, 
  {"cpse","compare, skip if equal"}, 
  {"dec","decrement"}, 
  {"eicall","extended indirect call to subroutine"}, 
  {"eijmp","extended indirect jump"}, 
  {"elpm","extended load programm memory"}, 
  {"eor","exclusive OR"}, 
  {"fmul","fractional multiply unsigned"}, 
  {"fmuls","fractional multiply signed"}, 
  {"fmulsu","fractional multiply signed with unsigned"}, 
  {"icall","indirect call to subroutine"}, 
  {"ijmp","indirect jump"}, 
  {"in","load an I/O location to register"}, 
  {"inc","increment"}, 
  {"jmp","jump"}, 
  {"lac","load and clear"}, 
  {"las","load and set"}, 
  {"lat","load and toggle"}, 
  {"ld","LD Rd,-Z. load indirect and pre-decrement"}, 
  {"ldd","LDD Rd,Z+q. load indirect with displacement"}, 
  {"ldi","LDI Rd,K. load immediate"}, 
  {"lds","LDS Rd,K. load direct from SRAM"}, 
  {"lpm","LPM Rd,Z+. load program memory and post-increment"}, 
  {"lsl","logical shift left"}, 
  {"lsr","logical shift right"}, 
  {"mov","copy register"}, 
  {"movw","copy register word"}, 
  {"mul","multiply unsigned"}, 
  {"muls","multiply signed"}, 
  {"mulsu","multiply signed with unsigned"}, 
  {"neg","two's complement"}, 
  {"nop","no operation"}, 
  {"or","logical OR"}, 
  {"ori","logical OR with immediate"}, 
  {"out","store register to an I/O location"}, 
  {"pop","pop register from stack"}, 
  {"push","push register on stack"}, 
  {"rcall","relative call to subroutine"}, 
  {"ret","return from subroutine"}, 
  {"reti","return from interrupt"}, 
  {"rjmp","relative jump"}, 
  {"rol","rotate left through carry"}, 
  {"ror","rotate right through carry"}, 
  {"sbc","subtract with carry"}, 
  {"sbci","subtract immediate with carry"}, 
  {"sbi","set bit in I/O register"}, 
  {"sbic","skip if bit in I/O register is cleared"}, 
  {"sbis","skip if bit in I/O register is set"}, 
  {"sbiw","subtract immediate from word"}, 
  {"sbr","set bit(s) in register"}, 
  {"sbrc","skip if bit in register is cleared"}, 
  {"sbrs","skip if bit in register is set"}, 
  {"sec","set carry flag"}, 
  {"seh","set half carry flag"}, 
  {"sei","set global interrupt flag"}, 
  {"sen","set negative flag"}, 
  {"ser","set all bits in register"}, 
  {"ses","set signed flag"}, 
  {"set","set T flag"}, 
  {"sev","set overflow flag"}, 
  {"sez","set zero flag"}, 
  {"sleep","sleep mode"}, 
  {"spm","store program memory"}, 
  {"st","ST -Z,Rr. store indirect and pre-decrement"}, 
  {"std","STD Z+q,Rr. store indirect with displacement"}, 
  {"sts","store direct to SRAM"}, 
  {"sub","subtract without carry"}, 
  {"subi","subtract immediate"}, 
  {"swap","swap nibbles"}, 
  {"tst","test for zero or minus"}, 
  {"wdr","watchdog reset"}, 
  {"xch","exchange"}, 
  {NULL, NULL}
};
// 0x55c12b33a620
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_avr_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_avr_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_avr(x,y) gperf_avr_hash(x)
const unsigned int gperf_avr_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_avr = {
  .name = "avr",
  .get = &gperf_avr_get,
  .hash = &gperf_avr_hash,
  .foreach = &gperf_avr_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_avr.get)("foo");
	printf ("%s\n", s);
}
#endif
