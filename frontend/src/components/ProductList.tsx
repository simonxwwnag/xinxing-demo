import { useState } from 'react';
import type { Product } from '../types';
import SpecModal from './SpecModal';
import SpecSummary from './SpecSummary';
import SupplierList from './SupplierList';
import PriceForm from './PriceForm';
import WebSearchButton from './WebSearchButton';
import { searchSpecs, searchSuppliersFromKnowledge, updateProductSpecsAndSuppliers } from '../services/api';

interface ProductListProps {
  products: Product[];
  onUpdate: (id: string, updates: Partial<Product>) => Promise<void>;
  onDelete?: (id: string) => Promise<void>;
  onRefresh?: () => Promise<void>;
}

export default function ProductList({ products, onUpdate, onDelete, onRefresh }: ProductListProps) {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [showSpecModal, setShowSpecModal] = useState(false);
  const [selectedSpecs, setSelectedSpecs] = useState<any[]>([]);
  const [queryingKnowledge, setQueryingKnowledge] = useState<Set<string>>(new Set());
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set());
  const [querySuccessMessage, setQuerySuccessMessage] = useState<string | null>(null);

  const toggleRow = (productId: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(productId)) {
      newExpanded.delete(productId);
    } else {
      newExpanded.add(productId);
    }
    setExpandedRows(newExpanded);
  };

  const handleDelete = async (productId: string, productName: string) => {
    if (!onDelete) return;
    
    if (!window.confirm(`确定要删除产品"${productName}"吗？此操作不可恢复。`)) {
      return;
    }

    setDeletingIds(prev => new Set(prev).add(productId));
    try {
      await onDelete(productId);
    } catch (error) {
      console.error('删除产品失败:', error);
      alert('删除产品失败，请稍后重试');
    } finally {
      setDeletingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(productId);
        return newSet;
      });
    }
  };

  // 查询知识库的通用函数（仅用于手动查询）
  // 并行调用规格和供应商API，哪个完成就先更新哪个
  const queryKnowledgeForProduct = async (product: Product, isManualRequery: boolean = true) => {
    setQueryingKnowledge(prev => new Set(prev).add(product.id));
    
    let specsResult: any = null;
    let suppliersResult: any = null;
    let specsError: any = null;
    let suppliersError: any = null;
    
    try {
      console.log('[ProductList] 开始并行查询知识库:', product.project_name, product.project_features);
      const startTime = Date.now();
      
      // 并行调用两个API
      const [specsResponse, suppliersResponse] = await Promise.allSettled([
        searchSpecs(product.project_name, product.project_features || undefined),
        searchSuppliersFromKnowledge(product.project_name, product.project_features || undefined)
      ]);
      
      // 处理规格结果
      if (specsResponse.status === 'fulfilled') {
        specsResult = specsResponse.value;
        console.log('[ProductList] 规格查询完成，耗时:', Date.now() - startTime, 'ms');
        console.log('[ProductList] 规格数据:', specsResult);
      } else {
        specsError = specsResponse.reason;
        console.error('[ProductList] 规格查询失败:', specsError);
      }
      
      // 处理供应商结果
      if (suppliersResponse.status === 'fulfilled') {
        suppliersResult = suppliersResponse.value;
        console.log('[ProductList] 供应商查询完成，耗时:', Date.now() - startTime, 'ms');
        console.log('[ProductList] 供应商数据:', suppliersResult);
      } else {
        suppliersError = suppliersResponse.reason;
        console.error('[ProductList] 供应商查询失败:', suppliersError);
      }
      
      // 处理规格数据
      const newSpecs = specsResult?.specs || [];
      console.log('[ProductList] 处理specs，数量:', newSpecs.length);
      let uniqueSpecs = [];
      
      if (newSpecs.length > 0) {
        const existingSpecs = product.other_specs || [];
        const allSpecs = [...existingSpecs, ...newSpecs];
        uniqueSpecs = allSpecs.filter((spec, index, self) =>
          index === self.findIndex(s => s.slice_id === spec.slice_id)
        );
        console.log('[ProductList] specs去重后数量:', uniqueSpecs.length);
      } else {
        uniqueSpecs = product.other_specs || [];
        console.log('[ProductList] 没有新的specs，使用现有的');
      }
      
      // 处理供应商数据
      const existingWebSuppliers = product.suppliers.filter(s => s.source === 'web_search');
      const existingKnowledgeSuppliers = product.suppliers.filter(s => s.source === 'knowledge_base');
      const newKnowledgeSuppliers = suppliersResult?.suppliers || [];
      console.log('[ProductList] 处理suppliers，新供应商数量:', newKnowledgeSuppliers.length);
      
      // 检查新供应商的content字段
      newKnowledgeSuppliers.forEach((supplier: any, idx: number) => {
        const hasContent = supplier.content && supplier.content.length > 0;
        console.log(`[ProductList] 新供应商 ${idx + 1}: ${supplier.name}, content存在: ${hasContent}, content长度: ${supplier.content ? supplier.content.length : 0}`);
      });
      
      // 优先使用新的suppliers（有content），然后补充旧的suppliers（去重）
      // 先建立新suppliers的映射（按name）
      const newSuppliersMap = new Map<string, any>();
      newKnowledgeSuppliers.forEach((supplier: any) => {
        newSuppliersMap.set(supplier.name, supplier);
      });
      
      // 添加旧的suppliers（如果name不在新suppliers中）
      const uniqueKnowledgeSuppliers: any[] = [];
      existingKnowledgeSuppliers.forEach((supplier: any) => {
        if (!newSuppliersMap.has(supplier.name)) {
          uniqueKnowledgeSuppliers.push(supplier);
        }
      });
      
      // 添加所有新的suppliers（优先，有content）
      uniqueKnowledgeSuppliers.push(...newKnowledgeSuppliers);
      
      const allSuppliers = [...uniqueKnowledgeSuppliers, ...existingWebSuppliers];
      console.log('[ProductList] suppliers去重后数量:', allSuppliers.length);
      
      // 检查保存前的suppliers数据
      allSuppliers.forEach((supplier: any, idx: number) => {
        if (supplier.source === 'knowledge_base') {
          const hasContent = supplier.content && supplier.content.length > 0;
          console.log(`[ProductList] 保存前供应商 ${idx + 1}: ${supplier.name}, content存在: ${hasContent}, content长度: ${supplier.content ? supplier.content.length : 0}`);
        }
      });
      
      // 获取规格参数总结
      const specSummary = specsResult?.spec_summary || null;
      console.log('[ProductList] 准备保存数据: specs数量=', uniqueSpecs.length, 'suppliers数量=', allSuppliers.length, 'spec_summary长度=', specSummary ? specSummary.length : 0);
      
      await updateProductSpecsAndSuppliers(product.id, uniqueSpecs, allSuppliers, specSummary);
      
      console.log('[ProductList] 数据保存成功');
      
      // 查询完成后，自动展开该产品的详情
      setExpandedRows(prev => {
        const newSet = new Set(prev);
        newSet.add(product.id);
        return newSet;
      });
      
      if (onRefresh) {
        await onRefresh();
      }
      
      // 显示查询完成提示
      if (isManualRequery) {
        setQuerySuccessMessage(`"${product.project_name}" 查询完成`);
        setTimeout(() => setQuerySuccessMessage(null), 3000); // 3秒后自动消失
      }
      
      // 如果有部分失败，显示警告
      if (specsError && suppliersError) {
        throw new Error('规格和供应商查询都失败');
      } else if (specsError || suppliersError) {
        const errorMsg = specsError ? '规格查询失败' : '供应商查询失败';
        console.warn(`[ProductList] ${errorMsg}，但已保存其他数据`);
        if (isManualRequery) {
          setQuerySuccessMessage(`${errorMsg}，但已保存其他数据`);
          setTimeout(() => setQuerySuccessMessage(null), 3000);
        }
      }
      
    } catch (error: any) {
      console.error('[ProductList] 查询知识库失败:', error);
      console.error('[ProductList] 错误类型:', error?.constructor?.name);
      console.error('[ProductList] 错误消息:', error?.message);
      console.error('[ProductList] 错误代码:', error?.code);
      console.error('[ProductList] 响应数据:', error?.response?.data);
      console.error('[ProductList] 响应状态:', error?.response?.status);
      
      if (isManualRequery) {
        let errorMessage = '查询知识库失败，请检查网络连接或稍后重试';
        if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
          errorMessage = '查询超时，请稍后重试';
        } else if (error.response?.data?.detail) {
          errorMessage = error.response.data.detail;
        }
        setQuerySuccessMessage(errorMessage);
        setTimeout(() => setQuerySuccessMessage(null), 5000); // 错误消息显示5秒
      }
      // 自动查询失败时不显示错误提示，避免打扰用户
    } finally {
      setQueryingKnowledge(prev => {
        const newSet = new Set(prev);
        newSet.delete(product.id);
        return newSet;
      });
    }
  };

  // 手动重新查询知识库
  const handleRequeryKnowledge = async (product: Product) => {
    await queryKnowledgeForProduct(product, true);
  };

  // 统计正在查询的产品数量
  const queryingCount = queryingKnowledge.size;

  return (
    <div className="h-full flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">
            采购清单 ({products.length}项)
          </h2>
          <div className="flex items-center gap-3">
            {querySuccessMessage && (
              <div className="px-3 py-1.5 bg-green-100 text-green-700 rounded-lg text-sm font-medium">
                {querySuccessMessage}
              </div>
            )}
            {queryingCount > 0 && (
              <div className="flex items-center gap-2 text-sm text-blue-600">
                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>正在查询知识库 ({queryingCount}个产品)...</span>
              </div>
            )}
          </div>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto">
        {products.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <p>暂无产品数据</p>
            <p className="text-sm mt-2">请上传Excel文件</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {products.map((product) => {
              const isExpanded = expandedRows.has(product.id);
              const isQuerying = queryingKnowledge.has(product.id);
              const knowledgeSuppliers = product.suppliers.filter(s => s.source === 'knowledge_base');
              
              return (
                <div
                  key={product.id}
                  className="p-4 hover:bg-gray-50 transition-colors"
                >
                  {/* 折叠状态：关键信息 */}
                  <div className="flex items-center justify-between">
                    <div className="flex-1 grid grid-cols-6 gap-4 items-center">
                      <div className="text-sm">
                        <div className="text-gray-500 text-xs mb-1">项目编码</div>
                        <div className="text-gray-900 font-medium">{product.project_code}</div>
                      </div>
                      <div className="text-sm">
                        <div className="text-gray-500 text-xs mb-1">项目名称</div>
                        <div className="text-gray-900 font-medium">{product.project_name}</div>
                      </div>
                      <div className="text-sm">
                        <div className="text-gray-500 text-xs mb-1">项目特征</div>
                        <div className="text-gray-900 truncate" title={product.project_features}>
                          {product.project_features || '-'}
                        </div>
                      </div>
                      <div className="text-sm">
                        <div className="text-gray-500 text-xs mb-1">计量单位</div>
                        <div className="text-gray-900">{product.unit}</div>
                      </div>
                      <div className="text-sm">
                        <div className="text-gray-500 text-xs mb-1">工程量</div>
                        <div className="text-gray-900">{product.quantity}</div>
                      </div>
                      <div className="text-sm">
                        <div className="text-gray-500 text-xs mb-1">是否询价</div>
                        <div className="flex items-center gap-2">
                          {product.inquiry_completed ? (
                            <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">
                              已完成
                            </span>
                          ) : (
                            <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs">
                              未完成
                            </span>
                          )}
                          {isQuerying && (
                            <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs flex items-center gap-1">
                              <svg className="animate-spin h-3 w-3" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                              </svg>
                              查询中
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      {onDelete && (
                        <button
                          onClick={() => handleDelete(product.id, product.project_name)}
                          disabled={deletingIds.has(product.id)}
                          className="p-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                          title="删除产品"
                        >
                          {deletingIds.has(product.id) ? (
                            <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                          ) : (
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          )}
                        </button>
                      )}
                      <button
                        onClick={() => toggleRow(product.id)}
                        className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                      >
                        {isExpanded ? (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                          </svg>
                        ) : (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        )}
                      </button>
                    </div>
                  </div>

                  {/* 展开状态：详细信息 */}
                  {isExpanded && (
                    <div className="mt-4 pt-4 border-t border-gray-200 space-y-4">
                      {/* 规格参数总结 */}
                      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <h4 className="text-sm font-semibold text-blue-900">规格参数</h4>
                          </div>
                          <button
                            onClick={() => handleRequeryKnowledge(product)}
                            disabled={isQuerying}
                            className="px-3 py-1 text-xs bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {isQuerying ? '查询中...' : '重新查询'}
                          </button>
                        </div>
                        
                        <SpecSummary
                          summary={product.spec_summary || null}
                          references={product.other_specs}
                          productName={product.project_name}
                        />
                      </div>

                      {/* 供应商信息 */}
                      <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                            </svg>
                            <h4 className="text-sm font-semibold text-green-900">供应商信息</h4>
                            {knowledgeSuppliers.length > 0 && (
                              <span className="text-xs text-gray-600">
                                ({knowledgeSuppliers.length}个知识库供应商)
                              </span>
                            )}
                          </div>
                          {knowledgeSuppliers.length > 0 && (
                            <div className="flex items-center gap-1">
                              {knowledgeSuppliers.some(s => s.doc_name === '集团定商采购') && (
                                <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded border border-blue-300 text-xs">
                                  集团定商
                                </span>
                              )}
                              {knowledgeSuppliers.some(s => s.doc_name === '油田定商采购') && (
                                <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded border border-purple-300 text-xs">
                                  油田定商
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                        
                        {product.suppliers.length > 0 ? (
                          <SupplierList suppliers={product.suppliers} />
                        ) : (
                          <div className="p-3 bg-white rounded-lg border border-gray-200">
                            <p className="text-sm text-gray-500 text-center">
                              暂无供应商信息
                            </p>
                          </div>
                        )}
                      </div>
                      
                      {/* 网络搜索按钮 */}
                      <div>
                        <WebSearchButton
                          productName={product.project_name}
                          productId={product.id}
                          onSuppliersFound={async () => {
                            if (onRefresh) {
                              await onRefresh();
                            } else {
                              await onUpdate(product.id, {});
                            }
                          }}
                        />
                      </div>

                      {/* 价格表单 */}
                      <div>
                        <PriceForm product={product} onUpdate={onUpdate} />
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 规格详情弹窗 */}
      {showSpecModal && (
        <SpecModal
          specs={selectedSpecs}
          onClose={() => {
            setShowSpecModal(false);
            setSelectedSpecs([]);
          }}
        />
      )}
    </div>
  );
}

