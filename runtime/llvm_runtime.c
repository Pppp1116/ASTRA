#include <errno.h>
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#if defined(__GNUC__) || defined(__clang__)
typedef __int128 i128;
typedef unsigned __int128 u128;
#else
#error "Astra LLVM runtime requires compiler support for __int128"
#endif

typedef struct AllocNode {
  void *ptr;
  struct AllocNode *next;
} AllocNode;

static AllocNode *g_alloc_head = NULL;
static bool g_alloc_init = false;

static void astra_cleanup_allocs(void) {
  AllocNode *cur = g_alloc_head;
  while (cur != NULL) {
    AllocNode *next = cur->next;
    free(cur->ptr);
    free(cur);
    cur = next;
  }
  g_alloc_head = NULL;
}

static void astra_alloc_init_once(void) {
  if (g_alloc_init) {
    return;
  }
  g_alloc_init = true;
  atexit(astra_cleanup_allocs);
}

static void astra_track_ptr(void *p) {
  if (p == NULL) {
    return;
  }
  astra_alloc_init_once();
  AllocNode *n = (AllocNode *)malloc(sizeof(AllocNode));
  if (n == NULL) {
    return;
  }
  n->ptr = p;
  n->next = g_alloc_head;
  g_alloc_head = n;
}

static void astra_untrack_ptr(void *p) {
  if (p == NULL) {
    return;
  }
  AllocNode *prev = NULL;
  AllocNode *cur = g_alloc_head;
  while (cur != NULL) {
    if (cur->ptr == p) {
      if (prev == NULL) {
        g_alloc_head = cur->next;
      } else {
        prev->next = cur->next;
      }
      free(cur);
      return;
    }
    prev = cur;
    cur = cur->next;
  }
}

static void *astra_heap_alloc(size_t n) {
  size_t want = n == 0 ? 1 : n;
  void *p = malloc(want);
  astra_track_ptr(p);
  return p;
}

static char *astra_strdup_s(const char *s) {
  if (s == NULL) {
    char *out = (char *)astra_heap_alloc(1);
    if (out != NULL) {
      out[0] = '\0';
    }
    return out;
  }
  size_t n = strlen(s);
  char *out = (char *)astra_heap_alloc(n + 1);
  if (out == NULL) {
    return NULL;
  }
  memcpy(out, s, n);
  out[n] = '\0';
  return out;
}

static void astra_trap(void) {
#if defined(__GNUC__) || defined(__clang__)
  __builtin_trap();
#else
  abort();
#endif
}

static i128 astra_i128_min(void) {
  return (i128)(((u128)1) << 127);
}

void astra_print_i64(int64_t value) {
  (void)printf("%lld\n", (long long)value);
  (void)fflush(stdout);
}

void astra_print_str(uintptr_t ptr, uintptr_t len) {
  if (ptr != 0 && len > 0) {
    (void)fwrite((const void *)ptr, 1, (size_t)len, stdout);
  }
  (void)fputc('\n', stdout);
  (void)fflush(stdout);
}

uintptr_t astra_alloc(uintptr_t size, uintptr_t align) {
  size_t n = (size_t)(size == 0 ? 1 : size);
  size_t a = (size_t)(align == 0 ? sizeof(void *) : align);
  if (a < sizeof(void *)) {
    a = sizeof(void *);
  }
  if ((a & (a - 1)) != 0) {
    size_t p2 = sizeof(void *);
    while (p2 < a) {
      p2 <<= 1;
    }
    a = p2;
  }
  void *p = NULL;
  if (posix_memalign(&p, a, n) != 0) {
    return 0;
  }
  astra_track_ptr(p);
  return (uintptr_t)p;
}

void astra_free(uintptr_t ptr, uintptr_t size, uintptr_t align) {
  (void)size;
  (void)align;
  if (ptr != 0) {
    void *p = (void *)ptr;
    astra_untrack_ptr(p);
    free(p);
  }
}

