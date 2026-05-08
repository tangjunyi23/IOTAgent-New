// SDB-CGEN V1.8.3
// gcc -DMAIN=1 comctl32.c ; ./a.out > comctl32.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"10","DPA_SaveStream"}, 
  {"11","DPA_Merge"}, 
  {"12","CreatePropertySheetPage"}, 
  {"13","MakeDragList"}, 
  {"14","LBItemFromPt"}, 
  {"15","DrawInsert"}, 
  {"152","FreeMRUList"}, 
  {"16","CreateUpDownControl"}, 
  {"17","InitCommonControls"}, 
  {"18","CreatePropertySheetPageA"}, 
  {"19","CreatePropertySheetPageW"}, 
  {"2","MenuHelp"}, 
  {"20","CreateStatusWindow"}, 
  {"21","CreateStatusWindowW"}, 
  {"22","CreateToolbarEx"}, 
  {"23","DestroyPropertySheetPage"}, 
  {"236","Str_SetPtrW"}, 
  {"24","DllGetVersion"}, 
  {"25","DrawStatusText"}, 
  {"26","DrawStatusTextW"}, 
  {"27","FlatSB_EnableScrollBar"}, 
  {"28","FlatSB_GetScrollInfo"}, 
  {"29","FlatSB_GetScrollPos"}, 
  {"3","ShowHideMenuCtl"}, 
  {"30","FlatSB_GetScrollProp"}, 
  {"31","FlatSB_GetScrollRange"}, 
  {"32","FlatSB_SetScrollInfo"}, 
  {"320","DSA_Create"}, 
  {"321","DSA_Destroy"}, 
  {"322","DSA_GetItem"}, 
  {"323","DSA_GetItemPtr"}, 
  {"324","DSA_InsertItem"}, 
  {"325","DSA_SetItem"}, 
  {"326","DSA_DeleteItem"}, 
  {"327","DSA_DeleteAllItems"}, 
  {"328","DPA_Create"}, 
  {"329","DPA_Destroy"}, 
  {"33","FlatSB_SetScrollPos"}, 
  {"330","DPA_Grow"}, 
  {"331","DPA_Clone"}, 
  {"332","DPA_GetPtr"}, 
  {"333","DPA_GetPtrIndex"}, 
  {"334","DPA_InsertPtr"}, 
  {"335","DPA_SetPtr"}, 
  {"336","DPA_DeletePtr"}, 
  {"337","DPA_DeleteAllPtrs"}, 
  {"338","DPA_Sort"}, 
  {"339","DPA_Search"}, 
  {"34","FlatSB_SetScrollProp"}, 
  {"340","DPA_CreateEx"}, 
  {"35","FlatSB_SetScrollRange"}, 
  {"36","FlatSB_ShowScrollBar"}, 
  {"37","GetMUILanguage"}, 
  {"38","ImageList_Add"}, 
  {"385","DPA_EnumCallback"}, 
  {"386","DPA_DestroyCallback"}, 
  {"387","DSA_EnumCallback"}, 
  {"388","DSA_DestroyCallback"}, 
  {"39","ImageList_AddIcon"}, 
  {"4","GetEffectiveClientRect"}, 
  {"40","ImageList_AddMasked"}, 
  {"400","CreateMRUListW"}, 
  {"401","AddMRUStringW"}, 
  {"403","EnumMRUListW"}, 
  {"41","ImageList_BeginDrag"}, 
  {"410","SetWindowSubclass"}, 
  {"412","RemoveWindowSubclass"}, 
  {"413","DefSubclassProc"}, 
  {"42","ImageList_Copy"}, 
  {"43","ImageList_Create"}, 
  {"44","ImageList_Destroy"}, 
  {"45","ImageList_DragEnter"}, 
  {"46","ImageList_DragLeave"}, 
  {"47","ImageList_DragMove"}, 
  {"48","ImageList_DragShowNolock"}, 
  {"49","ImageList_Draw"}, 
  {"5","DrawStatusTextA"}, 
  {"50","ImageList_DrawEx"}, 
  {"51","ImageList_DrawIndirect"}, 
  {"52","ImageList_Duplicate"}, 
  {"53","ImageList_EndDrag"}, 
  {"54","ImageList_GetBkColor"}, 
  {"55","ImageList_GetDragImage"}, 
  {"56","ImageList_GetFlags"}, 
  {"57","ImageList_GetIcon"}, 
  {"58","ImageList_GetIconSize"}, 
  {"59","ImageList_GetImageCount"}, 
  {"6","CreateStatusWindowA"}, 
  {"60","ImageList_GetImageInfo"}, 
  {"61","ImageList_GetImageRect"}, 
  {"62","ImageList_LoadImage"}, 
  {"63","ImageList_LoadImageA"}, 
  {"64","ImageList_LoadImageW"}, 
  {"65","ImageList_Merge"}, 
  {"66","ImageList_Read"}, 
  {"67","ImageList_Remove"}, 
  {"68","ImageList_Replace"}, 
  {"69","ImageList_ReplaceIcon"}, 
  {"7","CreateToolbar"}, 
  {"70","ImageList_SetBkColor"}, 
  {"75","ImageList_SetDragCursorImage"}, 
  {"76","ImageList_SetFilter"}, 
  {"77","ImageList_SetFlags"}, 
  {"78","ImageList_SetIconSize"}, 
  {"79","ImageList_SetImageCount"}, 
  {"8","CreateMappedBitmap"}, 
  {"80","ImageList_SetOverlayImage"}, 
  {"81","ImageList_Write"}, 
  {"82","InitCommonControlsEx"}, 
  {"83","InitMUILanguage"}, 
  {"84","InitializeFlatSB"}, 
  {"85","PropertySheet"}, 
  {"86","PropertySheetA"}, 
  {"87","PropertySheetW"}, 
  {"88","RegisterClassNameW"}, 
  {"89","UninitializeFlatSB"}, 
  {"9","DPA_LoadStream"}, 
  {"90","_TrackMouseEvent"}, 
  {NULL, NULL}
};
// 0x55f978c5c330
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_comctl32_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_comctl32_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_comctl32(x,y) gperf_comctl32_hash(x)
const unsigned int gperf_comctl32_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_comctl32 = {
  .name = "comctl32",
  .get = &gperf_comctl32_get,
  .hash = &gperf_comctl32_hash,
  .foreach = &gperf_comctl32_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_comctl32.get)("foo");
	printf ("%s\n", s);
}
#endif
