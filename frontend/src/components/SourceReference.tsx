import { useState } from 'react';
import type { SpecSource } from '../types';
import { refreshImageLink } from '../services/api';

interface SourceReferenceProps {
  reference: SpecSource;
  index?: number;
  showIndex?: boolean;
  variant?: 'inline' | 'card' | 'modal';
  onClose?: () => void;
  showDocName?: boolean; // 是否显示文档名称（默认true）
  compact?: boolean; // 紧凑模式，用于图片展示
}

/**
 * 图片展示组件
 */
function ImageDisplay({ 
  imageUrl, 
  alt, 
  className = '',
  onError,
  sliceId
}: { 
  imageUrl: string; 
  alt: string; 
  className?: string;
  onError?: (e: React.SyntheticEvent<HTMLImageElement, Event>) => void;
  sliceId?: string;
}) {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [currentImageUrl, setCurrentImageUrl] = useState(imageUrl);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleError = async (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    setIsLoading(false);
    
    // 检查是否是链接过期错误（403或AccessDenied）
    const img = e.currentTarget;
    const isExpired = img.src.includes('tos') || img.src.includes('volcengine');
    
    // 如果有sliceId且可能是链接过期，尝试刷新
    if (sliceId && isExpired && !isRefreshing) {
      setIsRefreshing(true);
      try {
        const newUrl = await refreshImageLink(sliceId);
        if (newUrl) {
          setCurrentImageUrl(newUrl);
          setIsLoading(true);
          setHasError(false);
          setIsRefreshing(false);
          return; // 使用新链接重新加载
        }
      } catch (error) {
        console.error('[ImageDisplay] 刷新图片链接失败:', error);
      }
      setIsRefreshing(false);
    }
    
    setHasError(true);
    if (onError) {
      onError(e);
    }
  };

  const handleLoad = () => {
    setIsLoading(false);
  };

  if (hasError && !isRefreshing) {
    return (
      <div className={`flex items-center justify-center p-4 bg-gray-100 rounded-lg border border-gray-200 ${className}`}>
        <div className="text-center">
          <svg className="w-8 h-8 mx-auto text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <p className="text-xs text-gray-500">图片加载失败</p>
          {sliceId && (
            <button
              onClick={async () => {
                setIsRefreshing(true);
                const newUrl = await refreshImageLink(sliceId);
                if (newUrl) {
                  setCurrentImageUrl(newUrl);
                  setIsLoading(true);
                  setHasError(false);
                }
                setIsRefreshing(false);
              }}
              className="text-xs text-blue-600 hover:text-blue-800 mt-1 inline-block"
            >
              {isRefreshing ? '正在刷新...' : '刷新链接'}
            </button>
          )}
          <a 
            href={currentImageUrl} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-xs text-blue-600 hover:text-blue-800 mt-1 ml-2 inline-block"
          >
            在新窗口打开链接
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded-lg">
          <div className="flex flex-col items-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="text-xs text-gray-500 mt-2">加载中...</p>
          </div>
        </div>
      )}
      <div className="relative group">
        {isRefreshing && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-100 bg-opacity-75 rounded-lg z-10">
            <div className="text-xs text-gray-600">正在刷新链接...</div>
          </div>
        )}
        <img
          src={currentImageUrl}
          alt={alt}
          className={`max-w-full h-auto rounded-lg border border-gray-200 shadow-sm transition-opacity ${
            isLoading ? 'opacity-0' : 'opacity-100'
          } ${isExpanded ? 'cursor-zoom-out' : 'cursor-zoom-in'}`}
          onError={handleError}
          onLoad={handleLoad}
          onClick={() => setIsExpanded(!isExpanded)}
        />
        {/* 悬停提示 */}
        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-10 rounded-lg transition-all flex items-center justify-center opacity-0 group-hover:opacity-100">
          <div className="bg-white bg-opacity-90 px-3 py-1 rounded text-xs text-gray-700">
            {isExpanded ? '点击缩小' : '点击放大'}
          </div>
        </div>
      </div>
      
      {/* 图片链接 */}
      <div className="mt-2 flex items-center gap-2">
        <a
          href={imageUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
          onClick={(e) => e.stopPropagation()}
        >
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
          在新窗口打开图片
        </a>
      </div>

      {/* 放大预览 */}
      {isExpanded && (
        <div
          className="fixed inset-0 z-[70] flex items-center justify-center bg-black bg-opacity-75 backdrop-blur-sm p-4"
          onClick={() => setIsExpanded(false)}
        >
          <div className="relative max-w-[90vw] max-h-[90vh]">
            <img
              src={currentImageUrl}
              alt={alt}
              className="max-w-full max-h-[90vh] rounded-lg shadow-2xl"
              onClick={(e) => e.stopPropagation()}
              onError={handleError}
            />
            <button
              onClick={() => setIsExpanded(false)}
              className="absolute top-4 right-4 p-2 bg-white bg-opacity-90 hover:bg-opacity-100 rounded-full shadow-lg transition-all"
            >
              <svg className="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * 通用的引用原文显示组件
 * 优化点：
 * 1. 隐藏slice_id（用户不关注）
 * 2. 保留文档名称
 * 3. 根据chunk_type选择最合适的内容格式
 * 4. 最小化清理：只移除特殊标记，保留内容结构
 */
export default function SourceReference({
  reference,
  index,
  showIndex = false,
  variant = 'card',
  onClose,
  showDocName = true,
  compact = false
}: SourceReferenceProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  /**
   * 提取KBImage标签内的内容
   */
  const extractKBImageInfo = (content: string): { hasImage: boolean; imageDescription?: string; cleanedContent: string } => {
    if (!content) return { hasImage: false, cleanedContent: '' };
    
    const imageRegex = /<KBImage>([\s\S]*?)<\/KBImage>/g;
    let match;
    let hasImage = false;
    let imageDescription: string | undefined;
    let cleanedContent = content;
    
    // 提取所有KBImage标签
    const matches: Array<{ full: string; description: string; index: number }> = [];
    while ((match = imageRegex.exec(content)) !== null) {
      matches.push({
        full: match[0],
        description: match[1].trim(),
        index: match.index
      });
      hasImage = true;
    }
    
    // 如果有多个KBImage，使用第一个的描述
    if (matches.length > 0) {
      imageDescription = matches[0].description;
      // 移除所有KBImage标签
      cleanedContent = content.replace(/<KBImage>[\s\S]*?<\/KBImage>/g, '');
    }
    
    // 移除其他特殊标记
    cleanedContent = cleanedContent
      .replace(/<KBTable>/g, '')
      .replace(/<\/KBTable>/g, '');
    
    // 清理多余空白，但保留基本结构
    cleanedContent = cleanedContent.replace(/\n{3,}/g, '\n\n');
    cleanedContent = cleanedContent.split('\n').map(line => line.trimEnd()).join('\n');
    
    return { hasImage, imageDescription, cleanedContent };
  };

  /**
   * 根据chunk_type选择最合适的内容格式
   */
  const getDisplayContent = (): string => {
    // 优先使用html_content（如果chunk_type是table或结构化数据）
    if (reference.chunk_type === 'table' && reference.html_content) {
      return reference.html_content;
    }
    
    // 如果有md_content，优先使用
    if (reference.md_content) {
      return reference.md_content;
    }
    
    // 如果有html_content，使用html_content
    if (reference.html_content) {
      return reference.html_content;
    }
    
    // 默认使用content
    return reference.content || '';
  };

  /**
   * 渲染内容：根据格式选择不同的渲染方式
   */
  const renderContent = () => {
    const displayContent = getDisplayContent();
    const { hasImage, imageDescription, cleanedContent } = extractKBImageInfo(displayContent);
    
    // 如果是HTML格式（表格等），使用dangerouslySetInnerHTML
    if (reference.chunk_type === 'table' && reference.html_content) {
      return (
        <div
          className="source-content-html"
          dangerouslySetInnerHTML={{ __html: cleanedContent }}
          style={{
            overflowX: 'auto',
            maxWidth: '100%'
          }}
        />
      );
    }
    
    // 如果是Markdown格式，可以在这里添加Markdown渲染
    // 目前先按文本处理
    if (reference.md_content) {
      return (
        <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
          {cleanedContent}
          {hasImage && imageDescription && !reference.image_url && (
            <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-700">
              <div className="font-medium mb-1">📷 图片说明：</div>
              <div>{imageDescription}</div>
            </div>
          )}
        </div>
      );
    }
    
    // 默认文本格式
    return (
      <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
        {cleanedContent}
        {hasImage && imageDescription && !reference.image_url && (
          <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-700">
            <div className="font-medium mb-1">📷 图片说明：</div>
            <div>{imageDescription}</div>
          </div>
        )}
      </div>
    );
  };

  // Inline变体：用于在答案中内联显示
  if (variant === 'inline') {
    return (
      <span className="relative inline-block">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className={`inline-flex items-center gap-1 px-2 py-0.5 mx-1 text-xs rounded transition-colors ${
            isExpanded 
              ? 'bg-blue-200 text-blue-800' 
              : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
          }`}
          title={reference.doc_name || '查看引用'}
        >
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
          {reference.doc_name ? `[${reference.doc_name}]` : '[引用]'}
        </button>
        {isExpanded && (
          <div className="absolute left-0 top-full z-20 mt-1 p-3 bg-white border border-gray-300 rounded-lg shadow-lg max-w-md max-h-96 overflow-y-auto">
            <div className="text-xs text-gray-500 mb-2 font-medium">
              {reference.doc_name || '引用内容'}
            </div>
            {reference.image_url ? (
              <div className="mb-3">
                <ImageDisplay
                  imageUrl={reference.image_url}
                  alt={reference.doc_name || "引用图片"}
                  sliceId={reference.slice_id}
                />
                {(() => {
                  const { hasImage: hasKBImage, imageDescription } = extractKBImageInfo(getDisplayContent());
                  return hasKBImage && imageDescription ? (
                    <div className="mt-2 text-xs text-gray-600 italic">
                      {imageDescription}
                    </div>
                  ) : null;
                })()}
              </div>
            ) : (() => {
              const { hasImage: hasKBImage, imageDescription } = extractKBImageInfo(getDisplayContent());
              return hasKBImage && imageDescription ? (
                <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="text-xs font-medium text-blue-700 mb-1">📷 图片说明</div>
                  <div className="text-sm text-gray-700">{imageDescription}</div>
                </div>
              ) : null;
            })()}
            <div className="text-sm text-gray-700">
              {renderContent()}
            </div>
            <button
              onClick={() => setIsExpanded(false)}
              className="mt-2 text-xs text-gray-500 hover:text-gray-700"
            >
              关闭
            </button>
          </div>
        )}
      </span>
    );
  }

  // Card变体：用于列表显示
  if (variant === 'card') {
    const displayContent = getDisplayContent();
    const { hasImage: hasKBImage, imageDescription } = extractKBImageInfo(displayContent);
    
    // 判断是否有图片（image_url 或 KBImage标签）
    const hasImage = reference.image_url || hasKBImage;
    
    // 如果是紧凑模式且只有图片，简化显示
    if (compact && hasImage && !displayContent) {
      return (
        <div>
          {reference.image_url ? (
            <ImageDisplay
              imageUrl={reference.image_url}
              alt={reference.doc_name || "知识库图片"}
              sliceId={reference.slice_id}
            />
          ) : hasKBImage && imageDescription ? (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="text-xs font-medium text-blue-700 mb-1">📷 图片说明</div>
              <div className="text-sm text-gray-700">{imageDescription}</div>
            </div>
          ) : null}
        </div>
      );
    }

    return (
      <div className={`${compact ? 'p-2' : 'p-4'} bg-white border border-gray-200 rounded-lg hover:border-blue-300 transition-colors shadow-sm`}>
        {showDocName && (
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-2">
              {showIndex && (
                <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-1 rounded">
                  #{index !== undefined ? index + 1 : ''}
                </span>
              )}
              {reference.doc_name && (
                <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded font-medium">
                  {reference.doc_name}
                </span>
              )}
            </div>
          </div>
        )}
        
        {/* 如果有image_url，优先显示图片 */}
        {reference.image_url ? (
          <div className={displayContent ? 'mb-3' : ''}>
            <ImageDisplay
              imageUrl={reference.image_url}
              alt={reference.doc_name || imageDescription || "知识库图片"}
              sliceId={reference.slice_id}
            />
            {/* 如果有KBImage说明，显示在图片下方 */}
            {hasKBImage && imageDescription && (
              <div className="mt-2 text-xs text-gray-600 italic">
                {imageDescription}
              </div>
            )}
          </div>
        ) : hasKBImage && imageDescription ? (
          // 如果没有image_url但有KBImage标签，显示说明
          <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="text-xs font-medium text-blue-700 mb-1">📷 图片说明</div>
            <div className="text-sm text-gray-700">{imageDescription}</div>
          </div>
        ) : null}
        
        {/* 如果有内容，显示内容 */}
        {displayContent && (
          <div className="text-sm text-gray-700 leading-relaxed">
            {renderContent()}
          </div>
        )}
      </div>
    );
  }

  // Modal变体：用于弹窗显示
  if (variant === 'modal') {
    return (
      <div
        className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      >
        <div
          className="bg-white p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto rounded-xl shadow-2xl border border-gray-200"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-gray-900">引用原文</h3>
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
            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
              <div className="space-y-3">
                <div>
                  <label className="text-xs text-gray-600 mb-1 block">文档名称</label>
                  <p className="text-gray-900 font-medium">{reference.doc_name || '未知'}</p>
                </div>
                {reference.image_url ? (
                  <div>
                    <label className="text-xs text-gray-600 mb-1 block">图片</label>
                    <div className="mb-3">
                      <ImageDisplay
                        imageUrl={reference.image_url}
                        alt={reference.doc_name || "知识库图片"}
                      />
                      {(() => {
                        const { hasImage: hasKBImage, imageDescription } = extractKBImageInfo(getDisplayContent());
                        return hasKBImage && imageDescription ? (
                          <div className="mt-2 text-xs text-gray-600 italic">
                            <div className="font-medium mb-1">图片说明：</div>
                            <div>{imageDescription}</div>
                          </div>
                        ) : null;
                      })()}
                    </div>
                  </div>
                ) : (() => {
                  const { hasImage: hasKBImage, imageDescription } = extractKBImageInfo(getDisplayContent());
                  return hasKBImage && imageDescription ? (
                    <div>
                      <label className="text-xs text-gray-600 mb-1 block">图片说明</label>
                      <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                        <div className="text-sm text-gray-700">{imageDescription}</div>
                      </div>
                    </div>
                  ) : null;
                })()}
                <div>
                  <label className="text-xs text-gray-600 mb-1 block">原文内容</label>
                  <div className="text-gray-900 text-sm bg-white p-3 rounded border border-gray-300 max-h-60 overflow-y-auto">
                    {renderContent()}
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex justify-end gap-2">
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg border border-gray-300 hover:bg-gray-200 transition-colors text-sm"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
}