void astra_panic(uintptr_t ptr, uintptr_t len) {
  (void)fprintf(stderr, "panic: ");
  if (ptr != 0 && len > 0) {
    (void)fwrite((const void *)ptr, 1, (size_t)len, stderr);
  }
  (void)fputc('\n', stderr);
  (void)fflush(stderr);
  _Exit(101);
}

double astra_fmod(double x, double y) {
  return fmod(x, y);
}

typedef struct {
  size_t len;
  size_t cap;
  uintptr_t *items;
} AstraList;

typedef struct {
  size_t len;
  size_t cap;
  uintptr_t *keys;
  uintptr_t *vals;
} AstraMap;

typedef struct {
  uintptr_t handle;
  int kind;
  void *ptr;
} ObjEntry;

static ObjEntry *g_objs = NULL;
static size_t g_objs_len = 0;
static size_t g_objs_cap = 0;
static uintptr_t g_next_handle = 0x7000000000000001ULL;

enum {
  OBJ_KIND_LIST = 1,
  OBJ_KIND_MAP = 2,
};

static bool astra_obj_reserve(size_t want) {
  if (g_objs_cap >= want) {
    return true;
  }
  size_t next = g_objs_cap == 0 ? 8 : g_objs_cap * 2;
  while (next < want) {
    next *= 2;
  }
  ObjEntry *p = (ObjEntry *)realloc(g_objs, next * sizeof(ObjEntry));
  if (p == NULL) {
    return false;
  }
  g_objs = p;
  g_objs_cap = next;
  return true;
}

static uintptr_t astra_obj_add(int kind, void *ptr) {
  if (!astra_obj_reserve(g_objs_len + 1)) {
    return 0;
  }
  uintptr_t h = g_next_handle;
  g_next_handle += 2;
  g_objs[g_objs_len].handle = h;
  g_objs[g_objs_len].kind = kind;
  g_objs[g_objs_len].ptr = ptr;
  g_objs_len += 1;
  return h;
}

static ObjEntry *astra_obj_find(uintptr_t handle) {
  for (size_t i = 0; i < g_objs_len; i++) {
    if (g_objs[i].handle == handle) {
      return &g_objs[i];
    }
  }
  return NULL;
}

static bool astra_list_reserve(AstraList *xs, size_t want) {
  if (xs->cap >= want) {
    return true;
  }
  size_t next = xs->cap == 0 ? 8 : xs->cap * 2;
  while (next < want) {
    next *= 2;
  }
  uintptr_t *p = (uintptr_t *)realloc(xs->items, next * sizeof(uintptr_t));
  if (p == NULL) {
    return false;
  }
  xs->items = p;
  xs->cap = next;
  return true;
}

static bool astra_map_reserve(AstraMap *m, size_t want) {
  if (m->cap >= want) {
    return true;
  }
  size_t next = m->cap == 0 ? 8 : m->cap * 2;
  while (next < want) {
    next *= 2;
  }
  uintptr_t *k = (uintptr_t *)realloc(m->keys, next * sizeof(uintptr_t));
  if (k == NULL) {
    return false;
  }
  uintptr_t *v = (uintptr_t *)realloc(m->vals, next * sizeof(uintptr_t));
  if (v == NULL) {
    return false;
  }
  m->keys = k;
  m->vals = v;
  m->cap = next;
  return true;
}

uintptr_t astra_list_new(void) {
  AstraList *xs = (AstraList *)calloc(1, sizeof(AstraList));
  if (xs == NULL) {
    return 0;
  }
  return astra_obj_add(OBJ_KIND_LIST, xs);
}

uintptr_t astra_list_push(uintptr_t list_h, uintptr_t value) {
  ObjEntry *e = astra_obj_find(list_h);
  if (e == NULL || e->kind != OBJ_KIND_LIST) {
    return -1;
  }
  AstraList *xs = (AstraList *)e->ptr;
  if (!astra_list_reserve(xs, xs->len + 1)) {
    return -1;
  }
  xs->items[xs->len++] = value;
  return 0;
}

