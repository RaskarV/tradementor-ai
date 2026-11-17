export type Role = "owner" | "admin" | "educator";
export interface Me { id: number; email: string; role: Role }
export interface SeriesPoint { date: string; messages: number; blocked: number }
export interface Overview {
  total_users: number; active_users: number; total_conversations: number;
  messages_processed: number; messages_blocked: number; pending_support: number; series: SeriesPoint[];
}
export interface UserRow { id: number; telegram_id: number; username: string | null; experience: string | null; registered_at: string; last_active_at: string | null }
export interface ConversationRow { id: number; user_id: number; username: string | null; telegram_id: number; messages: number; blocked: number; last_message_at: string; is_active: boolean }
export interface ChatMessage { id: number; role: string; content: string; created_at: string; decision: string | null; rules: string[] | null; original_draft: string | null }
export interface ComplianceLog { id: number; user_id: number | null; decision: "cleared" | "blocked"; rules: string[]; severity: string | null; excerpt: string | null; message_type: string; created_at: string }
export interface RuleRow { code: string; category: string; severity: string; enabled: boolean; is_builtin: boolean; pattern: string | null }
export interface Ticket { id: number; ticket_code: string; user_id: number; status: "pending" | "assigned" | "answered" | "closed"; assigned_to: number | null; created_at: string; updated_at: string; username?: string | null; context?: string | null }
export interface KnowledgeDoc { id: number; title: string; topic: string; source_url: string | null; is_published: boolean; chunks: number; updated_at: string }
export interface AdminRow { id: number; email: string; role: Role; telegram_id: number | null; is_active: boolean }
