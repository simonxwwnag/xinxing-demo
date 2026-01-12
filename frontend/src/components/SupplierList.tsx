import { useState } from 'react';
import type { SupplierInfo } from '../types';

interface SupplierListProps {
  suppliers: SupplierInfo[];
}

export default function SupplierList({ suppliers }: SupplierListProps) {
  const [selectedSupplier, setSelectedSupplier] = useState<SupplierInfo | null>(null);
  const knowledgeSuppliers = suppliers.filter(s => s.source === 'knowledge_base');
  const webSuppliers = suppliers.filter(s => s.source === 'web_search');
  
  // 区分集团文档和油田文档的供应商，并按相关性排序（强相关优先）
  const sortByRelevance = (suppliers: SupplierInfo[]) => {
    return [...suppliers].sort((a, b) => {
      if (a.relevance === '强相关' && b.relevance !== '强相关') return -1;
      if (a.relevance !== '强相关' && b.relevance === '强相关') return 1;
      return 0;
    });
  };
  
  const groupSuppliers = sortByRelevance(knowledgeSuppliers.filter(s => s.doc_name === '集团定商采购'));
  const oilfieldSuppliers = sortByRelevance(knowledgeSuppliers.filter(s => s.doc_name === '油田定商采购'));
  const otherKnowledgeSuppliers = sortByRelevance(knowledgeSuppliers.filter(s => 
    s.doc_name !== '集团定商采购' && s.doc_name !== '油田定商采购'
  ));
  
  // 判断知识库供应商是否有结构化数据（用于表格显示）
  const hasStructuredData = knowledgeSuppliers.some(s => 
    s.product_code || s.product_name || s.supplier_type
  );

  return (
    <div className="space-y-4">
      {/* 集团定商采购供应商 */}
      {groupSuppliers.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <span className="text-blue-600">集团定商采购</span>
            <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded border border-blue-300 text-xs font-medium">
              集团文档
            </span>
            <span className="text-xs text-gray-500">({groupSuppliers.length}个)</span>
          </h4>
          
          {hasStructuredData ? (
            // 表格显示
            <div className="overflow-x-auto border border-gray-200 rounded-lg">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">相关性</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">供应商名称</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">类型</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">物资类别</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">有效期开始</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">有效期结束</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">联系人</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">操作</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {groupSuppliers.map((supplier, index) => (
                    <tr key={index} className={`hover:bg-gray-50 transition-colors ${supplier.relevance === '强相关' ? 'bg-green-50/30' : ''}`}>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {supplier.relevance && (
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            supplier.relevance === '强相关'
                              ? 'bg-green-100 text-green-800 border border-green-300'
                              : 'bg-yellow-100 text-yellow-800 border border-yellow-300'
                          }`}>
                            {supplier.relevance === '强相关' ? (
                              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                              </svg>
                            ) : (
                              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                              </svg>
                            )}
                            {supplier.relevance}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{supplier.name}</div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {supplier.supplier_type && (
                          <span className={`px-2 py-1 text-xs rounded ${
                            supplier.supplier_type === '制造商' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-blue-100 text-blue-800'
                          }`}>
                            {supplier.supplier_type}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {supplier.sub_category_name || '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {supplier.valid_from || '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {supplier.valid_to || '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {supplier.contact_person || '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {supplier.slice_id && (
                          <button
                            onClick={() => {
                              console.log('[SupplierList] 查看原文，supplier数据:', {
                                name: supplier.name,
                                content: supplier.content ? `${supplier.content.substring(0, 50)}...` : 'null',
                                contentLength: supplier.content ? supplier.content.length : 0,
                                slice_id: supplier.slice_id
                              });
                              setSelectedSupplier(supplier);
                            }}
                            className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors"
                          >
                            查看原文
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            // 卡片显示（兼容旧数据）
            <div className="space-y-2">
              {groupSuppliers.map((supplier, index) => (
                <div
                  key={index}
                  className={`p-3 rounded-lg border transition-all ${
                    supplier.relevance === '强相关'
                      ? 'bg-green-50/50 border-green-300 hover:border-green-400'
                      : 'bg-gray-50 border-gray-200 hover:border-blue-400'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="text-gray-900 font-medium">{supplier.name}</p>
                        <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs border border-blue-300 font-medium">
                          集团文档
                        </span>
                        {supplier.relevance && (
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                            supplier.relevance === '强相关'
                              ? 'bg-green-100 text-green-800 border border-green-300'
                              : 'bg-yellow-100 text-yellow-800 border border-yellow-300'
                          }`}>
                            {supplier.relevance === '强相关' ? (
                              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                              </svg>
                            ) : (
                              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                              </svg>
                            )}
                            {supplier.relevance}
                          </span>
                        )}
                      </div>
                      {supplier.description && (
                        <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                          {supplier.description}
                        </p>
                      )}
                    </div>
                    {supplier.slice_id && (
                      <button
                        onClick={() => setSelectedSupplier(supplier)}
                        className="ml-3 px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors"
                      >
                        查看原文
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 油田定商采购供应商 */}
      {oilfieldSuppliers.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <span className="text-purple-600">油田定商采购</span>
            <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded border border-purple-300 text-xs font-medium">
              油田文档
            </span>
            <span className="text-xs text-gray-500">({oilfieldSuppliers.length}个)</span>
          </h4>
          
          {hasStructuredData ? (
            // 表格显示
            <div className="overflow-x-auto border border-gray-200 rounded-lg">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">相关性</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">供应商名称</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">类型</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">物资类别</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">有效期开始</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">有效期结束</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">联系人</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">操作</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {oilfieldSuppliers.map((supplier, index) => (
                    <tr key={index} className={`hover:bg-gray-50 transition-colors ${supplier.relevance === '强相关' ? 'bg-green-50/30' : ''}`}>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {supplier.relevance && (
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            supplier.relevance === '强相关'
                              ? 'bg-green-100 text-green-800 border border-green-300'
                              : 'bg-yellow-100 text-yellow-800 border border-yellow-300'
                          }`}>
                            {supplier.relevance === '强相关' ? (
                              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                              </svg>
                            ) : (
                              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                              </svg>
                            )}
                            {supplier.relevance}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{supplier.name}</div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {supplier.supplier_type && (
                          <span className={`px-2 py-1 text-xs rounded ${
                            supplier.supplier_type === '制造商' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-blue-100 text-blue-800'
                          }`}>
                            {supplier.supplier_type}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {supplier.sub_category_name || '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {supplier.valid_from || '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {supplier.valid_to || '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {supplier.contact_person || '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {supplier.slice_id && (
                          <button
                            onClick={() => {
                              console.log('[SupplierList] 查看原文，supplier数据:', {
                                name: supplier.name,
                                content: supplier.content ? `${supplier.content.substring(0, 50)}...` : 'null',
                                contentLength: supplier.content ? supplier.content.length : 0,
                                slice_id: supplier.slice_id
                              });
                              setSelectedSupplier(supplier);
                            }}
                            className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors"
                          >
                            查看原文
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            // 卡片显示（兼容旧数据）
            <div className="space-y-2">
              {oilfieldSuppliers.map((supplier, index) => (
                <div
                  key={index}
                  className={`p-3 rounded-lg border transition-all ${
                    supplier.relevance === '强相关'
                      ? 'bg-green-50/50 border-green-300 hover:border-green-400'
                      : 'bg-gray-50 border-gray-200 hover:border-purple-400'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="text-gray-900 font-medium">{supplier.name}</p>
                        <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs border border-purple-300 font-medium">
                          油田文档
                        </span>
                        {supplier.relevance && (
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                            supplier.relevance === '强相关'
                              ? 'bg-green-100 text-green-800 border border-green-300'
                              : 'bg-yellow-100 text-yellow-800 border border-yellow-300'
                          }`}>
                            {supplier.relevance === '强相关' ? (
                              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                              </svg>
                            ) : (
                              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                              </svg>
                            )}
                            {supplier.relevance}
                          </span>
                        )}
                      </div>
                      {supplier.description && (
                        <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                          {supplier.description}
                        </p>
                      )}
                    </div>
                    {supplier.slice_id && (
                      <button
                        onClick={() => setSelectedSupplier(supplier)}
                        className="ml-3 px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors"
                      >
                        查看原文
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 其他知识库供应商（如果有） */}
      {otherKnowledgeSuppliers.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <span className="text-gray-600">其他知识库供应商</span>
            <span className="text-xs text-gray-500">({otherKnowledgeSuppliers.length}个)</span>
          </h4>
          <div className="space-y-2">
            {otherKnowledgeSuppliers.map((supplier, index) => (
              <div
                key={index}
                className="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:border-gray-400 transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="text-gray-900 font-medium">{supplier.name}</p>
                      {supplier.doc_name && (
                        <span className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs border border-gray-300">
                          {supplier.doc_name}
                        </span>
                      )}
                    </div>
                    {supplier.description && (
                      <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                        {supplier.description}
                      </p>
                    )}
                  </div>
                  {supplier.slice_id && (
                    <button
                      onClick={() => setSelectedSupplier(supplier)}
                      className="ml-3 px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors"
                    >
                      查看原文
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 网络搜索供应商 */}
      {webSuppliers.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <span className="w-2 h-2 bg-purple-600 rounded-full"></span>
            网络搜索供应商
          </h4>
          <div className="space-y-2">
            {webSuppliers.map((supplier, index) => (
              <div
                key={index}
                className="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:border-purple-400 transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-gray-900 font-medium">{supplier.name}</p>
                    {supplier.description && (
                      <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                        {supplier.description}
                      </p>
                    )}
                  </div>
                  {supplier.url && (
                    <a
                      href={supplier.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="ml-3 p-2 hover:bg-gray-100 rounded transition-colors"
                    >
                      <svg
                        className="w-5 h-5 text-purple-600"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                        />
                      </svg>
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {suppliers.length === 0 && (
        <div className="text-center py-4 text-gray-500 text-sm">
          暂无供应商信息
        </div>
      )}
      
      {/* 供应商原文弹窗 */}
      {selectedSupplier && (
        <div
          className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={() => setSelectedSupplier(null)}
        >
          <div
            className="bg-white p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto rounded-xl shadow-2xl border border-gray-200"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-900">供应商原文</h3>
              <button
                onClick={() => setSelectedSupplier(null)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <svg
                  className="w-6 h-6 text-gray-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
            
            <div className="space-y-4">
              {selectedSupplier.content ? (
                <div className="bg-white p-4 rounded-lg border border-gray-300">
                  <div className="text-gray-900 text-sm whitespace-pre-wrap font-mono break-words">
                    {selectedSupplier.content}
                  </div>
                </div>
              ) : (
                <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                  <div className="text-center text-gray-500 mb-2">暂无原始内容</div>
                  <div className="text-xs text-gray-400 mt-2">
                    调试信息: content={selectedSupplier.content ? '存在' : '不存在'}, 
                    content长度={selectedSupplier.content ? selectedSupplier.content.length : 0},
                    slice_id={selectedSupplier.slice_id ? '存在' : '不存在'}
                  </div>
                </div>
              )}
              
              <div className="flex justify-end">
                <button
                  onClick={() => setSelectedSupplier(null)}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg border border-gray-300 hover:bg-gray-200 transition-colors text-sm"
                >
                  关闭
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