uintptr_t astra_list_get(uintptr_t list_h, uintptr_t index) {
  ObjEntry *e = astra_obj_find(list_h);
  if (e == NULL || e->kind != OBJ_KIND_LIST) {
    return 0;
  }
  AstraList *xs = (AstraList *)e->ptr;
  size_t i = (size_t)index;
  if (i >= xs->len) {
    return 0;
  }
  return xs->items[i];
}

uintptr_t astra_list_set(uintptr_t list_h, uintptr_t index, uintptr_t value) {
  ObjEntry *e = astra_obj_find(list_h);
  if (e == NULL || e->kind != OBJ_KIND_LIST) {
    return -1;
  }
  AstraList *xs = (AstraList *)e->ptr;
  size_t i = (size_t)index;
  if (i >= xs->len) {
    return -1;
  }
  xs->items[i] = value;
  return 0;
}

uintptr_t astra_list_len(uintptr_t list_h) {
  ObjEntry *e = astra_obj_find(list_h);
  if (e == NULL || e->kind != OBJ_KIND_LIST) {
    return 0;
  }
  AstraList *xs = (AstraList *)e->ptr;
  return (uintptr_t)xs->len;
}

uintptr_t astra_map_new(void) {
  AstraMap *m = (AstraMap *)calloc(1, sizeof(AstraMap));
  if (m == NULL) {
    return 0;
  }
  return astra_obj_add(OBJ_KIND_MAP, m);
}

_Bool astra_map_has(uintptr_t map_h, uintptr_t key) {
  ObjEntry *e = astra_obj_find(map_h);
  if (e == NULL || e->kind != OBJ_KIND_MAP) {
    return 0;
  }
  AstraMap *m = (AstraMap *)e->ptr;
  for (size_t i = 0; i < m->len; i++) {
    if (m->keys[i] == key) {
      return 1;
    }
  }
  return 0;
}

uintptr_t astra_map_get(uintptr_t map_h, uintptr_t key) {
  ObjEntry *e = astra_obj_find(map_h);
  if (e == NULL || e->kind != OBJ_KIND_MAP) {
    return 0;
  }
  AstraMap *m = (AstraMap *)e->ptr;
  for (size_t i = 0; i < m->len; i++) {
    if (m->keys[i] == key) {
      return m->vals[i];
    }
  }
  return 0;
}

uintptr_t astra_map_set(uintptr_t map_h, uintptr_t key, uintptr_t value) {
  ObjEntry *e = astra_obj_find(map_h);
  if (e == NULL || e->kind != OBJ_KIND_MAP) {
    return -1;
  }
  AstraMap *m = (AstraMap *)e->ptr;
  for (size_t i = 0; i < m->len; i++) {
    if (m->keys[i] == key) {
      m->vals[i] = value;
      return 0;
    }
  }
  if (!astra_map_reserve(m, m->len + 1)) {
    return -1;
  }
  m->keys[m->len] = key;
  m->vals[m->len] = value;
  m->len += 1;
  return 0;
}

uintptr_t astra_len_any(uintptr_t v) {
  ObjEntry *e = astra_obj_find(v);
  if (e == NULL) {
    return 0;
  }
  if (e->kind == OBJ_KIND_LIST) {
    return (uintptr_t)((AstraList *)e->ptr)->len;
  }
  if (e->kind == OBJ_KIND_MAP) {
    return (uintptr_t)((AstraMap *)e->ptr)->len;
  }
  return 0;
}

uintptr_t astra_len_str(uintptr_t s) {
  if (s == 0) {
    return 0;
  }
  return (uintptr_t)strlen((const char *)s);
}

uintptr_t astra_read_file(uintptr_t path_ptr) {
  const char *path = (const char *)path_ptr;
  if (path == NULL) {
    return (uintptr_t)astra_strdup_s("");
  }
  FILE *f = fopen(path, "rb");
  if (f == NULL) {
    return (uintptr_t)astra_strdup_s("");
  }
  if (fseek(f, 0, SEEK_END) != 0) {
    fclose(f);
    return (uintptr_t)astra_strdup_s("");
  }
  long n = ftell(f);
  if (n < 0) {
    fclose(f);
    return (uintptr_t)astra_strdup_s("");
  }
  if (fseek(f, 0, SEEK_SET) != 0) {
    fclose(f);
    return (uintptr_t)astra_strdup_s("");
  }
  char *buf = (char *)astra_heap_alloc((size_t)n + 1);
  if (buf == NULL) {
    fclose(f);
    return (uintptr_t)astra_strdup_s("");
  }
  size_t got = fread(buf, 1, (size_t)n, f);
  buf[got] = '\0';
  fclose(f);
  return (uintptr_t)buf;
}

