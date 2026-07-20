import type { components as ServiceDeskContract } from "@prom/generated-contracts/service-desk";

type Schemas = ServiceDeskContract["schemas"];

export type ServiceDeskCategory = Schemas["CategoryRead"];
export type ServiceDeskService = Schemas["ServiceRead"];
export type ServiceDeskTemplateFieldType = Schemas["TemplateFieldType"];
export type ServiceDeskTemplateField = Omit<
  Schemas["TemplateFieldPreviewRead"],
  "effective_options" | "options"
> & {
  effective_options?: Array<{
    label?: string;
    value?: string;
    position?: number;
    is_active?: boolean;
  }>;
  options: Array<{ label?: string; value?: string }> | null;
};
type ServiceDeskPublishedTemplateVersion = Omit<
  Schemas["TemplateVersionRead"],
  "system_settings"
> & {
  system_settings: {
    default_title?: string | null;
    is_title_editable?: boolean;
    is_description_required?: boolean;
    help_text?: string | null;
  };
};
export type ServiceDeskPublishedForm = Omit<
  Schemas["PublishedTemplateRead"],
  "fields" | "template_version"
> & {
  fields: ServiceDeskTemplateField[];
  template_version: ServiceDeskPublishedTemplateVersion;
};
