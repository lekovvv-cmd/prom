import { describe, expect, it, vi } from "vitest";
import {
  SERVICE_DESK_REFRESH_INTERVAL_MS,
  subscribeToServiceDeskRefresh
} from "./serviceDeskRefresh";

describe("subscribeToServiceDeskRefresh", () => {
  it("refreshes on invalidation and timer, then cleans up both", () => {
    const refresh = vi.fn();
    const unsubscribe = vi.fn();
    const listeners: Array<() => void> = [];
    const clearIntervalFn = vi.fn();
    const cleanup = subscribeToServiceDeskRefresh(refresh, {
      onInvalidated: (listener) => {
        listeners.push(listener);
        return unsubscribe;
      },
      setIntervalFn: (listener, intervalMs) => {
        listeners.push(listener);
        expect(intervalMs).toBe(SERVICE_DESK_REFRESH_INTERVAL_MS);
        return 42;
      },
      clearIntervalFn
    });

    listeners[0]();
    listeners[1]();
    expect(refresh).toHaveBeenCalledTimes(2);

    cleanup();
    expect(unsubscribe).toHaveBeenCalledTimes(1);
    expect(clearIntervalFn).toHaveBeenCalledWith(42);
  });
});