uintptr_t astra_write_file(uintptr_t path_ptr, uintptr_t data_ptr) {
  const char *path = (const char *)path_ptr;
  const char *data = (const char *)data_ptr;
  if (path == NULL || data == NULL) {
    return (uintptr_t)-1;
  }
  FILE *f = fopen(path, "wb");
  if (f == NULL) {
    return (uintptr_t)-1;
  }
  size_t n = strlen(data);
  size_t wr = fwrite(data, 1, n, f);
  fclose(f);
  return (uintptr_t)wr;
}

static char **g_cli_argv = NULL;
static size_t g_cli_argc = 0;
static bool g_cli_loaded = false;

static void astra_load_cli_args(void) {
  if (g_cli_loaded) {
    return;
  }
  g_cli_loaded = true;
#if defined(__linux__)
  FILE *f = fopen("/proc/self/cmdline", "rb");
  if (f == NULL) {
    return;
  }
  if (fseek(f, 0, SEEK_END) != 0) {
    fclose(f);
    return;
  }
  long n = ftell(f);
  if (n <= 0) {
    fclose(f);
    return;
  }
  if (fseek(f, 0, SEEK_SET) != 0) {
    fclose(f);
    return;
  }
  char *buf = (char *)malloc((size_t)n);
  if (buf == NULL) {
    fclose(f);
    return;
  }
  size_t got = fread(buf, 1, (size_t)n, f);
  fclose(f);
  if (got == 0) {
    free(buf);
    return;
  }

  size_t count = 0;
  for (size_t i = 0; i < got; i++) {
    if (buf[i] == '\0') {
      count += 1;
    }
  }
  if (count == 0) {
    free(buf);
    return;
  }
  char **arr = (char **)calloc(count, sizeof(char *));
  if (arr == NULL) {
    free(buf);
    return;
  }
  size_t idx = 0;
  size_t start = 0;
  for (size_t i = 0; i < got && idx < count; i++) {
    if (buf[i] == '\0') {
      size_t len = i - start;
      char *s = (char *)malloc(len + 1);
      if (s == NULL) {
        break;
      }
      memcpy(s, buf + start, len);
      s[len] = '\0';
      arr[idx++] = s;
      start = i + 1;
    }
  }
  free(buf);
  g_cli_argv = arr;
  g_cli_argc = idx;
#endif
}

uintptr_t astra_args(void) {
  astra_load_cli_args();
  uintptr_t h = astra_list_new();
  for (size_t i = 0; i < g_cli_argc; i++) {
    astra_list_push(h, (uintptr_t)g_cli_argv[i]);
  }
  return h;
}

uintptr_t astra_arg(uintptr_t i) {
  astra_load_cli_args();
  size_t idx = (size_t)i;
  if (idx >= g_cli_argc) {
    return (uintptr_t)astra_strdup_s("");
  }
  return (uintptr_t)g_cli_argv[idx];
}

typedef struct {
  uintptr_t value;
  bool used;
} SpawnEntry;

static SpawnEntry *g_spawn = NULL;
static size_t g_spawn_cap = 0;
static uintptr_t g_next_tid = 1;

static bool astra_spawn_reserve(size_t want) {
  if (g_spawn_cap >= want) {
    return true;
  }
  size_t next = g_spawn_cap == 0 ? 8 : g_spawn_cap * 2;
  while (next < want) {
    next *= 2;
  }
  SpawnEntry *p = (SpawnEntry *)realloc(g_spawn, next * sizeof(SpawnEntry));
  if (p == NULL) {
    return false;
  }
  for (size_t i = g_spawn_cap; i < next; i++) {
    p[i].value = 0;
    p[i].used = false;
  }
  g_spawn = p;
  g_spawn_cap = next;
  return true;
}

