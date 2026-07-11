const COUNTERS_INVALIDATED = "service-desk:counters-invalidated";

export function invalidateServiceDeskCounters() {
  window.dispatchEvent(new Event(COUNTERS_INVALIDATED));
}

export function onServiceDeskCountersInvalidated(listener: () => void) {
  window.addEventListener(COUNTERS_INVALIDATED, listener);
  return () => window.removeEventListener(COUNTERS_INVALIDATED, listener);
}
