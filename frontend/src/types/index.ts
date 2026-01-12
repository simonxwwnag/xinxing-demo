export interface SpecSource {
  content: string;
  slice_id: string;
  doc_id: string;
  doc_name?: string;
  image_url?: string;
  chunk_type?: string;
  // 新增字段：支持多种内容格式
  md_content?: string;
  html_content?: string;
  point_id?: string;
}

export interface SupplierInfo {
  name: string;
  source: 'knowledge_base' | 'web_search';
  doc_id?: string;
  doc_name?: string;
  url?: string;
  description?: string;
  slice_id?: string; // 切片ID（知识库来源，用于查看原文）
  content?: string; // 原始内容（知识库来源，用于查看原文）
  // 结构化数据字段（用于知识库供应商的表格显示）
  product_code?: string;
  product_name?: string;
  supplier_type?: string;
  sub_category_name?: string;
  sub_category_code?: string;
  valid_from?: string;
  valid_to?: string;
  contact_person?: string; // 联系人
  relevance?: string; // 相关性标记（强相关/可能相关）
}

export interface Product {
  id: string;
  project_id: string;
  project_code: string;
  project_name: string;
  project_features?: string;
  unit: string;
  quantity: number;
  other_specs: SpecSource[];
  suppliers: SupplierInfo[];
  spec_summary?: string; // 规格参数总结内容
  price?: number;
  price_unit?: string;
  notes?: string;
  inquiry_completed: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductCreate {
  project_id: string;
  project_code: string;
  project_name: string;
  project_features?: string;
  unit: string;
  quantity: number;
}

export interface ProductUpdate {
  price?: number;
  price_unit?: string;
  notes?: string;
  inquiry_completed?: boolean;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  description?: string;
}

export interface PersonnelInfo {
  name?: string;
  department?: string;
  category?: string;
  certificate_name?: string;
  certificate_number?: string;
  issue_date?: string;
  expiry_date?: string;
  free_status?: string;
  content: string;
  slice_id?: string;
  doc_id?: string;
}

export interface CertificatePersonnelResultData {
  question: string;
  personnel_list: PersonnelInfo[];
  references: SpecSource[];
}

