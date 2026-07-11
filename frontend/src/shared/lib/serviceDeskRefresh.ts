import { onServiceDeskCountersInvalidated } from "./serviceDeskCounterInvalidation";

export const SERVICE_DESK_REFRESH_INTERVAL_MS = 60_000;

type RefreshSubscriptionOptions = {
  intervalMs?: number;
  onInvalidated?: (listener: () => void) => () => void;
  setIntervalFn?: (listener: () => void, intervalMs: number) => number;
  clearIntervalFn?: (timerId: number) => void;
};

export function subscribeToServiceDeskRefresh(
  refresh: () => void,
  {
    intervalMs = SERVICE_DESK_REFRESH_INTERVAL_MS,
    onInvalidated = onServiceDeskCountersInvalidated,
    setIntervalFn = (listener, ms) => window.setInterval(listener, ms),
    clearIntervalFn = (timerId) => window.clearInterval(timerId)
  }: RefreshSubscriptionOptions = {}
) {
  const unsubscribeInvalidation = onInvalidated(refresh);
  const timerId = setIntervalFn(refresh, intervalMs);
  return () => {
    unsubscribeInvalidation();
    clearIntervalFn(timerId);
  };
}
