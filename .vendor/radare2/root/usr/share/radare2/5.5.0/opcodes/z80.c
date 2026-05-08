// SDB-CGEN V1.8.3
// gcc -DMAIN=1 z80.c ; ./a.out > z80.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"adc","add with carry register pair "}, 
  {"add","add value n to accumulator. "}, 
  {"and","logical AND of operand s to accumulator. "}, 
  {"bit","test bit b of location. "}, 
  {"call","call subroutine at location nn if condition CC is true. "}, 
  {"ccf","complement carry flag. "}, 
  {"cp","compare operand s with accumulator. "}, 
  {"cpd","comapre location (HL) and acc., decrement HL and BC, "}, 
  {"cpdr","perform a CPD and repeat until BC "}, 
  {"cpi","compare location (HL) and acc., incr HL, decr BC. "}, 
  {"cpir","perform a CPI and repeat until BC "}, 
  {"cpl","complement accumulator (1's complement). "}, 
  {"daa","decimal adjust accumulator. "}, 
  {"dec","decrement operand m. "}, 
  {"di","disable interrupts. "}, 
  {"djnz","decrement B and jump relative if B "}, 
  {"ei","enable interrupts. "}, 
  {"ex","exchange the location and register. "}, 
  {"exx","exchange the contents of BC,DE,HL with BC',DE',HL'. "}, 
  {"halt","halt computer and wait for interrupt. "}, 
  {"im","set interrupt mode 0,1 or 2. "}, 
  {"in","load the accumulator with input from device n or (C). "}, 
  {"inc","increment location. "}, 
  {"ind","input from port (C). Decrement HL and B. "}, 
  {"indr","perform an IND and repeat until B "}, 
  {"ini","input from port (C). HL "}, 
  {"inir","perform an INI and repeat until B "}, 
  {"jp","unconditional jump to location (HL IY or IX). "}, 
  {"jr","z,e Jump relative to PC+e if zero (Z "}, 
  {"ld","Load accumulator, register or location . "}, 
  {"ldd","load location (DE) with location (HL), decrement DE,HL,BC. "}, 
  {"lddr","perform an LDD and repeat until BC "}, 
  {"ldi","load location (DE) with location (HL), incr DE,HL; decr BC. "}, 
  {"ldir","perform an LDI and repeat until BC "}, 
  {"neg","negate accumulator (2's complement). "}, 
  {"nop","no operation "}, 
  {"or","logical OR of operand and accumulator. "}, 
  {"otdr","perform an OUTD and repeat until B "}, 
  {"otir","perform an OTI and repeat until B "}, 
  {"out","(n),a Load output port (n) with accumulator. "}, 
  {"outd","load output port (C) with (HL), decrement HL and B. "}, 
  {"outi","load output port (C) with (HL), incr HL, decr B. "}, 
  {"pop","load IX or IY with top of stack or Load register pair qq with top of stack. "}, 
  {"push","load IX or IY or Load register pair qq onto stack. "}, 
  {"res","b,m Reset bit b of operand m. "}, 
  {"ret","return from subroutine. with cc Return from subroutine if condition cc is true. "}, 
  {"reti","return from interrupt. "}, 
  {"retn","return from non-maskable interrupt. "}, 
  {"rl","rotate left through operand m. "}, 
  {"rla","rotate left accumulator through carry. "}, 
  {"rlc","(hl,ix+d or IY+d) Rotate location left circular. "}, 
  {"rlca","rotate left circular accumulator. "}, 
  {"rld","rotate digit left and right between accumulator and (HL). "}, 
  {"rr","rotate right through carry operand m. "}, 
  {"rra","rotate right accumulator through carry. "}, 
  {"rrc","rotate operand m right circular. "}, 
  {"rrca","rotate right circular accumulator. "}, 
  {"rrd","rotate digit right and left between accumulator and (HL) "}, 
  {"rst","restart to location p. "}, 
  {"sbc","a,s or HL,ss Subtract operands from accumulator with carry. "}, 
  {"scf","set carry flag (C "}, 
  {"set","b,(hl or IX+d or IY+d) Set bit b of location. "}, 
  {"sla","shift operand left arithmetic. "}, 
  {"sra","shift operand right arithmetic. "}, 
  {"srl","shift operand right logical. "}, 
  {"sub","subtract operand from accumulator. "}, 
  {"xor","exclusive OR operand and accumulator. "}, 
  {NULL, NULL}
};
// 0x5648cf95d910
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_z80_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_z80_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_z80(x,y) gperf_z80_hash(x)
const unsigned int gperf_z80_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_z80 = {
  .name = "z80",
  .get = &gperf_z80_get,
  .hash = &gperf_z80_hash,
  .foreach = &gperf_z80_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_z80.get)("foo");
	printf ("%s\n", s);
}
#endif
