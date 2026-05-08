// SDB-CGEN V1.8.3
// gcc -DMAIN=1 uxtheme.c ; ./a.out > uxtheme.h
#include <ctype.h>
#include <stdio.h>
#include <string.h>

struct kv { const char *name; const char *value; };
static struct kv kvs[] = {
  {"114","DrawThemeTextEx"}, 
  {"12","UpdatePanningFeedback"}, 
  {"120","GetUserColorPreference"}, 
  {"121","GetColorFromPreference"}, 
  {"126","EnableThemeDialogTexture"}, 
  {"127","EnableTheming"}, 
  {"128","EndBufferedAnimation"}, 
  {"129","EndBufferedPaint"}, 
  {"130","GetBufferedPaintBits"}, 
  {"131","GetBufferedPaintDC"}, 
  {"132","GetBufferedPaintTargetDC"}, 
  {"133","GetBufferedPaintTargetRect"}, 
  {"134","GetCurrentThemeName"}, 
  {"135","GetThemeAnimationProperty"}, 
  {"136","GetThemeAnimationTransform"}, 
  {"137","GetThemeAppProperties"}, 
  {"138","GetThemeBackgroundContentRect"}, 
  {"139","GetThemeBackgroundExtent"}, 
  {"140","GetThemeBackgroundRegion"}, 
  {"141","GetThemeBitmap"}, 
  {"142","GetThemeBool"}, 
  {"143","GetThemeColor"}, 
  {"144","GetThemeDocumentationProperty"}, 
  {"145","GetThemeEnumValue"}, 
  {"146","GetThemeFilename"}, 
  {"147","GetThemeFont"}, 
  {"148","GetThemeInt"}, 
  {"149","GetThemeIntList"}, 
  {"150","GetThemeMargins"}, 
  {"151","GetThemeMetric"}, 
  {"152","GetThemePartSize"}, 
  {"153","GetThemePosition"}, 
  {"154","GetThemePropertyOrigin"}, 
  {"155","GetThemeRect"}, 
  {"156","GetThemeStream"}, 
  {"157","GetThemeString"}, 
  {"158","GetThemeSysBool"}, 
  {"159","GetThemeSysColor"}, 
  {"160","GetThemeSysColorBrush"}, 
  {"161","GetThemeSysFont"}, 
  {"162","GetThemeSysInt"}, 
  {"163","GetThemeSysSize"}, 
  {"164","GetThemeSysString"}, 
  {"165","GetThemeTextExtent"}, 
  {"166","GetThemeTextMetrics"}, 
  {"167","GetThemeTimingFunction"}, 
  {"168","GetThemeTransitionDuration"}, 
  {"169","GetWindowTheme"}, 
  {"170","HitTestThemeBackground"}, 
  {"171","IsAppThemed"}, 
  {"172","IsCompositionActive"}, 
  {"173","IsThemeActive"}, 
  {"174","IsThemeBackgroundPartiallyTransparent"}, 
  {"175","IsThemeDialogTextureEnabled"}, 
  {"176","IsThemePartDefined"}, 
  {"177","OpenThemeData"}, 
  {"178","SetThemeAppProperties"}, 
  {"179","SetWindowTheme"}, 
  {"180","SetWindowThemeAttribute"}, 
  {"181","ThemeInitApiHook"}, 
  {"37","BeginBufferedAnimation"}, 
  {"38","BeginBufferedPaint"}, 
  {"39","BufferedPaintClear"}, 
  {"40","BufferedPaintInit"}, 
  {"41","BufferedPaintRenderAnimation"}, 
  {"42","BufferedPaintSetAlpha"}, 
  {"47","DrawThemeBackgroundEx"}, 
  {"5","BeginPanningFeedback"}, 
  {"51","BufferedPaintStopAllAnimations"}, 
  {"52","BufferedPaintUnInit"}, 
  {"53","CloseThemeData"}, 
  {"54","DllCanUnloadNow"}, 
  {"55","DllGetActivationFactory"}, 
  {"56","DllGetClassObject"}, 
  {"57","DrawThemeBackground"}, 
  {"58","DrawThemeEdge"}, 
  {"59","DrawThemeIcon"}, 
  {"6","EndPanningFeedback"}, 
  {"61","OpenThemeDataEx"}, 
  {"70","DrawThemeParentBackground"}, 
  {"71","DrawThemeParentBackgroundEx"}, 
  {"89","DrawThemeText"}, 
  {"95","GetImmersiveColorFromColorSetEx"}, 
  {"98","GetImmersiveUserColorSetPreference"}, 
  {NULL, NULL}
};
// 0x55a288369d60
// TODO
typedef int (*GperfForeachCallback)(void *user, const char *k, const char *v);
int gperf_uxtheme_foreach(GperfForeachCallback cb, void *user) {
  int i = 0; while (kvs[i].name) {
  cb (user, kvs[i].name, kvs[i].value);
  i++;}
  return 0;
}
const char *gperf_uxtheme_get(const char *s) {
  int i = 0; while (kvs[i].name) {
  if (!strcmp (s, kvs[i].name)) return kvs[i].value;
  i++;}
  return NULL;
}
#define sdb_hash_c_uxtheme(x,y) gperf_uxtheme_hash(x)
const unsigned int gperf_uxtheme_hash(const char *s) {
  int sum = strlen (s);
  while (*s) { sum += *s; s++; }
  return sum;
}
struct {const char *name;void *get;void *hash;void *foreach;} gperf_uxtheme = {
  .name = "uxtheme",
  .get = &gperf_uxtheme_get,
  .hash = &gperf_uxtheme_hash,
  .foreach = &gperf_uxtheme_foreach
};

#if MAIN
int main () {
	const char *s = ((char*(*)(char*))gperf_uxtheme.get)("foo");
	printf ("%s\n", s);
}
#endif
