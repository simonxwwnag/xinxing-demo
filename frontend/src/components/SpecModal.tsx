import { useEffect, useState } from 'react';
import type { SpecSource } from '../types';

interface SpecModalProps {
  specs: SpecSource[];
  onClose: () => void;
}

// 解析表格内容，尝试转换为结构化数据
function parseTableContent(tableContent: string): { type: 'table' | 'text'; data?: any; text: string } {
  const cleaned = tableContent.trim();
  
  // 尝试解析表格格式（包含表头和数据行）
  const lines = cleaned.split('\n').filter(line => line.trim());
  
  // 检查是否包含表格结构（包含多个列分隔符或表头）
  const hasTableStructure = lines.some(line => {
    // 检查是否包含多个制表符、多个空格分隔的列，或者包含表头标记
    return line.includes('\t') || 
           line.split(/\s{2,}/).length > 2 || 
           line.includes('|') ||
           (line.includes('：') && line.length < 100);
  });
  
  if (hasTableStructure && lines.length > 1) {
    // 尝试解析为表格
    const tableData: string[][] = [];
    lines.forEach(line => {
      // 尝试多种分隔符
      let cells: string[] = [];
      if (line.includes('\t')) {
        cells = line.split('\t').map(c => c.trim()).filter(c => c);
      } else if (line.includes('|')) {
        cells = line.split('|').map(c => c.trim()).filter(c => c);
      } else {
        // 尝试按多个空格分割
        cells = line.split(/\s{2,}/).map(c => c.trim()).filter(c => c);
      }
      if (cells.length > 0) {
        tableData.push(cells);
      }
    });
    
    if (tableData.length > 0 && tableData[0].length > 1) {
      return { type: 'table', data: tableData, text: cleaned };
    }
  }
  
  return { type: 'text', text: cleaned };
}

// 格式化知识库内容，处理KBTable、KBImage等标签
interface FormattedContent {
  type: 'text' | 'table' | 'image';
  content: string;
  tableData?: string[][];
}

function formatSpecContent(content: string): FormattedContent[] {
  if (!content) return [];
  
  const parts: FormattedContent[] = [];
  let remaining = content;
  
  // 处理KBTable标签
  const tableRegex = /<KBTable>\[([\s\S]*?)\]<\/KBTable>/g;
  let lastIndex = 0;
  let match;
  
  while ((match = tableRegex.exec(content)) !== null) {
    // 添加表格前的文本
    if (match.index > lastIndex) {
      const textBefore = content.substring(lastIndex, match.index).trim();
      if (textBefore) {
        parts.push({ type: 'text', content: textBefore });
      }
    }
    
    // 解析表格内容
    const tableResult = parseTableContent(match[1]);
    if (tableResult.type === 'table' && tableResult.data) {
      parts.push({ type: 'table', content: '', tableData: tableResult.data });
    } else {
      parts.push({ type: 'text', content: `【表格内容】\n${tableResult.text}` });
    }
    
    lastIndex = match.index + match[0].length;
  }
  
  // 添加剩余文本
  if (lastIndex < content.length) {
    remaining = content.substring(lastIndex);
  } else if (parts.length === 0) {
    // 如果没有找到任何表格，使用全部内容
    remaining = content;
  }
  
  // 处理KBImage标签
  const imageRegex = /<KBImage>([\s\S]*?)<\/KBImage>/g;
  let imageLastIndex = 0;
  let imageMatch;
  
  const processedParts: FormattedContent[] = [];
  
  // 处理所有部分（包括表格和剩余文本）
  const allParts = parts.length > 0 
    ? [...parts, ...(remaining ? [{ type: 'text' as const, content: remaining }] : [])]
    : [{ type: 'text' as const, content: remaining }];
  
  for (const part of allParts) {
    if (part.type === 'text') {
      const text = part.content;
      imageLastIndex = 0;
      
      while ((imageMatch = imageRegex.exec(text)) !== null) {
        // 添加图片前的文本
        if (imageMatch.index > imageLastIndex) {
          const textBefore = text.substring(imageLastIndex, imageMatch.index).trim();
          if (textBefore) {
            processedParts.push({ type: 'text', content: textBefore });
          }
        }
        
        // 添加图片
        processedParts.push({ 
          type: 'image', 
          content: imageMatch[1].trim() 
        });
        
        imageLastIndex = imageMatch.index + imageMatch[0].length;
      }
      
      // 添加剩余文本
      if (imageLastIndex < text.length) {
        const textAfter = text.substring(imageLastIndex).trim();
        if (textAfter) {
          processedParts.push({ type: 'text', content: textAfter });
        }
      }
    } else {
      processedParts.push(part);
    }
  }
  
  // 如果没有处理任何内容，返回原始文本
  if (processedParts.length === 0) {
    return [{ type: 'text', content: content.trim() }];
  }
  
  return processedParts;
}

