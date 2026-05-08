// SDB-CGEN V1.8.3
// gcc -DMAIN=1 COMMCTRL.c ; ./a.out > COMMCTRL.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"1","WEP"}, 
  {"10","TV_EDITWNDPROC"}, 
  {"11","LISTVIEW_EDITWNDPROC"}, 
  {"12","TV_WNDPROC"}, 
  {"13","MAKEDRAGLIST"}, 
  {"14","LBITEMFROMPT"}, 
  {"15","DRAWINSERT"}, 
  {"159","PROPERTYSHEET"}, 
  {"16","CREATEUPDOWNCONTROL"}, 
  {"160","CREATEPROPERTYSHEETPAGE"}, 
  {"161","DESTROYPROPERTYSHEETPAGE"}, 
  {"17","INITCOMMONCONTROLS"}, 
  {"2","MENUHELP"}, 
  {"20","CREATETOOLBAREX"}, 
  {"3","SHOWHIDEMENUCTL"}, 
  {"300","DLLENTRYPOINT"}, 
  {"301","CCTL1632_THUNKDATA16"}, 
  {"328","DPA_CREATE"}, 
  {"329","DPA_DESTROY"}, 
  {"330","DPA_GROW"}, 
  {"331","DPA_CLONE"}, 
  {"332","DPA_GETPTR"}, 
  {"333","DPA_GETPTRINDEX"}, 
  {"334","DPA_INSERTPTR"}, 
  {"335","DPA_SETPTR"}, 
  {"336","DPA_DELETEPTR"}, 
  {"337","DPA_DELETEALLPTRS"}, 
  {"338","DPA_SORT"}, 
  {"339","DPA_SEARCH"}, 
  {"4","GETEFFECTIVECLIENTRECT"}, 
  {"40","IMAGELIST_CREATE"}, 
  {"41","IMAGELIST_DESTROY"}, 
  {"42","IMAGELIST_GETIMAGECOUNT"}, 
  {"43","IMAGELIST_SETOVERLAYIMAGE"}, 
  {"44","IMAGELIST_SETBKCOLOR"}, 
  {"45","IMAGELIST_GETBKCOLOR"}, 
  {"46","IMAGELIST_ADD"}, 
  {"49","IMAGELIST_DRAW"}, 
  {"5","DRAWSTATUSTEXT"}, 
  {"53","IMAGELIST_ADDICON"}, 
  {"54","IMAGELIST_REPLACEICON"}, 
  {"6","CREATESTATUSWINDOW"}, 
  {"7","CREATETOOLBAR"}, 
  {"8","CREATEMAPPEDBITMAP"}, 
  {"9","LISTVIEW_WNDPROC"}, 
  {NULL, NULL}
};
// 0x55ef3f144c80
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_COMMCTRL_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_COMMCTRL_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_COMMCTRL(x,y) gperf_COMMCTRL_hash(x)
const unsigned int gperf_COMMCTRL_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_COMMCTRL = {
  .name = "COMMCTRL",
  .get = &gperf_COMMCTRL_get,
  .hash = &gperf_COMMCTRL_hash,
  .foreach = &gperf_COMMCTRL_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_COMMCTRL.get)("foo");
	printf ("%s\n", s);
}
#endif
