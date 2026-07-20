// Generated from service-desk.openapi.json. Do not edit by hand.
export interface paths {
    "/access/status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Access Status */
        get: operations["get_access_status_access_status_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/access/users": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Users */
        get: operations["users_admin_access_users_get"];
        put?: never;
        /** Create */
        post: operations["create_admin_access_users_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/access/users/{user_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update */
        patch: operations["update_admin_access_users__user_id__patch"];
        trace?: never;
    };
    "/admin/access/users/{user_id}/activate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Activate */
        post: operations["activate_admin_access_users__user_id__activate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/access/users/{user_id}/capabilities": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Capabilities */
        put: operations["capabilities_admin_access_users__user_id__capabilities_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/access/users/{user_id}/deactivate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Deactivate */
        post: operations["deactivate_admin_access_users__user_id__deactivate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/approval-stage-approvers/{approver_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Stage Approver */
        delete: operations["delete_stage_approver_admin_approval_stage_approvers__approver_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/approval-stages/{stage_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Approval Stage */
        delete: operations["delete_approval_stage_admin_approval_stages__stage_id__delete"];
        options?: never;
        head?: never;
        /** Update Approval Stage */
        patch: operations["update_approval_stage_admin_approval_stages__stage_id__patch"];
        trace?: never;
    };
    "/admin/approval-stages/{stage_id}/approvers": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Add Stage Approver */
        post: operations["add_stage_approver_admin_approval_stages__stage_id__approvers_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/approval-workflows/{workflow_id}/reorder-stages": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reorder Approval Stages */
        post: operations["reorder_approval_stages_admin_approval_workflows__workflow_id__reorder_stages_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/approval-workflows/{workflow_id}/stages": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Approval Stage */
        post: operations["create_approval_stage_admin_approval_workflows__workflow_id__stages_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/categories": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Admin List Categories */
        get: operations["admin_list_categories_admin_categories_get"];
        put?: never;
        /** Admin Create Category */
        post: operations["admin_create_category_admin_categories_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/categories/{category_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Admin Update Category */
        patch: operations["admin_update_category_admin_categories__category_id__patch"];
        trace?: never;
    };
    "/admin/categories/{category_id}/deactivate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Admin Deactivate Category */
        post: operations["admin_deactivate_category_admin_categories__category_id__deactivate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/categories/{category_id}/restore": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Admin Restore Category */
        post: operations["admin_restore_category_admin_categories__category_id__restore_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/dictionaries": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Dictionaries */
        get: operations["list_dictionaries_admin_dictionaries_get"];
        put?: never;
        /** Create Dictionary */
        post: operations["create_dictionary_admin_dictionaries_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/dictionaries/{dictionary_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Dictionary */
        patch: operations["update_dictionary_admin_dictionaries__dictionary_id__patch"];
        trace?: never;
    };
    "/admin/dictionaries/{dictionary_id}/items": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Dictionary Item */
        post: operations["create_dictionary_item_admin_dictionaries__dictionary_id__items_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/dictionary-items/{item_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Dictionary Item */
        patch: operations["update_dictionary_item_admin_dictionary_items__item_id__patch"];
        trace?: never;
    };
    "/admin/routing-rules": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Routing Rules */
        get: operations["list_routing_rules_admin_routing_rules_get"];
        put?: never;
        /** Create Routing Rule */
        post: operations["create_routing_rule_admin_routing_rules_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/routing-rules/candidates": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Routing Candidates */
        get: operations["list_routing_candidates_admin_routing_rules_candidates_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/routing-rules/catalog-options": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Routing Catalog Options */
        get: operations["list_routing_catalog_options_admin_routing_rules_catalog_options_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/routing-rules/reorder": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reorder Routing Rules */
        post: operations["reorder_routing_rules_admin_routing_rules_reorder_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/routing-rules/{rule_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Routing Rule */
        delete: operations["delete_routing_rule_admin_routing_rules__rule_id__delete"];
        options?: never;
        head?: never;
        /** Update Routing Rule */
        patch: operations["update_routing_rule_admin_routing_rules__rule_id__patch"];
        trace?: never;
    };
    "/admin/services": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Admin List Services */
        get: operations["admin_list_services_admin_services_get"];
        put?: never;
        /** Admin Create Service */
        post: operations["admin_create_service_admin_services_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/services/{service_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Admin Update Service */
        patch: operations["admin_update_service_admin_services__service_id__patch"];
        trace?: never;
    };
    "/admin/services/{service_id}/approval-workflow": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Service Approval Workflow */
        get: operations["get_service_approval_workflow_admin_services__service_id__approval_workflow_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/services/{service_id}/approval-workflow/apply": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Apply Service Approval Workflow */
        post: operations["apply_service_approval_workflow_admin_services__service_id__approval_workflow_apply_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/services/{service_id}/deactivate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Admin Deactivate Service */
        post: operations["admin_deactivate_service_admin_services__service_id__deactivate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/services/{service_id}/restore": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Admin Restore Service */
        post: operations["admin_restore_service_admin_services__service_id__restore_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/services/{service_id}/versions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Template Versions */
        get: operations["list_template_versions_admin_services__service_id__versions_get"];
        put?: never;
        /** Create Template Version */
        post: operations["create_template_version_admin_services__service_id__versions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/sla/bindings": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Sla Bindings */
        get: operations["list_sla_bindings_admin_sla_bindings_get"];
        put?: never;
        /** Create Sla Binding */
        post: operations["create_sla_binding_admin_sla_bindings_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/sla/bindings/{binding_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Sla Binding */
        patch: operations["update_sla_binding_admin_sla_bindings__binding_id__patch"];
        trace?: never;
    };
    "/admin/sla/calendars": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Business Calendars */
        get: operations["list_business_calendars_admin_sla_calendars_get"];
        put?: never;
        /** Create Business Calendar */
        post: operations["create_business_calendar_admin_sla_calendars_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/sla/calendars/{calendar_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Business Calendar */
        patch: operations["update_business_calendar_admin_sla_calendars__calendar_id__patch"];
        trace?: never;
    };
    "/admin/sla/escalations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Escalations */
        get: operations["list_escalations_admin_sla_escalations_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/sla/escalations/{rule_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Escalation */
        delete: operations["delete_escalation_admin_sla_escalations__rule_id__delete"];
        options?: never;
        head?: never;
        /** Update Escalation */
        patch: operations["update_escalation_admin_sla_escalations__rule_id__patch"];
        trace?: never;
    };
    "/admin/sla/policies": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Sla Policies */
        get: operations["list_sla_policies_admin_sla_policies_get"];
        put?: never;
        /** Create Sla Policy */
        post: operations["create_sla_policy_admin_sla_policies_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/sla/policies/{policy_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Sla Policy */
        patch: operations["update_sla_policy_admin_sla_policies__policy_id__patch"];
        trace?: never;
    };
    "/admin/sla/policies/{policy_id}/escalations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Escalation */
        post: operations["create_escalation_admin_sla_policies__policy_id__escalations_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/sla/recipients": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Sla Recipients */
        get: operations["list_sla_recipients_admin_sla_recipients_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/stats/approvals": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Approvals */
        get: operations["approvals_admin_stats_approvals_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/stats/assignees": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Assignees */
        get: operations["assignees_admin_stats_assignees_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/stats/backlog-aging": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Backlog */
        get: operations["backlog_admin_stats_backlog_aging_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/stats/categories": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Categories */
        get: operations["categories_admin_stats_categories_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/stats/services": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Services */
        get: operations["services_admin_stats_services_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/stats/sla": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Sla */
        get: operations["sla_admin_stats_sla_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/stats/statuses": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Statuses */
        get: operations["statuses_admin_stats_statuses_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/stats/summary": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Summary */
        get: operations["summary_admin_stats_summary_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/stats/times": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Times */
        get: operations["times_admin_stats_times_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/template-fields/{field_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Template Field */
        delete: operations["delete_template_field_admin_template_fields__field_id__delete"];
        options?: never;
        head?: never;
        /** Update Template Field */
        patch: operations["update_template_field_admin_template_fields__field_id__patch"];
        trace?: never;
    };
    "/admin/template-versions/{version_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Template Version */
        get: operations["get_template_version_admin_template_versions__version_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Template Version */
        patch: operations["update_template_version_admin_template_versions__version_id__patch"];
        trace?: never;
    };
    "/admin/template-versions/{version_id}/approval-workflow": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Approval Workflow */
        get: operations["get_approval_workflow_admin_template_versions__version_id__approval_workflow_get"];
        /** Configure Approval Workflow */
        put: operations["configure_approval_workflow_admin_template_versions__version_id__approval_workflow_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/template-versions/{version_id}/fields": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Template Field */
        post: operations["create_template_field_admin_template_versions__version_id__fields_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/template-versions/{version_id}/preview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Preview Template Version */
        get: operations["preview_template_version_admin_template_versions__version_id__preview_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/template-versions/{version_id}/publish": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Publish Template Version */
        post: operations["publish_template_version_admin_template_versions__version_id__publish_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/template-versions/{version_id}/reorder-fields": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reorder Template Fields */
        post: operations["reorder_template_fields_admin_template_versions__version_id__reorder_fields_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/template-versions/{version_id}/validate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Validate Template Payload */
        post: operations["validate_template_payload_admin_template_versions__version_id__validate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Api Health */
        get: operations["api_health_api_health_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/categories": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Categories */
        get: operations["list_categories_categories_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/health/live": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Live */
        get: operations["live_health_live_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/health/ready": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Ready */
        get: operations["ready_health_ready_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Me */
        get: operations["get_me_me_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/me/capabilities": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get My Capabilities */
        get: operations["get_my_capabilities_me_capabilities_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/me/tickets": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List My Tickets */
        get: operations["list_my_tickets_me_tickets_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/notifications": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Notifications */
        get: operations["list_notifications_notifications_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/notifications/contextual-counters": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Contextual Counters */
        get: operations["contextual_counters_notifications_contextual_counters_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/notifications/read-all": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Read All */
        post: operations["read_all_notifications_read_all_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/notifications/unread-count": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Unread Count */
        get: operations["unread_count_notifications_unread_count_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/notifications/{notification_id}/read": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Read Notification */
        post: operations["read_notification_notifications__notification_id__read_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/services": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Services */
        get: operations["list_services_services_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/services/{service_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Service */
        get: operations["get_service_services__service_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/services/{service_id}/form": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Service Form */
        get: operations["get_service_form_services__service_id__form_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tickets/drafts": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Ticket Draft */
        post: operations["create_ticket_draft_tickets_drafts_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tickets/{ticket_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Ticket */
        get: operations["get_ticket_tickets__ticket_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Ticket Draft */
        patch: operations["update_ticket_draft_tickets__ticket_id__patch"];
        trace?: never;
    };
    "/tickets/{ticket_id}/approvals": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Ticket Approvals */
        get: operations["get_ticket_approvals_tickets__ticket_id__approvals_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tickets/{ticket_id}/approvals/{approval_id}/approve": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Approve Ticket */
        post: operations["approve_ticket_tickets__ticket_id__approvals__approval_id__approve_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tickets/{ticket_id}/approvals/{approval_id}/reject": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reject Ticket */
        post: operations["reject_ticket_tickets__ticket_id__approvals__approval_id__reject_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tickets/{ticket_id}/assign": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Assign Ticket */
        post: operations["assign_ticket_tickets__ticket_id__assign_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tickets/{ticket_id}/attachments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Ticket Attachments */
        get: operations["list_ticket_attachments_tickets__ticket_id__attachments_get"];
        put?: never;
        /** Upload Ticket Attachment */
        post: operations["upload_ticket_attachment_tickets__ticket_id__attachments_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tickets/{ticket_id}/attachments/{attachment_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Ticket Attachment */
        delete: operations["delete_ticket_attachment_tickets__ticket_id__attachments__attachment_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tickets/{ticket_id}/attachments/{attachment_id}/download": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Download Ticket Attachment */
        get: operations["download_ticket_attachment_tickets__ticket_id__attachments__attachment_id__download_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tickets/{ticket_id}/cancel": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Cancel Ticket */
        post: operations["cancel_ticket_tickets__ticket_id__cancel_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tickets/{ticket_id}/close": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Close Ticket */
        post: operations["close_ticket_tickets__ticket_id__close_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tickets/{ticket_id}/comments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Ticket Comments */
        get: operations["list_ticket_comments_tickets__ticket_id__comments_get"];
        put?: never;
        /** Create Ticket Comment */
        post: operations["create_ticket_comment_tickets__ticket_id__comments_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tickets/{ticket_id}/comments/{comment_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Ticket Comment */
        delete: operations["delete_ticket_comment_tickets__ticket_id__comments__comment_id__delete"];
        options?: never;
        head?: never;
        /** Update Ticket Comment */
        patch: operations["update_ticket_comment_tickets__ticket_id__comments__comment_id__patch"];
        trace?: never;
    };
    "/tickets/{ticket_id}/comments/{comment_id}/attachments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Comment Attachments */
        get: operations["list_comment_attachments_tickets__ticket_id__comments__comment_id__attachments_get"];
        put?: never;
        /** Upload Comment Attachment */
        post: operations["upload_comment_attachment_tickets__ticket_id__comments__comment_id__attachments_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tickets/{ticket_id}/fields/{field_key}/attachments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Field Attachments */
        get: operations["list_field_attachments_tickets__ticket_id__fields__field_key__attachments_get"];
        put?: never;
        /** Upload Field Attachment */
        post: operations["upload_field_attachment_tickets__ticket_id__fields__field_key__attachments_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tickets/{ticket_id}/form": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Ticket Form */
        get: operations["get_ticket_form_tickets__ticket_id__form_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tickets/{ticket_id}/priority": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Change Ticket Priority */
        patch: operations["change_ticket_priority_tickets__ticket_id__priority_patch"];
        trace?: never;
    };
    "/tickets/{ticket_id}/reassign": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reassign Ticket */
        post: operations["reassign_ticket_tickets__ticket_id__reassign_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tickets/{ticket_id}/request-clarification": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Request Ticket Clarification */
        post: operations["request_ticket_clarification_tickets__ticket_id__request_clarification_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tickets/{ticket_id}/resolve": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Resolve Ticket */
        post: operations["resolve_ticket_tickets__ticket_id__resolve_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tickets/{ticket_id}/resume": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Resume Ticket */
        post: operations["resume_ticket_tickets__ticket_id__resume_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tickets/{ticket_id}/start": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Start Ticket */
        post: operations["start_ticket_tickets__ticket_id__start_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tickets/{ticket_id}/submit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Submit Ticket Draft */
        post: operations["submit_ticket_draft_tickets__ticket_id__submit_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tickets/{ticket_id}/wait-external": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Wait For External Action */
        post: operations["wait_for_external_action_tickets__ticket_id__wait_external_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/users/options": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get User Options */
        get: operations["get_user_options_users_options_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/workbench/counters": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Workbench Counters */
        get: operations["get_workbench_counters_workbench_counters_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/workbench/tickets": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Workbench Tickets */
        get: operations["list_workbench_tickets_workbench_tickets_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/workbench/users": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Workbench Users */
        get: operations["get_workbench_users_workbench_users_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** AccessUserCreate */
        AccessUserCreate: {
            access_type: components["schemas"]["ServiceDeskAccessType"];
            /**
             * Capabilities
             * @default []
             */
            capabilities: string[];
            /** Department */
            department?: string | null;
            /** Display Name */
            display_name: string;
            /** Email */
            email: string;
            /** Identity User Id */
            identity_user_id: string;
            /** Position */
            position?: string | null;
        };
        /** AccessUserPage */
        AccessUserPage: {
            /** Items */
            items: components["schemas"]["ServiceDeskUserRead"][];
            /** Page */
            page: number;
            /** Page Size */
            page_size: number;
            /** Pages */
            pages: number;
            /** Total */
            total: number;
        };
        /** AccessUserUpdate */
        AccessUserUpdate: {
            access_type?: components["schemas"]["ServiceDeskAccessType"] | null;
            /** Department */
            department?: string | null;
            /** Display Name */
            display_name?: string | null;
            /** Email */
            email?: string | null;
            /** Position */
            position?: string | null;
        };
        /**
         * ApprovalDecisionRule
         * @enum {string}
         */
        ApprovalDecisionRule: "any" | "all";
        /**
         * ApprovalMode
         * @enum {string}
         */
        ApprovalMode: "none" | "workflow";
        /** ApprovalStageApproverCreate */
        ApprovalStageApproverCreate: {
            /**
             * Service Desk User Id
             * Format: uuid
             */
            service_desk_user_id: string;
        };
        /** ApprovalStageApproverRead */
        ApprovalStageApproverRead: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Service Desk User Id
             * Format: uuid
             */
            service_desk_user_id: string;
            /**
             * Stage Id
             * Format: uuid
             */
            stage_id: string;
        };
        /** ApprovalStageCreate */
        ApprovalStageCreate: {
            decision_rule: components["schemas"]["ApprovalDecisionRule"];
            /** Position */
            position?: number | null;
            /** Title */
            title: string;
        };
        /** ApprovalStageRead */
        ApprovalStageRead: {
            /** Approvers */
            approvers?: components["schemas"]["ApprovalStageApproverRead"][];
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            decision_rule: components["schemas"]["ApprovalDecisionRule"];
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Position */
            position: number;
            /** Title */
            title: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /**
             * Workflow Id
             * Format: uuid
             */
            workflow_id: string;
        };
        /** ApprovalStageUpdate */
        ApprovalStageUpdate: {
            decision_rule?: components["schemas"]["ApprovalDecisionRule"] | null;
            /** Position */
            position?: number | null;
            /** Title */
            title?: string | null;
        };
        /** ApprovalStagesReorder */
        ApprovalStagesReorder: {
            /** Stage Ids */
            stage_ids: string[];
        };
        /** ApprovalWorkflowApply */
        ApprovalWorkflowApply: {
            approval_mode: components["schemas"]["ApprovalMode"];
            /**
             * Name
             * @default ������������ ������
             */
            name: string;
            /** Stages */
            stages?: components["schemas"]["ApprovalWorkflowStageApply"][];
        };
        /** ApprovalWorkflowConfigurationRead */
        ApprovalWorkflowConfigurationRead: {
            approval_mode: components["schemas"]["ApprovalMode"];
            /**
             * Template Version Id
             * Format: uuid
             */
            template_version_id: string;
            workflow: components["schemas"]["ApprovalWorkflowRead"] | null;
        };
        /** ApprovalWorkflowConfigure */
        ApprovalWorkflowConfigure: {
            approval_mode: components["schemas"]["ApprovalMode"];
            /**
             * Is Active
             * @default true
             */
            is_active: boolean;
            /**
             * Name
             * @default ������������ ������
             */
            name: string;
        };
        /** ApprovalWorkflowRead */
        ApprovalWorkflowRead: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Is Active */
            is_active: boolean;
            /** Name */
            name: string;
            /** Stages */
            stages?: components["schemas"]["ApprovalStageRead"][];
            /**
             * Template Version Id
             * Format: uuid
             */
            template_version_id: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** ApprovalWorkflowStageApply */
        ApprovalWorkflowStageApply: {
            /** Approver User Ids */
            approver_user_ids: string[];
            decision_rule: components["schemas"]["ApprovalDecisionRule"];
            /** Title */
            title: string;
        };
        /** Body_upload_comment_attachment_tickets__ticket_id__comments__comment_id__attachments_post */
        Body_upload_comment_attachment_tickets__ticket_id__comments__comment_id__attachments_post: {
            /** File */
            file: string;
        };
        /** Body_upload_field_attachment_tickets__ticket_id__fields__field_key__attachments_post */
        Body_upload_field_attachment_tickets__ticket_id__fields__field_key__attachments_post: {
            /** File */
            file: string;
        };
        /** Body_upload_ticket_attachment_tickets__ticket_id__attachments_post */
        Body_upload_ticket_attachment_tickets__ticket_id__attachments_post: {
            /** File */
            file: string;
        };
        /** BusinessCalendarCreate */
        BusinessCalendarCreate: {
            /** Business Hours */
            business_hours: components["schemas"]["BusinessHoursInput"][];
            /** Exceptions */
            exceptions?: components["schemas"]["CalendarExceptionInput"][];
            /**
             * Is Active
             * @default true
             */
            is_active: boolean;
            /** Name */
            name: string;
            /** Timezone */
            timezone: string;
        };
        /** BusinessCalendarRead */
        BusinessCalendarRead: {
            /** Business Hours */
            business_hours: components["schemas"]["BusinessHoursRead"][];
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Exceptions */
            exceptions: components["schemas"]["CalendarExceptionRead"][];
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Is Active */
            is_active: boolean;
            /** Name */
            name: string;
            /** Timezone */
            timezone: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** BusinessCalendarUpdate */
        BusinessCalendarUpdate: {
            /** Business Hours */
            business_hours?: components["schemas"]["BusinessHoursInput"][] | null;
            /** Exceptions */
            exceptions?: components["schemas"]["CalendarExceptionInput"][] | null;
            /** Is Active */
            is_active?: boolean | null;
            /** Name */
            name?: string | null;
            /** Timezone */
            timezone?: string | null;
        };
        /** BusinessHoursInput */
        BusinessHoursInput: {
            /**
             * End Time
             * Format: time
             */
            end_time: string;
            /**
             * Start Time
             * Format: time
             */
            start_time: string;
            /** Weekday */
            weekday: number;
        };
        /** BusinessHoursRead */
        BusinessHoursRead: {
            /**
             * Calendar Id
             * Format: uuid
             */
            calendar_id: string;
            /**
             * End Time
             * Format: time
             */
            end_time: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Start Time
             * Format: time
             */
            start_time: string;
            /** Weekday */
            weekday: number;
        };
        /** CalendarExceptionInput */
        CalendarExceptionInput: {
            /**
             * Date
             * Format: date
             */
            date: string;
            /** Description */
            description?: string | null;
            /** End Time */
            end_time?: string | null;
            /** Start Time */
            start_time?: string | null;
            type: components["schemas"]["CalendarExceptionType"];
        };
        /** CalendarExceptionRead */
        CalendarExceptionRead: {
            /**
             * Calendar Id
             * Format: uuid
             */
            calendar_id: string;
            /**
             * Date
             * Format: date
             */
            date: string;
            /** Description */
            description?: string | null;
            /** End Time */
            end_time?: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Start Time */
            start_time?: string | null;
            type: components["schemas"]["CalendarExceptionType"];
        };
        /**
         * CalendarExceptionType
         * @enum {string}
         */
        CalendarExceptionType: "holiday" | "working_day" | "custom_hours";
        /** CapabilityReplace */
        CapabilityReplace: {
            /** Capabilities */
            capabilities: string[];
        };
        /** CategoryCreate */
        CategoryCreate: {
            /** Description */
            description?: string | null;
            /**
             * Is Active
             * @default true
             */
            is_active: boolean;
            /** Parent Id */
            parent_id?: string | null;
            /**
             * Position
             * @default 0
             */
            position: number;
            /** Title */
            title: string;
        };
        /** CategoryRead */
        CategoryRead: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Deleted At */
            deleted_at: string | null;
            /** Description */
            description: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Is Active */
            is_active: boolean;
            /** Parent Id */
            parent_id: string | null;
            /** Position */
            position: number;
            /** Title */
            title: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** CategoryUpdate */
        CategoryUpdate: {
            /** Description */
            description?: string | null;
            /** Is Active */
            is_active?: boolean | null;
            /** Parent Id */
            parent_id?: string | null;
            /** Position */
            position?: number | null;
            /** Title */
            title?: string | null;
        };
        /** DictionaryCreate */
        DictionaryCreate: {
            /** Code */
            code: string;
            /** Description */
            description?: string | null;
            /**
             * Is Active
             * @default true
             */
            is_active: boolean;
            /** Title */
            title: string;
        };
        /** DictionaryItemCreate */
        DictionaryItemCreate: {
            /**
             * Is Active
             * @default true
             */
            is_active: boolean;
            /** Label */
            label: string;
            /** Metadata */
            metadata?: {
                [key: string]: unknown;
            };
            /**
             * Position
             * @default 0
             */
            position: number;
            /** Value */
            value: string;
        };
        /** DictionaryItemRead */
        DictionaryItemRead: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Dictionary Id
             * Format: uuid
             */
            dictionary_id: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Is Active */
            is_active: boolean;
            /** Label */
            label: string;
            /** Metadata */
            metadata: {
                [key: string]: unknown;
            };
            /** Position */
            position: number;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** Value */
            value: string;
        };
        /** DictionaryItemUpdate */
        DictionaryItemUpdate: {
            /** Is Active */
            is_active?: boolean | null;
            /** Label */
            label?: string | null;
            /** Metadata */
            metadata?: {
                [key: string]: unknown;
            } | null;
            /** Position */
            position?: number | null;
            /** Value */
            value?: string | null;
        };
        /** DictionaryRead */
        DictionaryRead: {
            /** Code */
            code: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Description */
            description: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Is Active */
            is_active: boolean;
            /** Items */
            items?: components["schemas"]["DictionaryItemRead"][];
            /** Title */
            title: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** DictionaryUpdate */
        DictionaryUpdate: {
            /** Code */
            code?: string | null;
            /** Description */
            description?: string | null;
            /** Is Active */
            is_active?: boolean | null;
            /** Title */
            title?: string | null;
        };
        /** EscalationRuleCreate */
        EscalationRuleCreate: {
            /**
             * Action Type
             * @enum {string}
             */
            action_type: "create_in_app_notification" | "email_notification_when_available";
            /**
             * Is Active
             * @default true
             */
            is_active: boolean;
            /**
             * Metric
             * @enum {string}
             */
            metric: "first_response" | "resolution";
            /**
             * Recipient Type
             * @enum {string}
             */
            recipient_type: "assignee" | "requester" | "service_desk_admin" | "specific_user";
            /** Recipient User Id */
            recipient_user_id?: string | null;
            /** Threshold Percent */
            threshold_percent: number;
        };
        /** EscalationRuleRead */
        EscalationRuleRead: {
            /**
             * Action Type
             * @enum {string}
             */
            action_type: "create_in_app_notification" | "email_notification_when_available";
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Is Active
             * @default true
             */
            is_active: boolean;
            /**
             * Metric
             * @enum {string}
             */
            metric: "first_response" | "resolution";
            /**
             * Recipient Type
             * @enum {string}
             */
            recipient_type: "assignee" | "requester" | "service_desk_admin" | "specific_user";
            /** Recipient User Id */
            recipient_user_id?: string | null;
            /**
             * Sla Policy Id
             * Format: uuid
             */
            sla_policy_id: string;
            /** Threshold Percent */
            threshold_percent: number;
        };
        /** EscalationRuleUpdate */
        EscalationRuleUpdate: {
            /** Action Type */
            action_type?: ("create_in_app_notification" | "email_notification_when_available") | null;
            /** Is Active */
            is_active?: boolean | null;
            /** Metric */
            metric?: ("first_response" | "resolution") | null;
            /** Recipient Type */
            recipient_type?: ("assignee" | "requester" | "service_desk_admin" | "specific_user") | null;
            /** Recipient User Id */
            recipient_user_id?: string | null;
            /** Threshold Percent */
            threshold_percent?: number | null;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** NotificationRead */
        NotificationRead: {
            /** Body */
            body: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Event Type */
            event_type: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Is Read */
            is_read: boolean;
            /** Read At */
            read_at: string | null;
            /**
             * Recipient User Id
             * Format: uuid
             */
            recipient_user_id: string;
            /** Ticket Id */
            ticket_id: string | null;
            /** Title */
            title: string;
        };
        /** PublishedTemplateRead */
        PublishedTemplateRead: {
            /** Fields */
            fields?: components["schemas"]["TemplateFieldPreviewRead"][];
            /**
             * Service Id
             * Format: uuid
             */
            service_id: string;
            template_version: components["schemas"]["TemplateVersionRead"];
        };
        /** ReadAllResult */
        ReadAllResult: {
            /** Marked Read */
            marked_read: number;
        };
        /** RoutingAction */
        RoutingAction: {
            priority?: components["schemas"]["ServiceDeskPriority"] | null;
            /**
             * Type
             * @enum {string}
             */
            type: "assign_user" | "set_priority";
            /** User Id */
            user_id?: string | null;
        };
        /** RoutingAssigneeRead */
        RoutingAssigneeRead: {
            /** Display Name */
            display_name: string;
            /** Email */
            email: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
        };
        /**
         * RoutingCatalogOptionsRead
         * @description Catalog entities available as routing rule conditions.
         */
        RoutingCatalogOptionsRead: {
            /** Categories */
            categories: components["schemas"]["CategoryRead"][];
            /** Services */
            services: components["schemas"]["ServiceRead"][];
        };
        /** RoutingCondition */
        RoutingCondition: {
            /**
             * Field
             * @enum {string}
             */
            field: "service_id" | "category_id" | "priority" | "field_value";
            /** Field Key */
            field_key?: string | null;
            /**
             * Operator
             * @constant
             */
            operator: "equals";
            /** Value */
            value: unknown;
        };
        /** RoutingRuleCreate */
        RoutingRuleCreate: {
            action: components["schemas"]["RoutingAction"];
            /** Conditions */
            conditions?: components["schemas"]["RoutingCondition"][];
            /**
             * Is Active
             * @default true
             */
            is_active: boolean;
            /** Name */
            name: string;
            /**
             * Priority
             * @default 100
             */
            priority: number;
        };
        /** RoutingRuleRead */
        RoutingRuleRead: {
            action: components["schemas"]["RoutingAction"];
            /** Conditions */
            conditions?: components["schemas"]["RoutingCondition"][];
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Is Active */
            is_active: boolean;
            /** Name */
            name: string;
            /** Priority */
            priority: number;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** RoutingRuleUpdate */
        RoutingRuleUpdate: {
            action?: components["schemas"]["RoutingAction"] | null;
            /** Conditions */
            conditions?: components["schemas"]["RoutingCondition"][] | null;
            /** Is Active */
            is_active?: boolean | null;
            /** Name */
            name?: string | null;
            /** Priority */
            priority?: number | null;
        };
        /** RoutingRulesReorder */
        RoutingRulesReorder: {
            /** Rule Ids */
            rule_ids: string[];
        };
        /** ServiceApprovalWorkflowConfigurationRead */
        ServiceApprovalWorkflowConfigurationRead: {
            approval_mode: components["schemas"]["ApprovalMode"];
            template_version: components["schemas"]["TemplateVersionRead"];
            /**
             * Template Version Id
             * Format: uuid
             */
            template_version_id: string;
            workflow: components["schemas"]["ApprovalWorkflowRead"] | null;
        };
        /** ServiceCreate */
        ServiceCreate: {
            /**
             * Category Id
             * Format: uuid
             */
            category_id: string;
            /** Default Assignee User Id */
            default_assignee_user_id?: string | null;
            /** Description */
            description?: string | null;
            /**
             * Is Active
             * @default true
             */
            is_active: boolean;
            /**
             * Position
             * @default 0
             */
            position: number;
            /** Short Description */
            short_description?: string | null;
            /** Title */
            title: string;
        };
        /**
         * ServiceDeskAccessType
         * @enum {string}
         */
        ServiceDeskAccessType: "service_desk_manager" | "service_desk_admin";
        /**
         * ServiceDeskApprovalStatus
         * @enum {string}
         */
        ServiceDeskApprovalStatus: "pending" | "approved" | "rejected" | "skipped";
        /**
         * ServiceDeskAttachmentOwnerType
         * @enum {string}
         */
        ServiceDeskAttachmentOwnerType: "service_desk_ticket" | "service_desk_comment" | "service_desk_field_value";
        /** ServiceDeskAttachmentRead */
        ServiceDeskAttachmentRead: {
            /** Checksum */
            checksum: string | null;
            /** Content Type */
            content_type: string | null;
            /** Content Type Detected */
            content_type_detected: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Field Key */
            field_key: string | null;
            /** File Name */
            file_name: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Owner Id
             * Format: uuid
             */
            owner_id: string;
            owner_type: components["schemas"]["ServiceDeskAttachmentOwnerType"];
            /** Size Bytes */
            size_bytes: number;
            status: components["schemas"]["ServiceDeskAttachmentStatus"];
            /**
             * Ticket Id
             * Format: uuid
             */
            ticket_id: string;
            /**
             * Uploaded By User Id
             * Format: uuid
             */
            uploaded_by_user_id: string;
        };
        /**
         * ServiceDeskAttachmentStatus
         * @enum {string}
         */
        ServiceDeskAttachmentStatus: "pending" | "quarantined" | "available" | "rejected" | "deleted";
        /** ServiceDeskCapabilitiesRead */
        ServiceDeskCapabilitiesRead: {
            /** Capabilities */
            capabilities: string[];
        };
        /**
         * ServiceDeskCommentVisibility
         * @enum {string}
         */
        ServiceDeskCommentVisibility: "public" | "internal";
        /** ServiceDeskCounters */
        ServiceDeskCounters: {
            /** Assigned To Me */
            assigned_to_me: number;
            /** Awaiting My Response */
            awaiting_my_response: number;
            /** Sla Breaches */
            sla_breaches: number | null;
            /** Waiting My Approval */
            waiting_my_approval: number;
        };
        /**
         * ServiceDeskPriority
         * @enum {string}
         */
        ServiceDeskPriority: "low" | "medium" | "high" | "critical";
        /**
         * ServiceDeskTicketStatus
         * @enum {string}
         */
        ServiceDeskTicketStatus: "draft" | "submitted" | "pending_approval" | "approved" | "rejected" | "assigned" | "in_progress" | "waiting_requester" | "waiting_external" | "resolved" | "closed" | "cancelled";
        /** ServiceDeskUserOptionRead */
        ServiceDeskUserOptionRead: {
            /** Department */
            department: string | null;
            /** Display Name */
            display_name: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Position */
            position: string | null;
        };
        /** ServiceDeskUserRead */
        ServiceDeskUserRead: {
            access_type: components["schemas"]["ServiceDeskAccessType"];
            /** Capabilities */
            capabilities: string[];
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Department */
            department: string | null;
            /** Display Name */
            display_name: string;
            /** Email */
            email: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Identity User Id */
            identity_user_id: string;
            /** Is Active */
            is_active: boolean;
            /** Position */
            position: string | null;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** ServiceRead */
        ServiceRead: {
            category?: components["schemas"]["CategoryRead"] | null;
            /**
             * Category Id
             * Format: uuid
             */
            category_id: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Default Assignee User Id */
            default_assignee_user_id: string | null;
            /** Deleted At */
            deleted_at: string | null;
            /** Description */
            description: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Is Active */
            is_active: boolean;
            /** Position */
            position: number;
            /**
             * Request Form Available
             * @default false
             */
            request_form_available: boolean;
            /** Short Description */
            short_description: string | null;
            /** Title */
            title: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** ServiceUpdate */
        ServiceUpdate: {
            /** Category Id */
            category_id?: string | null;
            /** Default Assignee User Id */
            default_assignee_user_id?: string | null;
            /** Description */
            description?: string | null;
            /** Is Active */
            is_active?: boolean | null;
            /** Position */
            position?: number | null;
            /** Short Description */
            short_description?: string | null;
            /** Title */
            title?: string | null;
        };
        /** SlaBindingCondition */
        SlaBindingCondition: {
            /**
             * Field
             * @enum {string}
             */
            field: "template_version_id" | "service_id" | "category_id" | "priority" | "field_value";
            /** Field Key */
            field_key?: string | null;
            /** Value */
            value: unknown;
        };
        /** SlaBindingCreate */
        SlaBindingCreate: {
            /** Conditions */
            conditions: components["schemas"]["SlaBindingCondition"][];
            /**
             * Is Active
             * @default true
             */
            is_active: boolean;
            /** Name */
            name: string;
            /**
             * Policy Id
             * Format: uuid
             */
            policy_id: string;
            /**
             * Priority
             * @default 100
             */
            priority: number;
        };
        /** SlaBindingRead */
        SlaBindingRead: {
            /** Conditions */
            conditions: components["schemas"]["SlaBindingCondition"][];
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Is Active
             * @default true
             */
            is_active: boolean;
            /** Name */
            name: string;
            /**
             * Policy Id
             * Format: uuid
             */
            policy_id: string;
            /**
             * Priority
             * @default 100
             */
            priority: number;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** SlaBindingUpdate */
        SlaBindingUpdate: {
            /** Conditions */
            conditions?: components["schemas"]["SlaBindingCondition"][] | null;
            /** Is Active */
            is_active?: boolean | null;
            /** Name */
            name?: string | null;
            /** Policy Id */
            policy_id?: string | null;
            /** Priority */
            priority?: number | null;
        };
        /** SlaPolicyCreate */
        SlaPolicyCreate: {
            /**
             * Business Calendar Id
             * Format: uuid
             */
            business_calendar_id: string;
            /** Description */
            description?: string | null;
            /** First Response Minutes */
            first_response_minutes: number;
            /**
             * Is Active
             * @default true
             */
            is_active: boolean;
            /** Name */
            name: string;
            /** Pause Statuses */
            pause_statuses?: ("waiting_requester" | "waiting_external")[];
            /** Resolution Minutes */
            resolution_minutes: number;
        };
        /** SlaPolicyRead */
        SlaPolicyRead: {
            /**
             * Business Calendar Id
             * Format: uuid
             */
            business_calendar_id: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Deleted At */
            deleted_at: string | null;
            /** Description */
            description?: string | null;
            /** First Response Minutes */
            first_response_minutes: number;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Is Active
             * @default true
             */
            is_active: boolean;
            /** Name */
            name: string;
            /** Pause Statuses */
            pause_statuses?: ("waiting_requester" | "waiting_external")[];
            /** Resolution Minutes */
            resolution_minutes: number;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** SlaPolicyUpdate */
        SlaPolicyUpdate: {
            /** Business Calendar Id */
            business_calendar_id?: string | null;
            /** Description */
            description?: string | null;
            /** First Response Minutes */
            first_response_minutes?: number | null;
            /** Is Active */
            is_active?: boolean | null;
            /** Name */
            name?: string | null;
            /** Pause Statuses */
            pause_statuses?: ("waiting_requester" | "waiting_external")[] | null;
            /** Resolution Minutes */
            resolution_minutes?: number | null;
        };
        /** SlaRecipientRead */
        SlaRecipientRead: {
            /** Display Name */
            display_name: string;
            /** Email */
            email: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
        };
        /** TemplateFieldCreate */
        TemplateFieldCreate: {
            /** Dictionary Code */
            dictionary_code?: string | null;
            field_type: components["schemas"]["TemplateFieldType"];
            /** Help Text */
            help_text?: string | null;
            /**
             * Is Required
             * @default false
             */
            is_required: boolean;
            /** Key */
            key: string;
            /** Label */
            label: string;
            /** Options */
            options?: {
                [key: string]: unknown;
            }[] | null;
            /** Placeholder */
            placeholder?: string | null;
            /**
             * Position
             * @default 0
             */
            position: number;
            /** Required Rules */
            required_rules?: {
                [key: string]: unknown;
            } | {
                [key: string]: unknown;
            }[] | null;
            /** Validation */
            validation?: {
                [key: string]: unknown;
            } | null;
            /** Visibility Rules */
            visibility_rules?: {
                [key: string]: unknown;
            } | {
                [key: string]: unknown;
            }[] | null;
        };
        /** TemplateFieldPreviewRead */
        TemplateFieldPreviewRead: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Dictionary Code */
            dictionary_code: string | null;
            /** Effective Options */
            effective_options?: {
                [key: string]: unknown;
            }[];
            field_type: components["schemas"]["TemplateFieldType"];
            /** Help Text */
            help_text: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Is Required */
            is_required: boolean;
            /** Key */
            key: string;
            /** Label */
            label: string;
            /** Options */
            options: {
                [key: string]: unknown;
            }[] | null;
            /** Placeholder */
            placeholder: string | null;
            /** Position */
            position: number;
            /** Required Rules */
            required_rules: {
                [key: string]: unknown;
            } | {
                [key: string]: unknown;
            }[] | null;
            /**
             * Template Version Id
             * Format: uuid
             */
            template_version_id: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** Validation */
            validation: {
                [key: string]: unknown;
            } | null;
            /** Visibility Rules */
            visibility_rules: {
                [key: string]: unknown;
            } | {
                [key: string]: unknown;
            }[] | null;
        };
        /** TemplateFieldRead */
        TemplateFieldRead: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Dictionary Code */
            dictionary_code: string | null;
            field_type: components["schemas"]["TemplateFieldType"];
            /** Help Text */
            help_text: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Is Required */
            is_required: boolean;
            /** Key */
            key: string;
            /** Label */
            label: string;
            /** Options */
            options: {
                [key: string]: unknown;
            }[] | null;
            /** Placeholder */
            placeholder: string | null;
            /** Position */
            position: number;
            /** Required Rules */
            required_rules: {
                [key: string]: unknown;
            } | {
                [key: string]: unknown;
            }[] | null;
            /**
             * Template Version Id
             * Format: uuid
             */
            template_version_id: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** Validation */
            validation: {
                [key: string]: unknown;
            } | null;
            /** Visibility Rules */
            visibility_rules: {
                [key: string]: unknown;
            } | {
                [key: string]: unknown;
            }[] | null;
        };
        /**
         * TemplateFieldType
         * @enum {string}
         */
        TemplateFieldType: "text" | "textarea" | "rich_text" | "select" | "multiselect" | "date" | "time" | "datetime" | "email" | "number" | "checkbox" | "file" | "user";
        /** TemplateFieldUpdate */
        TemplateFieldUpdate: {
            /** Dictionary Code */
            dictionary_code?: string | null;
            field_type?: components["schemas"]["TemplateFieldType"] | null;
            /** Help Text */
            help_text?: string | null;
            /** Is Required */
            is_required?: boolean | null;
            /** Key */
            key?: string | null;
            /** Label */
            label?: string | null;
            /** Options */
            options?: {
                [key: string]: unknown;
            }[] | null;
            /** Placeholder */
            placeholder?: string | null;
            /** Position */
            position?: number | null;
            /** Required Rules */
            required_rules?: {
                [key: string]: unknown;
            } | {
                [key: string]: unknown;
            }[] | null;
            /** Validation */
            validation?: {
                [key: string]: unknown;
            } | null;
            /** Visibility Rules */
            visibility_rules?: {
                [key: string]: unknown;
            } | {
                [key: string]: unknown;
            }[] | null;
        };
        /** TemplateFieldsReorder */
        TemplateFieldsReorder: {
            /** Field Ids */
            field_ids: string[];
        };
        /** TemplatePreviewRead */
        TemplatePreviewRead: {
            /** Fields */
            fields?: components["schemas"]["TemplateFieldPreviewRead"][];
            template_version: components["schemas"]["TemplateVersionRead"];
        };
        /** TemplateValidationErrorItem */
        TemplateValidationErrorItem: {
            /** Field Key */
            field_key: string;
            /** Message */
            message: string;
        };
        /** TemplateValidationRequest */
        TemplateValidationRequest: {
            /** Data */
            data?: {
                [key: string]: unknown;
            };
        };
        /** TemplateValidationResult */
        TemplateValidationResult: {
            /** Errors */
            errors: components["schemas"]["TemplateValidationErrorItem"][];
            /** Is Valid */
            is_valid: boolean;
            /** Normalized Data */
            normalized_data: {
                [key: string]: unknown;
            };
            /** Required Fields */
            required_fields: string[];
            /** Visible Fields */
            visible_fields: string[];
        };
        /** TemplateVersionCreate */
        TemplateVersionCreate: {
            /** Default Assignee User Id */
            default_assignee_user_id?: string | null;
            /** System Settings */
            system_settings?: {
                [key: string]: unknown;
            };
        };
        /** TemplateVersionRead */
        TemplateVersionRead: {
            approval_mode: components["schemas"]["ApprovalMode"];
            /** Archived At */
            archived_at: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Created By */
            created_by: string | null;
            /** Default Assignee User Id */
            default_assignee_user_id: string | null;
            /** Fields */
            fields?: components["schemas"]["TemplateFieldRead"][];
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Published At */
            published_at: string | null;
            /** Published By */
            published_by: string | null;
            /**
             * Service Id
             * Format: uuid
             */
            service_id: string;
            status: components["schemas"]["TemplateVersionStatus"];
            /** System Settings */
            system_settings: {
                [key: string]: unknown;
            };
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** Version */
            version: number;
        };
        /**
         * TemplateVersionStatus
         * @enum {string}
         */
        TemplateVersionStatus: "draft" | "published" | "archived";
        /** TemplateVersionUpdate */
        TemplateVersionUpdate: {
            /** Default Assignee User Id */
            default_assignee_user_id?: string | null;
            /** System Settings */
            system_settings?: {
                [key: string]: unknown;
            } | null;
        };
        /** TicketAction */
        TicketAction: Record<string, never>;
        /** TicketApprovalDecision */
        TicketApprovalDecision: {
            /** Comment */
            comment?: string | null;
        };
        /** TicketApprovalRead */
        TicketApprovalRead: {
            /** Approver Display Name */
            approver_display_name: string;
            /**
             * Approver User Id
             * Format: uuid
             */
            approver_user_id: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Decided At */
            decided_at: string | null;
            /** Decision Comment */
            decision_comment: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            status: components["schemas"]["ServiceDeskApprovalStatus"];
            /**
             * Ticket Approval Stage Id
             * Format: uuid
             */
            ticket_approval_stage_id: string;
        };
        /** TicketApprovalRejection */
        TicketApprovalRejection: {
            /** Comment */
            comment: string;
        };
        /** TicketApprovalStageRead */
        TicketApprovalStageRead: {
            /** Approvals */
            approvals?: components["schemas"]["TicketApprovalRead"][];
            /** Completed At */
            completed_at: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            decision_rule: components["schemas"]["ApprovalDecisionRule"];
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Position */
            position: number;
            /** Started At */
            started_at: string | null;
            status: components["schemas"]["ServiceDeskApprovalStatus"];
            /**
             * Ticket Id
             * Format: uuid
             */
            ticket_id: string;
            /** Title */
            title: string;
        };
        /** TicketAssignmentAction */
        TicketAssignmentAction: {
            /**
             * Assignee User Id
             * Format: uuid
             */
            assignee_user_id: string;
        };
        /** TicketCategorySummary */
        TicketCategorySummary: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Title */
            title: string;
        };
        /** TicketCommentAction */
        TicketCommentAction: {
            /** Comment */
            comment: string;
        };
        /** TicketCommentCreate */
        TicketCommentCreate: {
            /** Body */
            body: string;
            /** @default public */
            visibility: components["schemas"]["ServiceDeskCommentVisibility"];
        };
        /** TicketCommentRead */
        TicketCommentRead: {
            author: components["schemas"]["TicketUserSummary"];
            /**
             * Author User Id
             * Format: uuid
             */
            author_user_id: string;
            /** Body */
            body: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Ticket Id
             * Format: uuid
             */
            ticket_id: string;
            /** Updated At */
            updated_at: string | null;
            visibility: components["schemas"]["ServiceDeskCommentVisibility"];
        };
        /** TicketCommentSummary */
        TicketCommentSummary: {
            author: components["schemas"]["TicketUserSummary"];
            /**
             * Author User Id
             * Format: uuid
             */
            author_user_id: string;
            /** Body */
            body: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Ticket Id
             * Format: uuid
             */
            ticket_id: string;
            /** Updated At */
            updated_at: string | null;
            /**
             * Visibility
             * @enum {string}
             */
            visibility: "public" | "internal";
        };
        /** TicketCommentUpdate */
        TicketCommentUpdate: {
            /** Body */
            body: string;
        };
        /** TicketDraftCreate */
        TicketDraftCreate: {
            /** Description */
            description?: string | null;
            /** Field Values */
            field_values?: {
                [key: string]: unknown;
            };
            /** @default medium */
            priority: components["schemas"]["ServiceDeskPriority"];
            /**
             * Service Id
             * Format: uuid
             */
            service_id: string;
            /** Template Version Id */
            template_version_id?: string | null;
            /** Title */
            title: string;
        };
        /** TicketDraftUpdate */
        TicketDraftUpdate: {
            /** Description */
            description?: string | null;
            /** Field Values */
            field_values?: {
                [key: string]: unknown;
            } | null;
            priority?: components["schemas"]["ServiceDeskPriority"] | null;
            /** Title */
            title?: string | null;
        };
        /** TicketFieldSnapshotRead */
        TicketFieldSnapshotRead: {
            /** Display Value */
            display_value: string;
            /** Key */
            key: string;
            /** Label */
            label: string;
            /** Raw Value */
            raw_value: unknown;
            /** Type */
            type: string;
        };
        /** TicketHistoryRead */
        TicketHistoryRead: {
            /** Actor User Id */
            actor_user_id: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Event Type */
            event_type: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Message */
            message: string;
            /** Payload */
            payload: {
                [key: string]: unknown;
            };
            /**
             * Ticket Id
             * Format: uuid
             */
            ticket_id: string;
        };
        /** TicketPriorityUpdate */
        TicketPriorityUpdate: {
            priority: components["schemas"]["ServiceDeskPriority"];
            /** Reason */
            reason: string;
        };
        /** TicketRead */
        TicketRead: {
            /** Allowed Actions */
            allowed_actions?: ("approve" | "reject" | "assign" | "reassign" | "start" | "request_clarification" | "wait_external" | "resume" | "resolve" | "close" | "cancel" | "change_priority")[];
            /** Approval Stages */
            approval_stages?: components["schemas"]["TicketApprovalStageRead"][];
            /** Approval Started At */
            approval_started_at: string | null;
            /** Approved At */
            approved_at: string | null;
            /** Assigned At */
            assigned_at: string | null;
            assignee: components["schemas"]["TicketUserSummary"] | null;
            /** Assignee User Id */
            assignee_user_id: string | null;
            /** Cancellation Reason */
            cancellation_reason: string | null;
            /** Cancelled At */
            cancelled_at: string | null;
            /** Closed At */
            closed_at: string | null;
            /** Comments */
            comments?: components["schemas"]["TicketCommentSummary"][];
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Deleted At */
            deleted_at: string | null;
            /** Description */
            description: string | null;
            /** Field Snapshot */
            field_snapshot?: components["schemas"]["TicketFieldSnapshotRead"][];
            /** Field Values */
            field_values: {
                [key: string]: unknown;
            };
            /** First Response At */
            first_response_at: string | null;
            /** First Response Due At */
            first_response_due_at: string | null;
            /** History */
            history?: components["schemas"]["TicketHistoryRead"][];
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Is Resolution Breached */
            is_resolution_breached: boolean;
            /** Is Response Breached */
            is_response_breached: boolean;
            /** Number */
            number: string | null;
            /** Paused Seconds */
            paused_seconds: number;
            priority: components["schemas"]["ServiceDeskPriority"];
            /** Rejected At */
            rejected_at: string | null;
            requester: components["schemas"]["TicketUserSummary"];
            /**
             * Requester User Id
             * Format: uuid
             */
            requester_user_id: string;
            /** Resolution Breached At */
            resolution_breached_at: string | null;
            /** Resolution Due At */
            resolution_due_at: string | null;
            /** Resolution Summary */
            resolution_summary: string | null;
            /** Resolved At */
            resolved_at: string | null;
            /** Response Breached At */
            response_breached_at: string | null;
            /** Routing Snapshot */
            routing_snapshot: {
                [key: string]: unknown;
            } | null;
            service: components["schemas"]["TicketServiceSummary"];
            /**
             * Service Id
             * Format: uuid
             */
            service_id: string;
            /** Sla Policy Id */
            sla_policy_id: string | null;
            /** Sla Snapshot */
            sla_snapshot: {
                [key: string]: unknown;
            } | null;
            status: components["schemas"]["ServiceDeskTicketStatus"];
            /** Submitted At */
            submitted_at: string | null;
            /**
             * Template Version Id
             * Format: uuid
             */
            template_version_id: string;
            /** Title */
            title: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** Work Started At */
            work_started_at: string | null;
        };
        /** TicketReasonAction */
        TicketReasonAction: {
            /** Reason */
            reason: string;
        };
        /** TicketResolveAction */
        TicketResolveAction: {
            /** Comment */
            comment?: string | null;
            /** Resolution Summary */
            resolution_summary: string;
        };
        /** TicketServiceSummary */
        TicketServiceSummary: {
            category: components["schemas"]["TicketCategorySummary"];
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Title */
            title: string;
        };
        /** TicketUserSummary */
        TicketUserSummary: {
            /** Display Name */
            display_name: string;
            /** Email */
            email: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
        };
        /** UnreadCount */
        UnreadCount: {
            /** Count */
            count: number;
        };
        /** ValidationError */
        ValidationError: {
            /** Context */
            ctx?: Record<string, never>;
            /** Input */
            input?: unknown;
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
        };
        /** WorkbenchCounters */
        WorkbenchCounters: {
            /** Assigned To Me */
            assigned_to_me: number;
            /** In Progress */
            in_progress: number;
            /** Resolved */
            resolved: number;
            /** Sla Breached */
            sla_breached: number | null;
            /** Waiting Approval */
            waiting_approval: number;
            /** Waiting External */
            waiting_external: number;
            /** Waiting Requester */
            waiting_requester: number;
        };
        /** WorkbenchEntitySummary */
        WorkbenchEntitySummary: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Title */
            title: string;
        };
        /**
         * WorkbenchQuickView
         * @enum {string}
         */
        WorkbenchQuickView: "waiting_approval" | "assigned_to_me" | "in_progress" | "waiting_requester" | "waiting_external" | "resolved" | "sla_breached";
        /**
         * WorkbenchSlaState
         * @enum {string}
         */
        WorkbenchSlaState: "no_sla" | "on_track" | "paused" | "warning" | "breached";
        /** WorkbenchSlaSummary */
        WorkbenchSlaSummary: {
            /** Due At */
            due_at?: string | null;
            /** Metric */
            metric?: string | null;
            state: components["schemas"]["WorkbenchSlaState"];
        };
        /** WorkbenchTicketPage */
        WorkbenchTicketPage: {
            /** Items */
            items: components["schemas"]["WorkbenchTicketRow"][];
            /** Page */
            page: number;
            /** Page Size */
            page_size: number;
            /** Pages */
            pages: number;
            /** Total */
            total: number;
        };
        /** WorkbenchTicketRow */
        WorkbenchTicketRow: {
            /** Active Approval Id */
            active_approval_id?: string | null;
            /** Allowed Actions */
            allowed_actions?: string[];
            assignee: components["schemas"]["WorkbenchUserSummary"] | null;
            category: components["schemas"]["WorkbenchEntitySummary"];
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Number */
            number: string | null;
            priority: components["schemas"]["ServiceDeskPriority"];
            requester: components["schemas"]["WorkbenchUserSummary"];
            service: components["schemas"]["WorkbenchEntitySummary"];
            sla: components["schemas"]["WorkbenchSlaSummary"];
            status: components["schemas"]["ServiceDeskTicketStatus"];
            /**
             * Ticket Id
             * Format: uuid
             */
            ticket_id: string;
            /** Title */
            title: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** WorkbenchUserOption */
        WorkbenchUserOption: {
            /** Display Name */
            display_name: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
        };
        /** WorkbenchUserSummary */
        WorkbenchUserSummary: {
            /** Display Name */
            display_name: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    get_access_status_access_status_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    users_admin_access_users_get: {
        parameters: {
            query?: {
                q?: string | null;
                access_type?: components["schemas"]["ServiceDeskAccessType"] | null;
                is_active?: boolean | null;
                page?: number;
                page_size?: number;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AccessUserPage"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_admin_access_users_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AccessUserCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceDeskUserRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_admin_access_users__user_id__patch: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                user_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AccessUserUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceDeskUserRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    activate_admin_access_users__user_id__activate_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                user_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceDeskUserRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    capabilities_admin_access_users__user_id__capabilities_put: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                user_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CapabilityReplace"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceDeskUserRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    deactivate_admin_access_users__user_id__deactivate_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                user_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceDeskUserRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_stage_approver_admin_approval_stage_approvers__approver_id__delete: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                approver_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_approval_stage_admin_approval_stages__stage_id__delete: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                stage_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_approval_stage_admin_approval_stages__stage_id__patch: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                stage_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ApprovalStageUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApprovalWorkflowConfigurationRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    add_stage_approver_admin_approval_stages__stage_id__approvers_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                stage_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ApprovalStageApproverCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApprovalWorkflowConfigurationRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reorder_approval_stages_admin_approval_workflows__workflow_id__reorder_stages_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                workflow_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ApprovalStagesReorder"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApprovalWorkflowConfigurationRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_approval_stage_admin_approval_workflows__workflow_id__stages_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                workflow_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ApprovalStageCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApprovalWorkflowConfigurationRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    admin_list_categories_admin_categories_get: {
        parameters: {
            query?: {
                q?: string | null;
                active?: boolean | null;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CategoryRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    admin_create_category_admin_categories_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CategoryCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CategoryRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    admin_update_category_admin_categories__category_id__patch: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                category_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CategoryUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CategoryRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    admin_deactivate_category_admin_categories__category_id__deactivate_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                category_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CategoryRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    admin_restore_category_admin_categories__category_id__restore_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                category_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CategoryRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_dictionaries_admin_dictionaries_get: {
        parameters: {
            query?: {
                active?: boolean | null;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DictionaryRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_dictionary_admin_dictionaries_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DictionaryCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DictionaryRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_dictionary_admin_dictionaries__dictionary_id__patch: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                dictionary_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DictionaryUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DictionaryRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_dictionary_item_admin_dictionaries__dictionary_id__items_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                dictionary_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DictionaryItemCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DictionaryItemRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_dictionary_item_admin_dictionary_items__item_id__patch: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                item_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DictionaryItemUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DictionaryItemRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_routing_rules_admin_routing_rules_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RoutingRuleRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_routing_rule_admin_routing_rules_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RoutingRuleCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RoutingRuleRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_routing_candidates_admin_routing_rules_candidates_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RoutingAssigneeRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_routing_catalog_options_admin_routing_rules_catalog_options_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RoutingCatalogOptionsRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reorder_routing_rules_admin_routing_rules_reorder_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RoutingRulesReorder"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RoutingRuleRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_routing_rule_admin_routing_rules__rule_id__delete: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                rule_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_routing_rule_admin_routing_rules__rule_id__patch: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                rule_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RoutingRuleUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RoutingRuleRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    admin_list_services_admin_services_get: {
        parameters: {
            query?: {
                q?: string | null;
                category_id?: string | null;
                active?: boolean | null;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    admin_create_service_admin_services_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ServiceCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    admin_update_service_admin_services__service_id__patch: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                service_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ServiceUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_service_approval_workflow_admin_services__service_id__approval_workflow_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                service_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceApprovalWorkflowConfigurationRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    apply_service_approval_workflow_admin_services__service_id__approval_workflow_apply_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                service_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ApprovalWorkflowApply"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceApprovalWorkflowConfigurationRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    admin_deactivate_service_admin_services__service_id__deactivate_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                service_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    admin_restore_service_admin_services__service_id__restore_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                service_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_template_versions_admin_services__service_id__versions_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                service_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TemplateVersionRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_template_version_admin_services__service_id__versions_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                service_id: string;
            };
            cookie?: never;
        };
        requestBody?: {
            content: {
                "application/json": components["schemas"]["TemplateVersionCreate"] | null;
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TemplateVersionRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_sla_bindings_admin_sla_bindings_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SlaBindingRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_sla_binding_admin_sla_bindings_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SlaBindingCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SlaBindingRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_sla_binding_admin_sla_bindings__binding_id__patch: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                binding_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SlaBindingUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SlaBindingRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_business_calendars_admin_sla_calendars_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BusinessCalendarRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_business_calendar_admin_sla_calendars_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BusinessCalendarCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BusinessCalendarRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_business_calendar_admin_sla_calendars__calendar_id__patch: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                calendar_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BusinessCalendarUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BusinessCalendarRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_escalations_admin_sla_escalations_get: {
        parameters: {
            query?: {
                policy_id?: string | null;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EscalationRuleRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_escalation_admin_sla_escalations__rule_id__delete: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                rule_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_escalation_admin_sla_escalations__rule_id__patch: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                rule_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EscalationRuleUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EscalationRuleRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_sla_policies_admin_sla_policies_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SlaPolicyRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_sla_policy_admin_sla_policies_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SlaPolicyCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SlaPolicyRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_sla_policy_admin_sla_policies__policy_id__patch: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                policy_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SlaPolicyUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SlaPolicyRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_escalation_admin_sla_policies__policy_id__escalations_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                policy_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EscalationRuleCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EscalationRuleRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_sla_recipients_admin_sla_recipients_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SlaRecipientRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    approvals_admin_stats_approvals_get: {
        parameters: {
            query?: {
                date_from?: string | null;
                date_to?: string | null;
                category_id?: string | null;
                service_id?: string | null;
                assignee_user_id?: string | null;
                priority?: components["schemas"]["ServiceDeskPriority"] | null;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    assignees_admin_stats_assignees_get: {
        parameters: {
            query?: {
                date_from?: string | null;
                date_to?: string | null;
                category_id?: string | null;
                service_id?: string | null;
                assignee_user_id?: string | null;
                priority?: components["schemas"]["ServiceDeskPriority"] | null;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    backlog_admin_stats_backlog_aging_get: {
        parameters: {
            query?: {
                date_from?: string | null;
                date_to?: string | null;
                category_id?: string | null;
                service_id?: string | null;
                assignee_user_id?: string | null;
                priority?: components["schemas"]["ServiceDeskPriority"] | null;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    categories_admin_stats_categories_get: {
        parameters: {
            query?: {
                date_from?: string | null;
                date_to?: string | null;
                category_id?: string | null;
                service_id?: string | null;
                assignee_user_id?: string | null;
                priority?: components["schemas"]["ServiceDeskPriority"] | null;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    services_admin_stats_services_get: {
        parameters: {
            query?: {
                date_from?: string | null;
                date_to?: string | null;
                category_id?: string | null;
                service_id?: string | null;
                assignee_user_id?: string | null;
                priority?: components["schemas"]["ServiceDeskPriority"] | null;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    sla_admin_stats_sla_get: {
        parameters: {
            query?: {
                date_from?: string | null;
                date_to?: string | null;
                category_id?: string | null;
                service_id?: string | null;
                assignee_user_id?: string | null;
                priority?: components["schemas"]["ServiceDeskPriority"] | null;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    statuses_admin_stats_statuses_get: {
        parameters: {
            query?: {
                date_from?: string | null;
                date_to?: string | null;
                category_id?: string | null;
                service_id?: string | null;
                assignee_user_id?: string | null;
                priority?: components["schemas"]["ServiceDeskPriority"] | null;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    summary_admin_stats_summary_get: {
        parameters: {
            query?: {
                date_from?: string | null;
                date_to?: string | null;
                category_id?: string | null;
                service_id?: string | null;
                assignee_user_id?: string | null;
                priority?: components["schemas"]["ServiceDeskPriority"] | null;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    times_admin_stats_times_get: {
        parameters: {
            query?: {
                date_from?: string | null;
                date_to?: string | null;
                category_id?: string | null;
                service_id?: string | null;
                assignee_user_id?: string | null;
                priority?: components["schemas"]["ServiceDeskPriority"] | null;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_template_field_admin_template_fields__field_id__delete: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                field_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_template_field_admin_template_fields__field_id__patch: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                field_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TemplateFieldUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TemplateFieldRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_template_version_admin_template_versions__version_id__get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                version_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TemplateVersionRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_template_version_admin_template_versions__version_id__patch: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                version_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TemplateVersionUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TemplateVersionRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_approval_workflow_admin_template_versions__version_id__approval_workflow_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                version_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApprovalWorkflowConfigurationRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    configure_approval_workflow_admin_template_versions__version_id__approval_workflow_put: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                version_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ApprovalWorkflowConfigure"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApprovalWorkflowConfigurationRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_template_field_admin_template_versions__version_id__fields_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                version_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TemplateFieldCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TemplateFieldRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    preview_template_version_admin_template_versions__version_id__preview_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                version_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TemplatePreviewRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    publish_template_version_admin_template_versions__version_id__publish_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                version_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TemplateVersionRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reorder_template_fields_admin_template_versions__version_id__reorder_fields_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                version_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TemplateFieldsReorder"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TemplateFieldRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    validate_template_payload_admin_template_versions__version_id__validate_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                version_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TemplateValidationRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TemplateValidationResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    api_health_api_health_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: string;
                    };
                };
            };
        };
    };
    list_categories_categories_get: {
        parameters: {
            query?: {
                q?: string | null;
                active?: boolean | null;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CategoryRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    live_health_live_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: string;
                    };
                };
            };
        };
    };
    ready_health_ready_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    get_me_me_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceDeskUserRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_my_capabilities_me_capabilities_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceDeskCapabilitiesRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_my_tickets_me_tickets_get: {
        parameters: {
            query?: {
                status?: components["schemas"]["ServiceDeskTicketStatus"] | null;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TicketRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_notifications_notifications_get: {
        parameters: {
            query?: {
                unread_only?: boolean;
                limit?: number | null;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotificationRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    contextual_counters_notifications_contextual_counters_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceDeskCounters"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    read_all_notifications_read_all_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReadAllResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    unread_count_notifications_unread_count_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnreadCount"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    read_notification_notifications__notification_id__read_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                notification_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotificationRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_services_services_get: {
        parameters: {
            query?: {
                q?: string | null;
                category_id?: string | null;
                active?: boolean | null;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_service_services__service_id__get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                service_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_service_form_services__service_id__form_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                service_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PublishedTemplateRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_ticket_draft_tickets_drafts_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TicketDraftCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TicketRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_ticket_tickets__ticket_id__get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TicketRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_ticket_draft_tickets__ticket_id__patch: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TicketDraftUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TicketRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_ticket_approvals_tickets__ticket_id__approvals_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TicketApprovalStageRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    approve_ticket_tickets__ticket_id__approvals__approval_id__approve_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
                approval_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TicketApprovalDecision"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TicketRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reject_ticket_tickets__ticket_id__approvals__approval_id__reject_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
                approval_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TicketApprovalRejection"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TicketRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    assign_ticket_tickets__ticket_id__assign_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TicketAssignmentAction"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TicketRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_ticket_attachments_tickets__ticket_id__attachments_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceDeskAttachmentRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    upload_ticket_attachment_tickets__ticket_id__attachments_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_upload_ticket_attachment_tickets__ticket_id__attachments_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceDeskAttachmentRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_ticket_attachment_tickets__ticket_id__attachments__attachment_id__delete: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
                attachment_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    download_ticket_attachment_tickets__ticket_id__attachments__attachment_id__download_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
                attachment_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    cancel_ticket_tickets__ticket_id__cancel_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TicketReasonAction"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TicketRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    close_ticket_tickets__ticket_id__close_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TicketAction"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TicketRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_ticket_comments_tickets__ticket_id__comments_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TicketCommentRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_ticket_comment_tickets__ticket_id__comments_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TicketCommentCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TicketCommentRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_ticket_comment_tickets__ticket_id__comments__comment_id__delete: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
                comment_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_ticket_comment_tickets__ticket_id__comments__comment_id__patch: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
                comment_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TicketCommentUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TicketCommentRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_comment_attachments_tickets__ticket_id__comments__comment_id__attachments_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
                comment_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceDeskAttachmentRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    upload_comment_attachment_tickets__ticket_id__comments__comment_id__attachments_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
                comment_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_upload_comment_attachment_tickets__ticket_id__comments__comment_id__attachments_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceDeskAttachmentRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_field_attachments_tickets__ticket_id__fields__field_key__attachments_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
                field_key: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceDeskAttachmentRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    upload_field_attachment_tickets__ticket_id__fields__field_key__attachments_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
                field_key: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_upload_field_attachment_tickets__ticket_id__fields__field_key__attachments_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceDeskAttachmentRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_ticket_form_tickets__ticket_id__form_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PublishedTemplateRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    change_ticket_priority_tickets__ticket_id__priority_patch: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TicketPriorityUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TicketRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reassign_ticket_tickets__ticket_id__reassign_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TicketAssignmentAction"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TicketRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    request_ticket_clarification_tickets__ticket_id__request_clarification_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TicketCommentAction"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TicketRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    resolve_ticket_tickets__ticket_id__resolve_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TicketResolveAction"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TicketRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    resume_ticket_tickets__ticket_id__resume_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TicketAction"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TicketRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    start_ticket_tickets__ticket_id__start_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TicketAction"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TicketRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    submit_ticket_draft_tickets__ticket_id__submit_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TicketRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    wait_for_external_action_tickets__ticket_id__wait_external_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                ticket_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TicketReasonAction"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TicketRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_user_options_users_options_get: {
        parameters: {
            query?: {
                capability?: string | null;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceDeskUserOptionRead"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_workbench_counters_workbench_counters_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WorkbenchCounters"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_workbench_tickets_workbench_tickets_get: {
        parameters: {
            query?: {
                status?: components["schemas"]["ServiceDeskTicketStatus"] | null;
                assignee_user_id?: string | null;
                requester_user_id?: string | null;
                priority?: components["schemas"]["ServiceDeskPriority"] | null;
                category_id?: string | null;
                service_id?: string | null;
                sla_state?: components["schemas"]["WorkbenchSlaState"] | null;
                overdue?: boolean | null;
                created_from?: string | null;
                created_to?: string | null;
                q?: string | null;
                quick_view?: components["schemas"]["WorkbenchQuickView"] | null;
                page?: number;
                page_size?: number;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WorkbenchTicketPage"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_workbench_users_workbench_users_get: {
        parameters: {
            query?: {
                eligible_assignees?: boolean;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WorkbenchUserOption"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
}
