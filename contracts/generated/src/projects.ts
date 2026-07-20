// Generated from projects.openapi.json. Do not edit by hand.
export interface paths {
    "/api/admin/audit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Audit Events */
        get: operations["list_audit_events_api_admin_audit_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/admin/projects": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Admin Projects */
        get: operations["list_admin_projects_api_admin_projects_get"];
        put?: never;
        /** Create Admin Project */
        post: operations["create_admin_project_api_admin_projects_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/admin/projects/{project_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Admin Project */
        get: operations["get_admin_project_api_admin_projects__project_id__get"];
        put?: never;
        post?: never;
        /** Archive Admin Project */
        delete: operations["archive_admin_project_api_admin_projects__project_id__delete"];
        options?: never;
        head?: never;
        /** Update Admin Project */
        patch: operations["update_admin_project_api_admin_projects__project_id__patch"];
        trace?: never;
    };
    "/api/admin/projects/{project_id}/attachments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Upload Project Attachment */
        post: operations["upload_project_attachment_api_admin_projects__project_id__attachments_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/admin/projects/{project_id}/candidates": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Project Candidates */
        get: operations["list_project_candidates_api_admin_projects__project_id__candidates_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/admin/projects/{project_id}/members/{user_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Add Project Member */
        post: operations["add_project_member_api_admin_projects__project_id__members__user_id__post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/admin/projects/{project_id}/responses": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Project Responses */
        get: operations["list_project_responses_api_admin_projects__project_id__responses_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/admin/projects/{project_id}/restore": {
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
        /** Restore Admin Project */
        patch: operations["restore_admin_project_api_admin_projects__project_id__restore_patch"];
        trace?: never;
    };
    "/api/admin/projects/{project_id}/stages": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Admin Project Stages */
        get: operations["list_admin_project_stages_api_admin_projects__project_id__stages_get"];
        put?: never;
        /** Create Admin Project Stage */
        post: operations["create_admin_project_stage_api_admin_projects__project_id__stages_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/admin/projects/{project_id}/stages/{stage_id}": {
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
        /** Update Admin Project Stage */
        patch: operations["update_admin_project_stage_api_admin_projects__project_id__stages__stage_id__patch"];
        trace?: never;
    };
    "/api/admin/projects/{project_id}/stages/{stage_id}/attachments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Upload Stage Attachment */
        post: operations["upload_stage_attachment_api_admin_projects__project_id__stages__stage_id__attachments_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/admin/projects/{project_id}/tasks": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Admin Project Task */
        post: operations["create_admin_project_task_api_admin_projects__project_id__tasks_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/admin/projects/{project_id}/tasks/{task_id}": {
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
        /** Update Admin Project Task */
        patch: operations["update_admin_project_task_api_admin_projects__project_id__tasks__task_id__patch"];
        trace?: never;
    };
    "/api/admin/reports": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Reports */
        get: operations["list_reports_api_admin_reports_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/admin/reports/periods": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Report Periods */
        get: operations["list_report_periods_api_admin_reports_periods_get"];
        put?: never;
        /** Open Report Period */
        post: operations["open_report_period_api_admin_reports_periods_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/admin/reports/periods/{period_id}/close": {
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
        /** Close Report Period */
        patch: operations["close_report_period_api_admin_reports_periods__period_id__close_patch"];
        trace?: never;
    };
    "/api/admin/responses": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Admin Responses */
        get: operations["list_admin_responses_api_admin_responses_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/admin/responses/{response_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Response */
        delete: operations["delete_response_api_admin_responses__response_id__delete"];
        options?: never;
        head?: never;
        /** Update Response Status */
        patch: operations["update_response_status_api_admin_responses__response_id__patch"];
        trace?: never;
    };
    "/api/admin/stats": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Admin Stats */
        get: operations["get_admin_stats_api_admin_stats_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/admin/users": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Admin Users */
        get: operations["list_admin_users_api_admin_users_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/attachments/{attachment_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Download Attachment */
        get: operations["download_attachment_api_attachments__attachment_id__get"];
        put?: never;
        post?: never;
        /** Delete Attachment */
        delete: operations["delete_attachment_api_attachments__attachment_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/competencies": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Competencies */
        get: operations["list_competencies_api_competencies_get"];
        put?: never;
        post?: never;
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
        /** Health */
        get: operations["health_api_health_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Me */
        get: operations["get_me_api_me_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/me/profile": {
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
        /** Update My Profile */
        patch: operations["update_my_profile_api_me_profile_patch"];
        trace?: never;
    };
    "/api/me/project-tasks/{task_id}": {
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
        /** Update My Project Task Status */
        patch: operations["update_my_project_task_status_api_me_project_tasks__task_id__patch"];
        trace?: never;
    };
    "/api/me/projects": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List My Projects */
        get: operations["list_my_projects_api_me_projects_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/me/projects/{project_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get My Project */
        get: operations["get_my_project_api_me_projects__project_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/me/projects/{project_id}/tasks": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List My Project Tasks */
        get: operations["list_my_project_tasks_api_me_projects__project_id__tasks_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/me/responses": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List My Responses */
        get: operations["list_my_responses_api_me_responses_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/me/responses/{response_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Withdraw My Response */
        delete: operations["withdraw_my_response_api_me_responses__response_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/project-tasks/{task_id}/attachments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Upload Task Attachment */
        post: operations["upload_task_attachment_api_project_tasks__task_id__attachments_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/projects": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Projects */
        get: operations["list_projects_api_projects_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/projects/recommendations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Project Recommendations */
        get: operations["list_project_recommendations_api_projects_recommendations_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/projects/{project_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Project */
        get: operations["get_project_api_projects__project_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/projects/{project_id}/responses": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Project Response */
        post: operations["create_project_response_api_projects__project_id__responses_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/projects/{project_id}/responses/{response_id}/attachments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Upload Response Attachment */
        post: operations["upload_response_attachment_api_projects__project_id__responses__response_id__attachments_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/reports/current": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Current Report State */
        get: operations["get_current_report_state_api_reports_current_get"];
        /** Submit Current Report */
        put: operations["submit_current_report_api_reports_current_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/reports/{report_id}/attachments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Upload Report Attachment */
        post: operations["upload_report_attachment_api_reports__report_id__attachments_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/users/directory": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List User Directory */
        get: operations["list_user_directory_api_users_directory_get"];
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
        /** AdminHalfYearReportRead */
        AdminHalfYearReportRead: {
            /** Competencies Used */
            competencies_used?: string | null;
            /** Completed Work */
            completed_work: string;
            /** Difficulties */
            difficulties?: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Next Period Plans */
            next_period_plans?: string | null;
            period: components["schemas"]["ReportPeriodRead"];
            /**
             * Period Id
             * Format: uuid
             */
            period_id: string;
            /** Project Results */
            project_results?: string | null;
            /**
             * Submitted At
             * Format: date-time
             */
            submitted_at: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            user: components["schemas"]["UserRead"];
            /**
             * User Id
             * Format: uuid
             */
            user_id: string;
        };
        /** AdminProjectResponseRead */
        AdminProjectResponseRead: {
            /**
             * Attachments
             * @default []
             */
            attachments: components["schemas"]["AttachmentRead"][];
            /** Comment */
            comment: string | null;
            /** Competencies */
            competencies: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Email */
            email: string;
            /** Full Name */
            full_name: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Processed At */
            processed_at: string | null;
            /** Processed By */
            processed_by: string | null;
            /**
             * Project Id
             * Format: uuid
             */
            project_id: string;
            /** Project Title */
            project_title: string;
            status: components["schemas"]["ProjectResponseStatus"];
        };
        /** AdminStats */
        AdminStats: {
            /** Projects Active */
            projects_active: number;
            /** Projects Archived */
            projects_archived: number;
            /** Projects Total */
            projects_total: number;
            /** Responses Accepted */
            responses_accepted: number;
            /** Responses By Project */
            responses_by_project: components["schemas"]["ResponsesByProject"][];
            /** Responses New */
            responses_new: number;
            /** Responses Rejected */
            responses_rejected: number;
            /** Responses Total */
            responses_total: number;
        };
        /**
         * AttachmentOwnerType
         * @enum {string}
         */
        AttachmentOwnerType: "project" | "stage" | "response" | "task" | "report";
        /** AttachmentRead */
        AttachmentRead: {
            /** Checksum */
            checksum?: string | null;
            /** Content Type */
            content_type: string | null;
            /** Content Type Detected */
            content_type_detected?: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Download Url */
            download_url: string;
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
            owner_type: components["schemas"]["AttachmentOwnerType"];
            /** Size Bytes */
            size_bytes: number;
            /** @default available */
            status: components["schemas"]["AttachmentStatus"];
        };
        /**
         * AttachmentStatus
         * @enum {string}
         */
        AttachmentStatus: "pending" | "quarantined" | "available" | "rejected" | "deleted";
        /** Body_upload_project_attachment_api_admin_projects__project_id__attachments_post */
        Body_upload_project_attachment_api_admin_projects__project_id__attachments_post: {
            /** File */
            file: string;
        };
        /** Body_upload_report_attachment_api_reports__report_id__attachments_post */
        Body_upload_report_attachment_api_reports__report_id__attachments_post: {
            /** File */
            file: string;
        };
        /** Body_upload_response_attachment_api_projects__project_id__responses__response_id__attachments_post */
        Body_upload_response_attachment_api_projects__project_id__responses__response_id__attachments_post: {
            /** File */
            file: string;
        };
        /** Body_upload_stage_attachment_api_admin_projects__project_id__stages__stage_id__attachments_post */
        Body_upload_stage_attachment_api_admin_projects__project_id__stages__stage_id__attachments_post: {
            /** File */
            file: string;
        };
        /** Body_upload_task_attachment_api_project_tasks__task_id__attachments_post */
        Body_upload_task_attachment_api_project_tasks__task_id__attachments_post: {
            /** File */
            file: string;
        };
        /** CompetencyRead */
        CompetencyRead: {
            /** Group */
            group: string;
            /** Name */
            name: string;
        };
        /** CurrentReportState */
        CurrentReportState: {
            active_period: components["schemas"]["ReportPeriodRead"] | null;
            report: components["schemas"]["HalfYearReportRead"] | null;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** HalfYearReportPayload */
        HalfYearReportPayload: {
            /** Competencies Used */
            competencies_used?: string | null;
            /** Completed Work */
            completed_work: string;
            /** Difficulties */
            difficulties?: string | null;
            /** Next Period Plans */
            next_period_plans?: string | null;
            /** Project Results */
            project_results?: string | null;
        };
        /** HalfYearReportRead */
        HalfYearReportRead: {
            /** Competencies Used */
            competencies_used?: string | null;
            /** Completed Work */
            completed_work: string;
            /** Difficulties */
            difficulties?: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Next Period Plans */
            next_period_plans?: string | null;
            /**
             * Period Id
             * Format: uuid
             */
            period_id: string;
            /** Project Results */
            project_results?: string | null;
            /**
             * Submitted At
             * Format: date-time
             */
            submitted_at: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /**
             * User Id
             * Format: uuid
             */
            user_id: string;
        };
        /** OkResponse */
        OkResponse: {
            /** Ok */
            ok: boolean;
        };
        /** PaginatedResponse[AdminProjectResponseRead] */
        PaginatedResponse_AdminProjectResponseRead_: {
            /** Items */
            items: components["schemas"]["AdminProjectResponseRead"][];
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
            /** Total */
            total: number;
        };
        /** PaginatedResponse[ProjectCandidateRead] */
        PaginatedResponse_ProjectCandidateRead_: {
            /** Items */
            items: components["schemas"]["ProjectCandidateRead"][];
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
            /** Total */
            total: number;
        };
        /** PaginatedResponse[ProjectSummary] */
        PaginatedResponse_ProjectSummary_: {
            /** Items */
            items: components["schemas"]["ProjectSummary"][];
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
            /** Total */
            total: number;
        };
        /** PaginatedResponse[UserProjectResponseRead] */
        PaginatedResponse_UserProjectResponseRead_: {
            /** Items */
            items: components["schemas"]["UserProjectResponseRead"][];
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
            /** Total */
            total: number;
        };
        /** ProjectAuditEventRead */
        ProjectAuditEventRead: {
            /** Action */
            action: string;
            /** Actor User Id */
            actor_user_id: string | null;
            /** After */
            after: {
                [key: string]: unknown;
            } | null;
            /** Before */
            before: {
                [key: string]: unknown;
            } | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** External User Id */
            external_user_id: string | null;
            /** Id */
            id: string;
            /** Module */
            module: string;
            /** Object Id */
            object_id: string;
            /** Object Type */
            object_type: string;
            /** Reason */
            reason: string | null;
            /** Request Id */
            request_id: string | null;
            /** Result */
            result: string;
            /** Source */
            source: string;
        };
        /** ProjectCandidateRead */
        ProjectCandidateRead: {
            /** About */
            about?: string | null;
            /** Competencies */
            competencies?: string | null;
            /** Department */
            department?: string | null;
            /** Email */
            email: string;
            /** Full Name */
            full_name: string;
            /**
             * Has Response
             * @default false
             */
            has_response: boolean;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Is Working Group Member
             * @default false
             */
            is_working_group_member: boolean;
            /**
             * Match Score
             * @default 0
             */
            match_score: number;
            /** Matched Blocks */
            matched_blocks?: string[];
            /** Matched Competencies */
            matched_competencies?: string[];
            /** Position */
            position?: string | null;
            role: components["schemas"]["UserRole"];
        };
        /** ProjectCompetencyBlock */
        ProjectCompetencyBlock: {
            /** Competencies */
            competencies?: string[];
            /** Title */
            title: string;
        };
        /** ProjectCompetencyCoverage */
        ProjectCompetencyCoverage: {
            /** Accepted Count */
            accepted_count: number;
            /** Block Title */
            block_title: string;
            /** Competency */
            competency: string;
            /** Is Covered */
            is_covered: boolean;
            /**
             * Priority
             * @enum {string}
             */
            priority: "open" | "covered";
        };
        /** ProjectCreate */
        ProjectCreate: {
            /** Competency Blocks */
            competency_blocks?: components["schemas"]["ProjectCompetencyBlock"][];
            /** Contact Email */
            contact_email?: string | null;
            /** Description */
            description: string;
            /** End Date */
            end_date?: string | null;
            /** Expected Result */
            expected_result?: string | null;
            /** Goal */
            goal: string;
            /** Planned Tasks */
            planned_tasks?: string | null;
            /** @default medium */
            priority: components["schemas"]["ProjectPriority"];
            /** @default strategic */
            project_type: components["schemas"]["ProjectType"];
            /** Required Competencies */
            required_competencies?: string | null;
            /** Responsible User Id */
            responsible_user_id?: string | null;
            /** Short Description */
            short_description: string;
            /** Start Date */
            start_date?: string | null;
            /** @default active */
            status: components["schemas"]["ProjectStatus"];
            /** Title */
            title: string;
            /** Working Group Member Ids */
            working_group_member_ids?: string[];
        };
        /** ProjectDetails */
        ProjectDetails: {
            /** Attachments */
            attachments: components["schemas"]["AttachmentRead"][];
            /** Competency Blocks */
            competency_blocks?: components["schemas"]["ProjectCompetencyBlock"][];
            /** Competency Coverage */
            competency_coverage?: components["schemas"]["ProjectCompetencyCoverage"][];
            /** Contact Email */
            contact_email: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Description */
            description: string;
            /** End Date */
            end_date: string | null;
            /** Expected Result */
            expected_result: string | null;
            /** Goal */
            goal: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Members */
            members: components["schemas"]["ProjectMemberRead"][];
            /** Planned Tasks */
            planned_tasks: string | null;
            priority: components["schemas"]["ProjectPriority"];
            project_type: components["schemas"]["ProjectType"];
            /** Required Competencies */
            required_competencies: string | null;
            /** Responses Count */
            responses_count: number;
            responsible: components["schemas"]["UserShort"] | null;
            /** Short Description */
            short_description: string;
            /** Start Date */
            start_date: string | null;
            status: components["schemas"]["ProjectStatus"];
            /** Title */
            title: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** Version */
            version: number;
        };
        /** ProjectMemberRead */
        ProjectMemberRead: {
            /** Email */
            email: string;
            /** Full Name */
            full_name: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            member_role: components["schemas"]["ProjectMemberRole"];
        };
        /**
         * ProjectMemberRole
         * @enum {string}
         */
        ProjectMemberRole: "manager" | "working_group_member" | "participant";
        /**
         * ProjectPriority
         * @enum {string}
         */
        ProjectPriority: "low" | "medium" | "high" | "critical";
        /** ProjectRecommendationRead */
        ProjectRecommendationRead: {
            /** Matched Blocks */
            matched_blocks?: string[];
            /** Matched Competencies */
            matched_competencies?: string[];
            /** Matched Profile Terms */
            matched_profile_terms?: string[];
            project: components["schemas"]["ProjectSummary"];
            /** Reasons */
            reasons?: string[];
            /** Score */
            score: number;
        };
        /** ProjectResponseCreate */
        ProjectResponseCreate: {
            /** Comment */
            comment?: string | null;
            /** Competencies */
            competencies?: string | null;
            /** Email */
            email: string;
            /** Full Name */
            full_name: string;
        };
        /** ProjectResponseRead */
        ProjectResponseRead: {
            /**
             * Attachments
             * @default []
             */
            attachments: components["schemas"]["AttachmentRead"][];
            /** Comment */
            comment: string | null;
            /** Competencies */
            competencies: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Email */
            email: string;
            /** Full Name */
            full_name: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Project Id
             * Format: uuid
             */
            project_id: string;
            status: components["schemas"]["ProjectResponseStatus"];
        };
        /**
         * ProjectResponseStatus
         * @enum {string}
         */
        ProjectResponseStatus: "new" | "viewed" | "contacted" | "accepted" | "rejected" | "cancelled";
        /** ProjectResponseStatusUpdate */
        ProjectResponseStatusUpdate: {
            status: components["schemas"]["ProjectResponseStatus"];
        };
        /** ProjectStageCreate */
        ProjectStageCreate: {
            /** End Date */
            end_date?: string | null;
            /**
             * Position
             * @default 0
             */
            position: number;
            /** Start Date */
            start_date?: string | null;
            /** Title */
            title: string;
        };
        /** ProjectStageRead */
        ProjectStageRead: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** End Date */
            end_date: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Position */
            position: number;
            /**
             * Project Id
             * Format: uuid
             */
            project_id: string;
            /** Start Date */
            start_date: string | null;
            /** Title */
            title: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** ProjectStageUpdate */
        ProjectStageUpdate: {
            /** End Date */
            end_date?: string | null;
            /** Position */
            position?: number | null;
            /** Start Date */
            start_date?: string | null;
            /** Title */
            title?: string | null;
        };
        /** ProjectStageWithTasksRead */
        ProjectStageWithTasksRead: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** End Date */
            end_date: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Position */
            position: number;
            /**
             * Project Id
             * Format: uuid
             */
            project_id: string;
            /** Start Date */
            start_date: string | null;
            /** Tasks */
            tasks?: components["schemas"]["ProjectTaskRead"][];
            /** Title */
            title: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /**
         * ProjectStatus
         * @enum {string}
         */
        ProjectStatus: "draft" | "active" | "paused" | "completed" | "archived";
        /** ProjectSummary */
        ProjectSummary: {
            /** Competency Blocks */
            competency_blocks?: components["schemas"]["ProjectCompetencyBlock"][];
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** End Date */
            end_date: string | null;
            /** Goal */
            goal: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            priority: components["schemas"]["ProjectPriority"];
            project_type: components["schemas"]["ProjectType"];
            /** Required Competencies */
            required_competencies: string | null;
            /** Responses Count */
            responses_count: number;
            responsible: components["schemas"]["UserShort"] | null;
            /** Short Description */
            short_description: string;
            /** Start Date */
            start_date: string | null;
            status: components["schemas"]["ProjectStatus"];
            /** Title */
            title: string;
            /** Version */
            version: number;
        };
        /** ProjectTaskCreate */
        ProjectTaskCreate: {
            /** Assignee User Id */
            assignee_user_id?: string | null;
            /** Description */
            description?: string | null;
            /** Due Date */
            due_date?: string | null;
            /** Stage Id */
            stage_id?: string | null;
            /** @default todo */
            status: components["schemas"]["ProjectTaskStatus"];
            /** Title */
            title: string;
        };
        /** ProjectTaskRead */
        ProjectTaskRead: {
            assignee: components["schemas"]["UserShort"] | null;
            /** Attachments */
            attachments?: components["schemas"]["AttachmentRead"][];
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Description */
            description: string | null;
            /** Due Date */
            due_date: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Is Overdue */
            is_overdue: boolean;
            /**
             * Project Id
             * Format: uuid
             */
            project_id: string;
            /** Stage Id */
            stage_id: string | null;
            status: components["schemas"]["ProjectTaskStatus"];
            /** Title */
            title: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /**
         * ProjectTaskStatus
         * @enum {string}
         */
        ProjectTaskStatus: "todo" | "in_progress" | "done" | "cancelled";
        /** ProjectTaskStatusUpdate */
        ProjectTaskStatusUpdate: {
            status: components["schemas"]["ProjectTaskStatus"];
        };
        /** ProjectTaskUpdate */
        ProjectTaskUpdate: {
            /** Assignee User Id */
            assignee_user_id?: string | null;
            /** Description */
            description?: string | null;
            /** Due Date */
            due_date?: string | null;
            /** Stage Id */
            stage_id?: string | null;
            status?: components["schemas"]["ProjectTaskStatus"] | null;
            /** Title */
            title?: string | null;
        };
        /**
         * ProjectType
         * @enum {string}
         */
        ProjectType: "strategic";
        /** ProjectUpdate */
        ProjectUpdate: {
            /** Competency Blocks */
            competency_blocks?: components["schemas"]["ProjectCompetencyBlock"][] | null;
            /** Contact Email */
            contact_email?: string | null;
            /** Description */
            description?: string | null;
            /** End Date */
            end_date?: string | null;
            /** Expected Result */
            expected_result?: string | null;
            /** Goal */
            goal?: string | null;
            /** Planned Tasks */
            planned_tasks?: string | null;
            priority?: components["schemas"]["ProjectPriority"] | null;
            project_type?: components["schemas"]["ProjectType"] | null;
            /** Required Competencies */
            required_competencies?: string | null;
            /** Responsible User Id */
            responsible_user_id?: string | null;
            /** Short Description */
            short_description?: string | null;
            /** Start Date */
            start_date?: string | null;
            status?: components["schemas"]["ProjectStatus"] | null;
            /** Title */
            title?: string | null;
            /** Working Group Member Ids */
            working_group_member_ids?: string[] | null;
        };
        /** ReportPeriodCreate */
        ReportPeriodCreate: {
            /** Ends On */
            ends_on?: string | null;
            /** Starts On */
            starts_on?: string | null;
            /** Title */
            title: string;
        };
        /** ReportPeriodRead */
        ReportPeriodRead: {
            /** Closed At */
            closed_at: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Ends On */
            ends_on: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Opened At
             * Format: date-time
             */
            opened_at: string;
            /**
             * Opened By
             * Format: uuid
             */
            opened_by: string;
            /** Starts On */
            starts_on: string | null;
            status: components["schemas"]["ReportPeriodStatus"];
            /** Title */
            title: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /**
         * ReportPeriodStatus
         * @enum {string}
         */
        ReportPeriodStatus: "open" | "closed";
        /** ResponsesByProject */
        ResponsesByProject: {
            /**
             * Project Id
             * Format: uuid
             */
            project_id: string;
            /** Project Title */
            project_title: string;
            /** Responses Count */
            responses_count: number;
        };
        /** UserProfileUpdate */
        UserProfileUpdate: {
            /** About */
            about?: string | null;
            /** Competencies */
            competencies?: string | null;
            /** Department */
            department?: string | null;
            /** Full Name */
            full_name: string;
            /** Position */
            position?: string | null;
        };
        /** UserProjectResponseRead */
        UserProjectResponseRead: {
            /**
             * Attachments
             * @default []
             */
            attachments: components["schemas"]["AttachmentRead"][];
            /** Comment */
            comment: string | null;
            /** Competencies */
            competencies: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Email */
            email: string;
            /** Full Name */
            full_name: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Project Id
             * Format: uuid
             */
            project_id: string;
            /** Project Title */
            project_title: string;
            status: components["schemas"]["ProjectResponseStatus"];
        };
        /** UserRead */
        UserRead: {
            /** About */
            about?: string | null;
            /** Competencies */
            competencies?: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Department */
            department?: string | null;
            /** Email */
            email: string;
            /** Full Name */
            full_name: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Position */
            position?: string | null;
            role: components["schemas"]["UserRole"];
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /**
         * UserRole
         * @enum {string}
         */
        UserRole: "employee" | "project_manager" | "platform_admin";
        /** UserShort */
        UserShort: {
            /** Email */
            email: string;
            /** Full Name */
            full_name: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
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
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    list_audit_events_api_admin_audit_get: {
        parameters: {
            query?: {
                action?: string | null;
                object_type?: string | null;
                object_id?: string | null;
                limit?: number;
                offset?: number;
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
                    "application/json": components["schemas"]["ProjectAuditEventRead"][];
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
    list_admin_projects_api_admin_projects_get: {
        parameters: {
            query?: {
                search?: string | null;
                status?: components["schemas"]["ProjectStatus"] | null;
                project_type?: components["schemas"]["ProjectType"] | null;
                competency?: string | null;
                sort?: "created_at_desc" | "created_at_asc" | "priority_desc" | "priority_asc";
                limit?: number | null;
                offset?: number | null;
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
                    "application/json": components["schemas"]["PaginatedResponse_ProjectSummary_"];
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
    create_admin_project_api_admin_projects_post: {
        parameters: {
            query?: never;
            header?: {
                "Idempotency-Key"?: string | null;
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProjectCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProjectDetails"];
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
    get_admin_project_api_admin_projects__project_id__get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                project_id: string;
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
                    "application/json": components["schemas"]["ProjectDetails"];
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
    archive_admin_project_api_admin_projects__project_id__delete: {
        parameters: {
            query?: never;
            header?: {
                "If-Match"?: string | null;
                authorization?: string | null;
            };
            path: {
                project_id: string;
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
                    "application/json": components["schemas"]["OkResponse"];
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
    update_admin_project_api_admin_projects__project_id__patch: {
        parameters: {
            query?: never;
            header?: {
                "If-Match"?: string | null;
                authorization?: string | null;
            };
            path: {
                project_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProjectUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProjectDetails"];
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
    upload_project_attachment_api_admin_projects__project_id__attachments_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                project_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_upload_project_attachment_api_admin_projects__project_id__attachments_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AttachmentRead"];
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
    list_project_candidates_api_admin_projects__project_id__candidates_get: {
        parameters: {
            query?: {
                search?: string | null;
                block_title?: string | null;
                competency?: string | null;
                sort?: "match_desc" | "name_asc" | "responses_asc";
                limit?: number | null;
                offset?: number | null;
            };
            header?: {
                authorization?: string | null;
            };
            path: {
                project_id: string;
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
                    "application/json": components["schemas"]["PaginatedResponse_ProjectCandidateRead_"];
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
    add_project_member_api_admin_projects__project_id__members__user_id__post: {
        parameters: {
            query?: never;
            header?: {
                "Idempotency-Key"?: string | null;
                authorization?: string | null;
            };
            path: {
                project_id: string;
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
                    "application/json": components["schemas"]["ProjectDetails"];
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
    list_project_responses_api_admin_projects__project_id__responses_get: {
        parameters: {
            query?: {
                status?: components["schemas"]["ProjectResponseStatus"] | null;
                limit?: number | null;
                offset?: number | null;
            };
            header?: {
                authorization?: string | null;
            };
            path: {
                project_id: string;
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
                    "application/json": components["schemas"]["PaginatedResponse_AdminProjectResponseRead_"];
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
    restore_admin_project_api_admin_projects__project_id__restore_patch: {
        parameters: {
            query?: never;
            header?: {
                "If-Match"?: string | null;
                authorization?: string | null;
            };
            path: {
                project_id: string;
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
                    "application/json": components["schemas"]["ProjectDetails"];
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
    list_admin_project_stages_api_admin_projects__project_id__stages_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                project_id: string;
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
                    "application/json": components["schemas"]["ProjectStageWithTasksRead"][];
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
    create_admin_project_stage_api_admin_projects__project_id__stages_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                project_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProjectStageCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProjectStageRead"];
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
    update_admin_project_stage_api_admin_projects__project_id__stages__stage_id__patch: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                project_id: string;
                stage_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProjectStageUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProjectStageRead"];
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
    upload_stage_attachment_api_admin_projects__project_id__stages__stage_id__attachments_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                project_id: string;
                stage_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_upload_stage_attachment_api_admin_projects__project_id__stages__stage_id__attachments_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AttachmentRead"];
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
    create_admin_project_task_api_admin_projects__project_id__tasks_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                project_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProjectTaskCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProjectTaskRead"];
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
    update_admin_project_task_api_admin_projects__project_id__tasks__task_id__patch: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                project_id: string;
                task_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProjectTaskUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProjectTaskRead"];
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
    list_reports_api_admin_reports_get: {
        parameters: {
            query?: {
                period_id?: string | null;
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
                    "application/json": components["schemas"]["AdminHalfYearReportRead"][];
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
    list_report_periods_api_admin_reports_periods_get: {
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
                    "application/json": components["schemas"]["ReportPeriodRead"][];
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
    open_report_period_api_admin_reports_periods_post: {
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
                "application/json": components["schemas"]["ReportPeriodCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReportPeriodRead"];
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
    close_report_period_api_admin_reports_periods__period_id__close_patch: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                period_id: string;
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
                    "application/json": components["schemas"]["ReportPeriodRead"];
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
    list_admin_responses_api_admin_responses_get: {
        parameters: {
            query?: {
                project_id?: string | null;
                status?: components["schemas"]["ProjectResponseStatus"] | null;
                search?: string | null;
                limit?: number | null;
                offset?: number | null;
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
                    "application/json": components["schemas"]["PaginatedResponse_AdminProjectResponseRead_"];
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
    delete_response_api_admin_responses__response_id__delete: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                response_id: string;
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
                    "application/json": components["schemas"]["OkResponse"];
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
    update_response_status_api_admin_responses__response_id__patch: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                response_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProjectResponseStatusUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AdminProjectResponseRead"];
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
    get_admin_stats_api_admin_stats_get: {
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
                    "application/json": components["schemas"]["AdminStats"];
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
    list_admin_users_api_admin_users_get: {
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
                    "application/json": components["schemas"]["UserRead"][];
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
    download_attachment_api_attachments__attachment_id__get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
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
    delete_attachment_api_attachments__attachment_id__delete: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
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
                    "application/json": components["schemas"]["OkResponse"];
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
    list_competencies_api_competencies_get: {
        parameters: {
            query?: {
                search?: string | null;
            };
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
                    "application/json": components["schemas"]["CompetencyRead"][];
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
    health_api_health_get: {
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
    get_me_api_me_get: {
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
                    "application/json": components["schemas"]["UserRead"];
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
    update_my_profile_api_me_profile_patch: {
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
                "application/json": components["schemas"]["UserProfileUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserRead"];
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
    update_my_project_task_status_api_me_project_tasks__task_id__patch: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                task_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProjectTaskStatusUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProjectTaskRead"];
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
    list_my_projects_api_me_projects_get: {
        parameters: {
            query?: {
                search?: string | null;
                status?: components["schemas"]["ProjectStatus"] | null;
                sort?: "created_at_desc" | "created_at_asc" | "priority_desc" | "priority_asc";
                limit?: number | null;
                offset?: number | null;
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
                    "application/json": components["schemas"]["PaginatedResponse_ProjectSummary_"];
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
    get_my_project_api_me_projects__project_id__get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                project_id: string;
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
                    "application/json": components["schemas"]["ProjectDetails"];
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
    list_my_project_tasks_api_me_projects__project_id__tasks_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                project_id: string;
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
                    "application/json": components["schemas"]["ProjectTaskRead"][];
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
    list_my_responses_api_me_responses_get: {
        parameters: {
            query?: {
                limit?: number | null;
                offset?: number | null;
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
                    "application/json": components["schemas"]["PaginatedResponse_UserProjectResponseRead_"];
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
    withdraw_my_response_api_me_responses__response_id__delete: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                response_id: string;
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
                    "application/json": components["schemas"]["UserProjectResponseRead"];
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
    upload_task_attachment_api_project_tasks__task_id__attachments_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                task_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_upload_task_attachment_api_project_tasks__task_id__attachments_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AttachmentRead"];
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
    list_projects_api_projects_get: {
        parameters: {
            query?: {
                search?: string | null;
                status?: components["schemas"]["ProjectStatus"] | null;
                project_type?: components["schemas"]["ProjectType"] | null;
                competency?: string | null;
                sort?: "created_at_desc" | "created_at_asc" | "priority_desc" | "priority_asc";
                limit?: number | null;
                offset?: number | null;
            };
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
                    "application/json": components["schemas"]["PaginatedResponse_ProjectSummary_"];
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
    list_project_recommendations_api_projects_recommendations_get: {
        parameters: {
            query?: {
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
                    "application/json": components["schemas"]["ProjectRecommendationRead"][];
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
    get_project_api_projects__project_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
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
                    "application/json": components["schemas"]["ProjectDetails"];
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
    create_project_response_api_projects__project_id__responses_post: {
        parameters: {
            query?: never;
            header?: {
                "Idempotency-Key"?: string | null;
                authorization?: string | null;
            };
            path: {
                project_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProjectResponseCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProjectResponseRead"];
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
    upload_response_attachment_api_projects__project_id__responses__response_id__attachments_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                project_id: string;
                response_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_upload_response_attachment_api_projects__project_id__responses__response_id__attachments_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AttachmentRead"];
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
    get_current_report_state_api_reports_current_get: {
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
                    "application/json": components["schemas"]["CurrentReportState"];
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
    submit_current_report_api_reports_current_put: {
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
                "application/json": components["schemas"]["HalfYearReportPayload"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HalfYearReportRead"];
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
    upload_report_attachment_api_reports__report_id__attachments_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                report_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_upload_report_attachment_api_reports__report_id__attachments_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AttachmentRead"];
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
    list_user_directory_api_users_directory_get: {
        parameters: {
            query?: {
                search?: string | null;
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
                    "application/json": components["schemas"]["UserRead"][];
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