export default function SpecModal({ specs, onClose }: SpecModalProps) {
  const [selectedSlice, setSelectedSlice] = useState<SpecSource | null>(null);
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={handleBackdropClick}
    >
      <div className="bg-white p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto rounded-xl shadow-2xl border border-gray-200">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold gradient-text">知识库匹配规格汇总</h2>
            <p className="text-sm text-gray-600 mt-1">来自知识库的相关规格信息，包含切片来源</p>
          </div>
          <button
            onClick={onClose}
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
          {specs.map((spec, index) => (
            <div
              key={index}
              className="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-blue-400 transition-all"
            >
              <div className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center text-xs font-bold text-white">
                  {index + 1}
                </span>
                <div className="flex-1">
                  {/* 如果有图片链接，先显示图片 */}
                  {spec.image_url && (
                    <div className="mb-4">
                      <img 
                        src={spec.image_url} 
                        alt={spec.doc_name || "知识库图片"}
                        className="max-w-full h-auto rounded-lg border border-gray-300 shadow-md"
                        onError={(e) => {
                          // 图片加载失败时的处理
                          const target = e.currentTarget;
                          target.style.display = 'none';
                          console.error('图片加载失败:', spec.image_url);
                        }}
                      />
                    </div>
                  )}
                  
                  <div className="text-gray-900 mb-3 leading-relaxed">
                    {formatSpecContent(spec.content).map((part, idx) => {
                      if (part.type === 'table' && part.tableData) {
                        // 渲染表格
                        return (
                          <div key={idx} className="my-4 overflow-x-auto">
                            <div className="inline-block min-w-full">
                              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                                <div className="text-blue-700 text-xs font-medium mb-2 flex items-center gap-2">
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                  </svg>
                                  表格内容
                                </div>
                                <table className="min-w-full text-sm">
                                  <tbody>
                                    {part.tableData.map((row, rowIdx) => (
                                      <tr 
                                        key={rowIdx} 
                                        className={rowIdx === 0 ? 'bg-blue-100 font-medium' : 'border-t border-blue-200'}
                                      >
                                        {row.map((cell, cellIdx) => (
                                          <td 
                                            key={cellIdx} 
                                            className={`px-3 py-2 ${rowIdx === 0 ? 'text-blue-900' : 'text-gray-700'}`}
                                          >
                                            {cell}
                                          </td>
                                        ))}
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            </div>
                          </div>
                        );
                      } else if (part.type === 'image') {
                        // 渲染图片占位符
                        return (
                          <div key={idx} className="my-4 p-4 bg-purple-50 border border-purple-200 rounded-lg">
                            <div className="flex items-start gap-3">
                              <div className="flex-shrink-0 w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                </svg>
                              </div>
                              <div className="flex-1">
                                <div className="text-purple-700 text-xs font-medium mb-1">图片说明</div>
                                <div className="text-gray-700 text-sm whitespace-pre-wrap">{part.content}</div>
                              </div>
                            </div>
                          </div>
                        );
                      } else {
                        // 渲染文本内容
                        return (
                          <div key={idx} className="mb-2 whitespace-pre-wrap">
                            {part.content.split('\n').map((line, lineIdx) => {
                              const trimmed = line.trim();
                              // 处理加粗文本（标题行）
                              if (trimmed.includes('：') && trimmed.length < 50 && !trimmed.includes('。')) {
                                return (
                                  <div key={lineIdx} className="font-semibold text-blue-700 my-2">
                                    {trimmed}
                                  </div>
                                );
                              }
                              if (trimmed) {
                                return <div key={lineIdx} className="mb-1">{line}</div>;
                              }
                              return <br key={lineIdx} />;
                            })}
                          </div>
                        );
                      }
                    })}
                  </div>
                  <div className="flex flex-wrap gap-2 mt-3">
                    {spec.doc_name && (
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs border border-blue-300 flex items-center gap-1">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        知识库文档: {spec.doc_name}
                      </span>
                    )}
                    <button
                      onClick={() => setSelectedSlice(spec)}
                      className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs border border-purple-300 hover:bg-purple-200 transition-colors flex items-center gap-1"
                    >
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      查看切片来源
                    </button>
                    {spec.slice_id && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs border border-gray-300">
                        ID: {spec.slice_id.slice(0, 8)}...
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 切片详情弹窗 */}
      {selectedSlice && (
        <div
          className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={() => setSelectedSlice(null)}
        >
          <div
            className="bg-white p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto rounded-xl shadow-2xl border border-gray-200"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold gradient-text">切片来源详情</h3>
              <button
                onClick={() => setSelectedSlice(null)}
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
              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="space-y-3">
                  <div>
                    <label className="text-xs text-gray-600 mb-1 block">文档名称</label>
                    <p className="text-gray-900 font-medium">{selectedSlice.doc_name || '未知'}</p>
                  </div>
                  <div>
                    <label className="text-xs text-gray-600 mb-1 block">文档ID</label>
                    <p className="text-gray-700 text-sm font-mono break-all">{selectedSlice.doc_id}</p>
                  </div>
                  <div>
                    <label className="text-xs text-gray-600 mb-1 block">切片ID</label>
                    <p className="text-gray-700 text-sm font-mono break-all">{selectedSlice.slice_id}</p>
                  </div>
                  {/* 如果有图片链接，显示图片 */}
                  {selectedSlice.image_url && (
                    <div>
                      <label className="text-xs text-gray-600 mb-1 block">图片</label>
                      <div className="mb-3">
                        <img 
                          src={selectedSlice.image_url} 
                          alt={selectedSlice.doc_name || "知识库图片"}
                          className="max-w-full h-auto rounded-lg border border-gray-300 shadow-md"
                          onError={(e) => {
                            const target = e.currentTarget;
                            target.style.display = 'none';
                            console.error('图片加载失败:', selectedSlice.image_url);
                          }}
                        />
                      </div>
                    </div>
                  )}
                  
                  <div>
                    <label className="text-xs text-gray-600 mb-1 block">切片内容</label>
                    <div className="text-gray-900 text-sm bg-white p-3 rounded border border-gray-300 max-h-60 overflow-y-auto">
                      {formatSpecContent(selectedSlice.content).map((part, idx) => {
                        if (part.type === 'table' && part.tableData) {
                          return (
                            <div key={idx} className="my-2 overflow-x-auto">
                              <table className="min-w-full text-xs">
                                <tbody>
                                  {part.tableData.map((row, rowIdx) => (
                                    <tr key={rowIdx} className={rowIdx === 0 ? 'bg-blue-100' : 'border-t border-gray-200'}>
                                      {row.map((cell, cellIdx) => (
                                        <td key={cellIdx} className="px-2 py-1">{cell}</td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          );
                        } else if (part.type === 'image') {
                          return (
                            <div key={idx} className="my-2 p-2 bg-purple-50 border border-purple-200 rounded text-xs italic">
                              📷 {part.content}
                            </div>
                          );
                        } else {
                          return (
                            <div key={idx} className="whitespace-pre-wrap mb-1">{part.content}</div>
                          );
                        }
                      })}
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-2">
                <button
                  onClick={() => {
                    // 复制切片ID到剪贴板
                    navigator.clipboard.writeText(selectedSlice.slice_id);
                    alert('切片ID已复制到剪贴板');
                  }}
                  className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg border border-blue-300 hover:bg-blue-200 transition-colors text-sm"
                >
                  复制切片ID
                </button>
                <button
                  onClick={() => setSelectedSlice(null)}
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

