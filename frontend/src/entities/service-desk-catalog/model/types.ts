export type ServiceDeskCategory = {
  id: string;
  title: string;
  description: string | null;
  parent_id: string | null;
  position: number;
  is_active: boolean;
  deleted_at: string | null;
};

export type ServiceDeskService = {
  id: string;
  category_id: string;
  title: string;
  short_description: string | null;
  description: string | null;
  position: number;
  is_active: boolean;
  deleted_at: string | null;
  category: ServiceDeskCategory | null;
  request_form_available?: boolean;
};

export type ServiceDeskTemplateFieldType = "text" | "textarea" | "rich_text" | "select" | "multiselect" | "date" | "time" | "datetime" | "email" | "number" | "checkbox" | "file" | "user";

export type ServiceDeskTemplateField = {
  id: string;
  template_version_id: string;
  key: string;
  label: string;
  field_type: ServiceDeskTemplateFieldType;
  is_required: boolean;
  position: number;
  help_text: string | null;
  placeholder: string | null;
  options: Array<{ label?: string; value?: string }> | null;
  effective_options?: Array<{ label?: string; value?: string; position?: number; is_active?: boolean }>;
  dictionary_code: string | null;
  validation: Record<string, unknown> | null;
  visibility_rules: Record<string, unknown> | Array<Record<string, unknown>> | null;
  required_rules: Record<string, unknown> | Array<Record<string, unknown>> | null;
};

export type ServiceDeskPublishedForm = {
  service_id: string;
  template_version: {
    id: string;
    version: number;
    status: "draft" | "published" | "archived";
    system_settings: {
      default_title?: string | null;
      is_title_editable?: boolean;
      is_description_required?: boolean;
      help_text?: string | null;
    };
  };
  fields: ServiceDeskTemplateField[];
};
