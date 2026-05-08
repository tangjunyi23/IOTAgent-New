// SDB-CGEN V1.8.3
// gcc -DMAIN=1 pic18c.c ; ./a.out > pic18c.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"addlw","add literal and wreg"}, 
  {"addwf","add wreg and f"}, 
  {"addwfc","add wreg and carry bit to f"}, 
  {"andlw","and literal with wreg"}, 
  {"andwf","and wreg with f"}, 
  {"bc","branch if carry"}, 
  {"bcf","bit clear f"}, 
  {"bn","branch if negative"}, 
  {"bnc","branch if not carry"}, 
  {"bnn","branch if not negative"}, 
  {"bnov","branch if not overflow"}, 
  {"bnz","branch if not zero"}, 
  {"bov","branch if overflow"}, 
  {"bra","branch unconditionally"}, 
  {"bsf","bit set f"}, 
  {"btfsc","bit test f, skip if clear"}, 
  {"btfss","bit test f, skip if set"}, 
  {"btg","bit toggle f"}, 
  {"bz","branch if zero"}, 
  {"call","call subroutine"}, 
  {"clrf","clear f"}, 
  {"clrwdt","clear watchdog timer"}, 
  {"conf","complement f"}, 
  {"cpfseq","compare f with wreg, skip ="}, 
  {"cpfsgt","compare f with wreg, skip >"}, 
  {"cpfslt","compare f with wreg, skip <"}, 
  {"daw","decimal adjust wreg"}, 
  {"dcfsnz","decrement f, skip if not 0"}, 
  {"decf","decrement f"}, 
  {"decfsz","decrement f, skip if 0"}, 
  {"goto","go to address"}, 
  {"incf","increment f, skip if 0"}, 
  {"incfsz","increment f, skip if not 0"}, 
  {"iorlw","inclusive or literal with wreg"}, 
  {"iorwf","inclusive or wreg with f"}, 
  {"lfsr","move literal (12-bit) to fsrx"}, 
  {"movf","move f"}, 
  {"movff","move fs (source) to fd (destination)"}, 
  {"movlb","move literal to bsr<3:0>"}, 
  {"movlw","move literal to wreg"}, 
  {"movwf","move wreg to f"}, 
  {"mullw","multiply literal with wreg"}, 
  {"mulwf","multiply wreg with f"}, 
  {"negf","negate f"}, 
  {"nop","no operation"}, 
  {"pop","pop top of return stack (tos)"}, 
  {"push","push top of return stack (tos)"}, 
  {"rcall","relative call"}, 
  {"reset","software device reset"}, 
  {"retfie","return from interrupt enable"}, 
  {"retlw","return with literal in wreg"}, 
  {"return","return from subroutine"}, 
  {"rlcf","rotate left f through carry"}, 
  {"rlncf","rotate left f (no carry)"}, 
  {"rrcf","rotate right f through carry"}, 
  {"rrncf","rotate right f (no carry)"}, 
  {"setf","set f"}, 
  {"sleep","go into standby mode"}, 
  {"subfwb","subtract f from wreg with borrow"}, 
  {"sublw","subtract wreg from literal"}, 
  {"subwfb","subtract wreg from f with borrow"}, 
  {"subwfi","subtract wreg from f"}, 
  {"swapf","swap nibbles in f"}, 
  {"tblrd*","table read with pre-increment"}, 
  {"tblrd*+","table read with post-increment"}, 
  {"tblrd*-","table read with post-decrement"}, 
  {"tblwt*","table write"}, 
  {"tblwt*+","table write with post-increment"}, 
  {"tblwt*-","table write with post-decrement"}, 
  {"tblwt+*","table write with pre-increment"}, 
  {"tstfsz","test f, skip if 0"}, 
  {"xorlw","exclusive or literal with wreg"}, 
  {"xorwf","exclusive or wreg with f"}, 
  {NULL, NULL}
};
// 0x556770e74bc0
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_pic18c_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_pic18c_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_pic18c(x,y) gperf_pic18c_hash(x)
const unsigned int gperf_pic18c_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_pic18c = {
  .name = "pic18c",
  .get = &gperf_pic18c_get,
  .hash = &gperf_pic18c_hash,
  .foreach = &gperf_pic18c_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_pic18c.get)("foo");
	printf ("%s\n", s);
}
#endif