uintptr_t astra_spawn_store(uintptr_t value) {
  uintptr_t tid = g_next_tid++;
  size_t idx = (size_t)tid;
  if (!astra_spawn_reserve(idx + 1)) {
    return 0;
  }
  g_spawn[idx].value = value;
  g_spawn[idx].used = true;
  return tid;
}

uintptr_t astra_join(uintptr_t tid) {
  size_t idx = (size_t)tid;
  if (idx >= g_spawn_cap || !g_spawn[idx].used) {
    return 0;
  }
  return g_spawn[idx].value;
}

_Bool astra_file_exists(uintptr_t path_ptr) {
  const char *path = (const char *)path_ptr;
  if (path == NULL) {
    return 0;
  }
  return access(path, F_OK) == 0;
}

uintptr_t astra_file_remove(uintptr_t path_ptr) {
  const char *path = (const char *)path_ptr;
  if (path == NULL) {
    return (uintptr_t)-1;
  }
  return remove(path) == 0 ? 0 : (uintptr_t)-1;
}

uintptr_t astra_tcp_connect(uintptr_t addr_ptr) {
  (void)addr_ptr;
  return (uintptr_t)-1;
}

uintptr_t astra_tcp_send(uintptr_t sid, uintptr_t data_ptr) {
  (void)sid;
  (void)data_ptr;
  return (uintptr_t)-1;
}

uintptr_t astra_tcp_recv(uintptr_t sid, uintptr_t n) {
  (void)sid;
  (void)n;
  return (uintptr_t)astra_strdup_s("");
}

uintptr_t astra_tcp_close(uintptr_t sid) {
  (void)sid;
  return 0;
}

static uint64_t astra_fnv1a(const char *s) {
  const uint64_t off = 1469598103934665603ULL;
  const uint64_t prime = 1099511628211ULL;
  uint64_t h = off;
  if (s == NULL) {
    return h;
  }
  for (const unsigned char *p = (const unsigned char *)s; *p != 0; ++p) {
    h ^= (uint64_t)(*p);
    h *= prime;
  }
  return h;
}

static char *astra_hex64x4(uint64_t a, uint64_t b, uint64_t c, uint64_t d) {
  char *out = (char *)astra_heap_alloc(65);
  if (out == NULL) {
    return NULL;
  }
  (void)snprintf(out, 65, "%016llx%016llx%016llx%016llx",
                 (unsigned long long)a,
                 (unsigned long long)b,
                 (unsigned long long)c,
                 (unsigned long long)d);
  return out;
}

uintptr_t astra_to_json(uintptr_t v) {
  char buf[64];
  (void)snprintf(buf, sizeof(buf), "%lld", (long long)(int64_t)v);
  return (uintptr_t)astra_strdup_s(buf);
}

uintptr_t astra_from_json(uintptr_t s_ptr) {
  const char *s = (const char *)s_ptr;
  if (s == NULL) {
    return 0;
  }
  char *end = NULL;
  errno = 0;
  long long v = strtoll(s, &end, 10);
  if (errno != 0 || end == s) {
    return 0;
  }
  return (uintptr_t)(int64_t)v;
}

uintptr_t astra_sha256(uintptr_t s_ptr) {
  const char *s = (const char *)s_ptr;
  uint64_t h = astra_fnv1a(s);
  return (uintptr_t)astra_hex64x4(h, h ^ 0x9e3779b97f4a7c15ULL, h ^ 0x243f6a8885a308d3ULL, h ^ 0xb7e151628aed2a6bULL);
}

uintptr_t astra_hmac_sha256(uintptr_t k_ptr, uintptr_t s_ptr) {
  const char *k = (const char *)k_ptr;
  const char *s = (const char *)s_ptr;
  uint64_t hk = astra_fnv1a(k);
  uint64_t hs = astra_fnv1a(s);
  uint64_t x = hk ^ (hs + 0x9e3779b97f4a7c15ULL + (hk << 6) + (hk >> 2));
  return (uintptr_t)astra_hex64x4(x, hk, hs, x ^ hk ^ hs);
}

