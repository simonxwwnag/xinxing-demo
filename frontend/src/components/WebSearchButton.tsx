import { useState } from 'react';
import { searchSuppliersForProduct } from '../services/api';
import type { SupplierInfo } from '../types';

interface WebSearchButtonProps {
  productName: string;
  productId: string;
  onSuppliersFound: (suppliers: SupplierInfo[]) => void;
}

export default function WebSearchButton({ productName, productId, onSuppliersFound }: WebSearchButtonProps) {
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    setSearching(true);
    setError(null);

    try {
      // 使用为特定产品搜索的API，会自动更新产品信息
      const response = await searchSuppliersForProduct(productId, productName, 5);
      
      if (response.suppliers && response.suppliers.length > 0) {
        // 调用回调函数通知父组件更新
        onSuppliersFound(response.suppliers);
        // 显示成功消息
        console.log(`成功找到 ${response.suppliers.length} 个供应商`);
      } else {
        setError('未找到供应商信息，请稍后重试或检查网络连接');
      }
    } catch (err: any) {
      console.error('搜索供应商失败:', err);
      if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        setError('搜索超时，MCP调用可能需要更长时间，请稍后重试');
      } else {
        setError(err.response?.data?.detail || err.message || '搜索失败，请检查网络连接');
      }
    } finally {
      setSearching(false);
    }
  };

  return (
    <div>
      <button
        onClick={handleSearch}
        disabled={searching}
        className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white text-sm font-medium rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {searching ? (
          <>
            <svg
              className="animate-spin -ml-1 mr-2 h-4 w-4 inline"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            搜索中...
          </>
        ) : (
          <>
            <svg
              className="w-4 h-4 inline mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            网络搜索供应商
          </>
        )}
      </button>
      {error && (
        <p className="text-xs text-red-600 mt-2">{error}</p>
      )}
    </div>
  );
}

