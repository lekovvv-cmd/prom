export type ServiceDeskRoutingConditionField =
  | "service_id"
  | "category_id"
  | "priority"
  | "field_value";

export type ServiceDeskRoutingCondition = {
  field: ServiceDeskRoutingConditionField;
  operator: "equals";
  value: string;
  field_key?: string | null;
};

export type ServiceDeskRoutingAction =
  | {
      type: "assign_user";
      user_id: string;
      priority?: never;
    }
  | {
      type: "set_priority";
      priority: "low" | "medium" | "high" | "critical";
      user_id?: never;
    };

export type ServiceDeskRoutingRule = {
  id: string;
  name: string;
  priority: number;
  is_active: boolean;
  conditions: ServiceDeskRoutingCondition[];
  action: ServiceDeskRoutingAction;
  created_at: string;
  updated_at: string;
};

export type ServiceDeskRoutingRulePayload = {
  name: string;
  priority: number;
  is_active: boolean;
  conditions: ServiceDeskRoutingCondition[];
  action: ServiceDeskRoutingAction;
};

export type ServiceDeskRoutingAssignee = {
  id: string;
  display_name: string;
  email: string;
};

export type ServiceDeskRoutingCatalogOptions = {
  categories: import("../../service-desk-catalog/model/types").ServiceDeskCategory[];
  services: import("../../service-desk-catalog/model/types").ServiceDeskService[];
};
