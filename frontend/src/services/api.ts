import axios from 'axios';
import type { Product, ProductUpdate, Project, ProjectCreate } from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000, // 默认30秒，但某些请求会单独设置更长的超时时间
});

// 添加请求拦截器用于日志记录
api.interceptors.request.use(
  (config) => {
    console.log('[API] 请求:', config.method?.toUpperCase(), config.url, '超时设置:', config.timeout || '使用默认值');
    return config;
  },
  (error) => {
    console.error('[API] 请求错误:', error);
    return Promise.reject(error);
  }
);

// 添加响应拦截器用于日志记录
api.interceptors.response.use(
  (response) => {
    console.log('[API] 响应:', response.config.url, '状态码:', response.status, '数据大小:', JSON.stringify(response.data).length, '字节');
    return response;
  },
  (error) => {
    console.error('[API] 响应错误:', error.config?.url, error.code, error.message);
    if (error.code === 'ECONNABORTED') {
      console.error('[API] 请求超时，超时设置:', error.config?.timeout);
    }
    return Promise.reject(error);
  }
);

// 上传Excel文件
export const uploadExcel = async (file: File, projectId: string): Promise<Product[]> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('project_id', projectId);
  const response = await api.post<Product[]>('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// 知识库查询（包含AI总结，可能需要较长时间）
export const searchKnowledge = async (productName: string, productFeatures?: string) => {
  const response = await api.post('/knowledge/search', {
    product_name: productName,
    product_features: productFeatures,
  }, {
    timeout: 120000, // 知识库查询+AI总结可能需要较长时间，设置为120秒
  });
  return response.data;
};

// 只搜索规格信息（独立API，哪个完成哪个返回）
export const searchSpecs = async (productName: string, productFeatures?: string) => {
  const response = await api.post('/knowledge/search-specs', {
    product_name: productName,
    product_features: productFeatures,
  }, {
    timeout: 120000, // 规格搜索+AI总结可能需要较长时间，设置为120秒
  });
  return response.data;
};

// 只搜索供应商信息（独立API，哪个完成哪个返回）
export const searchSuppliersFromKnowledge = async (productName: string, productFeatures?: string) => {
  const response = await api.post('/knowledge/search-suppliers', {
    product_name: productName,
    product_features: productFeatures,
  }, {
    timeout: 120000, // 供应商搜索+AI过滤可能需要较长时间，设置为120秒
  });
  return response.data;
};

// 知识库问答（包含AI总结，可能需要较长时间）
export const answerQuestion = async (question: string) => {
  const response = await api.post('/knowledge/qa', {
    question,
  }, {
    timeout: 120000, // AI问答可能需要较长时间，设置为120秒
  });
  return response.data;
};

// 网络搜索供应商
export const searchSuppliers = async (productName: string, limit: number = 5) => {
  const response = await api.post('/search/suppliers', {
    product_name: productName,
    limit,
  }, {
    timeout: 60000, // MCP调用可能需要更长时间，设置为60秒
  });
  return response.data;
};

// 为特定产品搜索供应商并更新
export const searchSuppliersForProduct = async (productId: string, productName: string, limit: number = 5) => {
  const response = await api.post(`/search/suppliers/${productId}`, {
    product_name: productName,
    limit,
  }, {
    timeout: 60000, // MCP调用可能需要更长时间，设置为60秒
  });
  return response.data;
};

// 获取所有产品
export const getProducts = async (projectId?: string): Promise<Product[]> => {
  const params = projectId ? { project_id: projectId } : {};
  const response = await api.get<Product[]>('/data/products', { params });
  return response.data;
};

// 更新产品信息
export const updateProduct = async (id: string, data: ProductUpdate): Promise<Product> => {
  const response = await api.put<Product>(`/data/products/${id}`, data);
  return response.data;
};

// 标记询价完成
export const completeInquiry = async (id: string): Promise<Product> => {
  const response = await api.post<Product>(`/data/products/${id}/complete`);
  return response.data;
};

// 更新产品的规格和供应商信息
export const updateProductSpecsAndSuppliers = async (
  id: string,
  specs?: any[],
  suppliers?: any[],
  spec_summary?: string | null
): Promise<Product> => {
  const response = await api.put<Product>(`/data/products/${id}/specs-suppliers`, {
    specs,
    suppliers,
    spec_summary,
  });
  return response.data;
};

// 删除产品
export const deleteProduct = async (id: string): Promise<void> => {
  await api.delete(`/data/products/${id}`);
};

// 获取所有项目
export const getProjects = async (): Promise<Project[]> => {
  const response = await api.get<Project[]>('/data/projects');
  return response.data;
};

// 创建项目
export const createProject = async (project: ProjectCreate): Promise<Project> => {
  const response = await api.post<Project>('/data/projects', project);
  return response.data;
};

// 删除项目
export const deleteProject = async (id: string): Promise<void> => {
  await api.delete(`/data/projects/${id}`);
};

// 证书人员查询（使用自然语言描述）
export const searchCertificatePersonnel = async (query: string) => {
  const response = await api.post('/knowledge/certificate-personnel', {
    query,
  }, {
    timeout: 120000, // 查询可能需要较长时间，设置为120秒
  });
  return response.data;
};

// 证书文件匹配
export interface CertificateFile {
  name: string;
  file_path: string;
  file_name: string;
  file_url: string;
}

export const matchCertificates = async (names: string[]): Promise<CertificateFile[]> => {
  const response = await api.post<{ certificates: CertificateFile[] }>('/certificate/match', {
    names,
  });
  return response.data.certificates || [];
};

// 刷新过期的图片链接
export const refreshImageLink = async (sliceId: string): Promise<string | null> => {
  try {
    const response = await api.post<{ image_url: string | null; success: boolean }>('/knowledge/refresh-image-link', {
      slice_id: sliceId,
    });
    return response.data.success ? response.data.image_url : null;
  } catch (error) {
    console.error('[API] 刷新图片链接失败:', error);
    return null;
  }
};

