import type { components as ServiceDeskContract } from "@prom/generated-contracts/service-desk";

export type ServiceDeskUser =
  ServiceDeskContract["schemas"]["ServiceDeskUserRead"];
