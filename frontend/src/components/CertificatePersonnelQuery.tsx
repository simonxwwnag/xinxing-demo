import { useState } from 'react';
import { searchCertificatePersonnel } from '../services/api';
import type { CertificatePersonnelResultData } from '../types';

interface CertificatePersonnelQueryProps {
  onResultChange?: (result: CertificatePersonnelResultData | null) => void;
}

export default function CertificatePersonnelQuery({ onResultChange }: CertificatePersonnelQueryProps) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 验证输入
    if (!query.trim()) {
      setError('请输入查询需求');
      return;
    }

    setLoading(true);
    setError(null);
    if (onResultChange) {
      onResultChange(null);
    }

    try {
      const response = await searchCertificatePersonnel(query.trim());
      
      // 确保personnel_list是数组
      let personnelList = response?.personnel_list;
      if (!personnelList) {
        personnelList = [];
      } else if (!Array.isArray(personnelList)) {
        console.warn('[证书人员查询] personnel_list不是数组类型:', typeof personnelList);
        personnelList = [];
      }
      
      // 确保references是数组
      let references = response?.references;
      if (!references) {
        references = [];
      } else if (!Array.isArray(references)) {
        console.warn('[证书人员查询] references不是数组类型:', typeof references);
        references = [];
      }
      
      const result: CertificatePersonnelResultData = {
        question: response?.question || query.trim(),
        personnel_list: personnelList,
        references: references,
      };
      
      if (onResultChange) {
        onResultChange(result);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '查询失败，请重试');
      if (onResultChange) {
        onResultChange(null);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* 输入区域 */}
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">证书人员查询</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              查询需求 <span className="text-red-500">*</span>
            </label>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="请输入您的需求，例如：&#10;标段时间：2026年1月到2026年3月&#10;需要2个关键岗位HSE培训施工项目负责人证书的人员，需要3个一级建造师注册证书的人员&#10;空闲状态：空闲"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
              rows={8}
              disabled={loading}
            />
            <p className="mt-2 text-xs text-gray-500">
              提示：可以直接用自然语言描述需求，AI会自动解析标段时间、证书要求、空闲状态等信息
            </p>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 inline" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                正在查询...
              </>
            ) : (
              '查询'
            )}
          </button>
        </form>
      </div>

      {/* 提示信息 */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="text-center py-12 text-gray-400">
          <svg
            className="w-16 h-16 mx-auto mb-4 text-gray-300"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <p className="text-sm">请在左侧输入查询需求，AI会自动解析并查找匹配的人员</p>
          <div className="mt-4 text-xs text-gray-400 space-y-1">
            <p>示例：</p>
            <p>• 标段时间：2026年1月到2026年3月，需要2个一级建造师</p>
            <p>• 2026年1-3月，需要3个HSE培训证书，人员要空闲</p>
          </div>
        </div>
      </div>
    </div>
  );
}