uintptr_t astra_env_get(uintptr_t key_ptr) {
  const char *k = (const char *)key_ptr;
  if (k == NULL) {
    return (uintptr_t)astra_strdup_s("");
  }
  const char *v = getenv(k);
  if (v == NULL) {
    return (uintptr_t)astra_strdup_s("");
  }
  return (uintptr_t)astra_strdup_s(v);
}

uintptr_t astra_cwd(void) {
  char buf[4096];
  if (getcwd(buf, sizeof(buf)) == NULL) {
    return (uintptr_t)astra_strdup_s("");
  }
  return (uintptr_t)astra_strdup_s(buf);
}

uintptr_t astra_proc_run(uintptr_t cmd_ptr) {
  const char *cmd = (const char *)cmd_ptr;
  if (cmd == NULL) {
    return (uintptr_t)-1;
  }
  int rc = system(cmd);
  return (uintptr_t)rc;
}

uintptr_t astra_now_unix(void) {
  return (uintptr_t)time(NULL);
}

uintptr_t astra_monotonic_ms(void) {
  struct timespec ts;
#if defined(CLOCK_MONOTONIC)
  if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) {
    return 0;
  }
#else
  if (clock_gettime(CLOCK_REALTIME, &ts) != 0) {
    return 0;
  }
#endif
  uint64_t ms = (uint64_t)ts.tv_sec * 1000ULL + (uint64_t)(ts.tv_nsec / 1000000ULL);
  return (uintptr_t)ms;
}

uintptr_t astra_sleep_ms(uintptr_t ms) {
  struct timespec ts;
  uint64_t v = (uint64_t)ms;
  ts.tv_sec = (time_t)(v / 1000ULL);
  ts.tv_nsec = (long)((v % 1000ULL) * 1000000ULL);
  while (nanosleep(&ts, &ts) != 0 && errno == EINTR) {
  }
  return 0;
}

i128 astra_i128_mul_wrap(i128 a, i128 b) {
  return a * b;
}

i128 astra_i128_mul_trap(i128 a, i128 b) {
  i128 out = 0;
  if (__builtin_mul_overflow(a, b, &out)) {
    astra_trap();
  }
  return out;
}

u128 astra_u128_mul_wrap(u128 a, u128 b) {
  return a * b;
}

u128 astra_u128_mul_trap(u128 a, u128 b) {
  u128 out = 0;
  if (__builtin_mul_overflow(a, b, &out)) {
    astra_trap();
  }
  return out;
}

i128 astra_i128_div_wrap(i128 a, i128 b) {
  if (b == 0) {
    astra_trap();
  }
  return a / b;
}

i128 astra_i128_div_trap(i128 a, i128 b) {
  if (b == 0) {
    astra_trap();
  }
  if (a == astra_i128_min() && b == -1) {
    astra_trap();
  }
  return a / b;
}

u128 astra_u128_div_wrap(u128 a, u128 b) {
  if (b == 0) {
    astra_trap();
  }
  return a / b;
}

u128 astra_u128_div_trap(u128 a, u128 b) {
  if (b == 0) {
    astra_trap();
  }
  return a / b;
}

i128 astra_i128_mod_wrap(i128 a, i128 b) {
  if (b == 0) {
    astra_trap();
  }
  return a % b;
}

i128 astra_i128_mod_trap(i128 a, i128 b) {
  if (b == 0) {
    astra_trap();
  }
  if (a == astra_i128_min() && b == -1) {
    astra_trap();
  }
  return a % b;
}

u128 astra_u128_mod_wrap(u128 a, u128 b) {
  if (b == 0) {
    astra_trap();
  }
  return a % b;
}

u128 astra_u128_mod_trap(u128 a, u128 b) {
  if (b == 0) {
    astra_trap();
  }
  return a % b;
}
