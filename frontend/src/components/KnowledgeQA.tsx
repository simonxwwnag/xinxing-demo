import { useState } from 'react';
import { answerQuestion } from '../services/api';

interface KnowledgeQAProps {
  onClose?: () => void;
  onResultChange?: (result: any) => void;
}

export default function KnowledgeQA({ onClose: _onClose, onResultChange }: KnowledgeQAProps) {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError(null);
    if (onResultChange) {
      onResultChange(null);
    }

    try {
      console.log('[KnowledgeQA] 开始发送问答请求:', question);
      const startTime = Date.now();
      
      // 使用知识库问答API
      const response = await answerQuestion(question);
      
      const elapsed = Date.now() - startTime;
      console.log('[KnowledgeQA] 请求完成，耗时:', elapsed, 'ms');
      console.log('[KnowledgeQA] 响应数据:', response);
      console.log('[KnowledgeQA] answer类型:', typeof response?.answer);
      console.log('[KnowledgeQA] answer长度:', response?.answer?.length);
      console.log('[KnowledgeQA] references类型:', typeof response?.references);
      console.log('[KnowledgeQA] references长度:', response?.references?.length);
      
      if (!response) {
        throw new Error('响应数据为空');
      }
      
      const result = {
        question,
        answer: response.answer || '未找到相关信息',
        references: response.references || [],
      };
      
      console.log('[KnowledgeQA] 准备返回结果:', result);
      
      if (onResultChange) {
        onResultChange(result);
      }
    } catch (err: any) {
      console.error('[KnowledgeQA] 请求失败:', err);
      console.error('[KnowledgeQA] 错误类型:', err?.constructor?.name);
      console.error('[KnowledgeQA] 错误消息:', err?.message);
      console.error('[KnowledgeQA] 错误代码:', err?.code);
      console.error('[KnowledgeQA] 响应数据:', err?.response?.data);
      console.error('[KnowledgeQA] 响应状态:', err?.response?.status);
      
      let errorMessage = '问答失败，请重试';
      
      if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        errorMessage = '请求超时，请稍后重试';
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
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
        <h2 className="text-xl font-semibold text-gray-900 mb-4">知识库问答</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="请输入您的问题，例如：某种产品的技术规格是什么？如何选择供应商？..."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
              rows={6}
              disabled={loading}
            />
          </div>
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 inline" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                正在生成答案...
              </>
            ) : (
              '提问'
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
              d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p className="text-sm">请在左侧输入问题，答案将显示在右侧</p>
        </div>
      </div>
    </div>
  );
}
