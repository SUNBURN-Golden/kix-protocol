#ifndef KIX_GPU_H
#define KIX_GPU_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Forward declarations from the Arrow C / C Device interfaces. */
struct ArrowSchema;
struct ArrowDeviceArray;

typedef struct KixGpuContext KixGpuContext;

typedef enum KixGpuStatus {
  KIX_GPU_OK = 0,
  KIX_GPU_INVALID_ARGUMENT = 1,
  KIX_GPU_UNSUPPORTED_PLAN = 2,
  KIX_GPU_OUT_OF_MEMORY = 3,
  KIX_GPU_CUDA_ERROR = 4,
  KIX_GPU_INTERNAL_ERROR = 5
} KixGpuStatus;

typedef struct KixByteSlice {
  const uint8_t* data;
  size_t len;
} KixByteSlice;

typedef struct KixGpuOptions {
  int32_t device_id;
  uint32_t stream_count;
  uint64_t device_pool_bytes;
  uint64_t pinned_host_pool_bytes;
} KixGpuOptions;

typedef struct KixGpuInput {
  uint16_t slot;
  const struct ArrowSchema* schema;
  const struct ArrowDeviceArray* array;
} KixGpuInput;

/* Context is long-lived: one instance per GPU/NUMA placement is preferred. */
KixGpuStatus kix_gpu_context_create(
    const KixGpuOptions* options,
    KixGpuContext** out_context);

void kix_gpu_context_destroy(KixGpuContext* context);

/*
 * Execute a KIX Feature IR v1 plan encoded with its registered KIX-BCS1 schema.
 * Input/output ownership follows Arrow C Device release-callback semantics.
 * The native implementation must use libcudf and a persistent RMM resource.
 */
KixGpuStatus kix_gpu_execute_feature_plan_v1(
    KixGpuContext* context,
    KixByteSlice feature_plan_bcs,
    const KixGpuInput* inputs,
    size_t input_count,
    struct ArrowSchema* out_schema,
    struct ArrowDeviceArray* out_array);

/* Thread-local/context-local diagnostic text; never business authority. */
const char* kix_gpu_last_error(const KixGpuContext* context);

#ifdef __cplusplus
}
#endif

#endif /* KIX_GPU_H */
