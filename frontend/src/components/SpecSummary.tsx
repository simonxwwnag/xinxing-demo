import { useState } from 'react';
import type React from 'react';
import type { SpecSource } from '../types';
import SourceReference from './SourceReference';

interface SpecSummaryProps {
  summary: string | null | undefined;
  references: SpecSource[];
  productName: string;
}

// Markdown解析后的节点类型
interface MarkdownNode {
  type: 'h1' | 'h2' | 'h3' | 'h4' | 'list' | 'listItem' | 'text' | 'bold' | 'reference';
  content: string;
  children?: MarkdownNode[];
  refId?: string;
  level?: number; // 用于标题级别
}

// 解析Markdown格式的文本
function parseMarkdown(text: string): MarkdownNode[] {
  const nodes: MarkdownNode[] = [];
  
  // 先处理引用标签，将其替换为占位符
  const referenceMap = new Map<string, string>();
  let refCounter = 0;
  const referenceRegex = /<reference\s+data-ref="([^"]+)"\s*><\/reference>/g;
  let processedText = text.replace(referenceRegex, (_match, refId) => {
    const placeholder = `__REF_${refCounter}__`;
    referenceMap.set(placeholder, refId);
    refCounter++;
    return placeholder;
  });
  
  const processedLines = processedText.split('\n');
  let currentList: MarkdownNode | null = null;
  
  for (let i = 0; i < processedLines.length; i++) {
    const line = processedLines[i].trim();
    
    if (!line) {
      if (currentList) {
        nodes.push(currentList);
        currentList = null;
      }
      continue;
    }
    
    // 解析标题
    const h4Match = line.match(/^####\s+(.+)$/);
    if (h4Match) {
      if (currentList) {
        nodes.push(currentList);
        currentList = null;
      }
      nodes.push({
        type: 'h4',
        content: h4Match[1],
        level: 4
      });
      continue;
    }
    
    const h3Match = line.match(/^###\s+(.+)$/);
    if (h3Match) {
      if (currentList) {
        nodes.push(currentList);
        currentList = null;
      }
      nodes.push({
        type: 'h3',
        content: h3Match[1],
        level: 3
      });
      continue;
    }
    
    const h2Match = line.match(/^##\s+(.+)$/);
    if (h2Match) {
      if (currentList) {
        nodes.push(currentList);
        currentList = null;
      }
      nodes.push({
        type: 'h2',
        content: h2Match[1],
        level: 2
      });
      continue;
    }
    
    const h1Match = line.match(/^#\s+(.+)$/);
    if (h1Match) {
      if (currentList) {
        nodes.push(currentList);
        currentList = null;
      }
      nodes.push({
        type: 'h1',
        content: h1Match[1],
        level: 1
      });
      continue;
    }
    
    // 解析列表项
    const listMatch = line.match(/^(\d+)\.\s+(.+)$/);
    if (listMatch) {
      if (!currentList) {
        currentList = {
          type: 'list',
          content: '',
          children: []
        };
      }
      
      const itemContent = parseInlineMarkdown(listMatch[2], referenceMap);
      currentList.children!.push({
        type: 'listItem',
        content: listMatch[1],
        children: itemContent
      });
      continue;
    }
    
    // 普通文本
    if (currentList) {
      nodes.push(currentList);
      currentList = null;
    }
    
    if (line) {
      const inlineNodes = parseInlineMarkdown(line, referenceMap);
      nodes.push({
        type: 'text',
        content: '',
        children: inlineNodes
      });
    }
  }
  
  if (currentList) {
    nodes.push(currentList);
  }
  
  return nodes;
}

// 解析行内Markdown（粗体、引用等）
function parseInlineMarkdown(text: string, referenceMap: Map<string, string>): MarkdownNode[] {
  const nodes: MarkdownNode[] = [];
  let lastIndex = 0;
  
  // 先处理引用占位符
  const refPlaceholderRegex = /__REF_(\d+)__/g;
  let match;
  
  while ((match = refPlaceholderRegex.exec(text)) !== null) {
    // 添加引用前的文本
    if (match.index > lastIndex) {
      const textBefore = text.substring(lastIndex, match.index);
      if (textBefore.trim()) {
        // 解析粗体
        const boldNodes = parseBold(textBefore);
        nodes.push(...boldNodes);
      }
    }
    
    // 添加引用
    const placeholder = match[0];
    const refId = referenceMap.get(placeholder);
    if (refId) {
      nodes.push({
        type: 'reference',
        content: '',
        refId: refId
      });
    }
    
    lastIndex = match.index + match[0].length;
  }
  
  // 添加剩余文本
  if (lastIndex < text.length) {
    const textAfter = text.substring(lastIndex);
    if (textAfter.trim()) {
      const boldNodes = parseBold(textAfter);
      nodes.push(...boldNodes);
    }
  }
  
  // 如果没有找到任何特殊格式，返回纯文本
  if (nodes.length === 0 && text.trim()) {
    const boldNodes = parseBold(text);
    return boldNodes.length > 0 ? boldNodes : [{ type: 'text', content: text }];
  }
  
  return nodes;
}

// 解析粗体文本
function parseBold(text: string): MarkdownNode[] {
  const nodes: MarkdownNode[] = [];
  const boldRegex = /\*\*(.+?)\*\*/g;
  let lastIndex = 0;
  let match;
  
  while ((match = boldRegex.exec(text)) !== null) {
    // 添加粗体前的文本
    if (match.index > lastIndex) {
      const textBefore = text.substring(lastIndex, match.index);
      if (textBefore.trim()) {
        nodes.push({ type: 'text', content: textBefore });
      }
    }
    
    // 添加粗体
    nodes.push({ type: 'bold', content: match[1] });
    
    lastIndex = match.index + match[0].length;
  }
  
  // 添加剩余文本
  if (lastIndex < text.length) {
    const textAfter = text.substring(lastIndex);
    if (textAfter.trim()) {
      nodes.push({ type: 'text', content: textAfter });
    }
  }
  
  // 如果没有粗体，返回整个文本
  if (nodes.length === 0) {
    return [{ type: 'text', content: text }];
  }
  
  return nodes;
}


// 解析illustration标签
function parseIllustrations(summary: string): { content: string; images: Array<{ refId: string; position: number }> } {
  const images: Array<{ refId: string; position: number }> = [];
  const illustrationRegex = /<illustration\s+data-ref="([^"]+)"\s*><\/illustration>/g;
  
  let match;
  while ((match = illustrationRegex.exec(summary)) !== null) {
    images.push({ refId: match[1], position: match.index });
  }
  
  // 移除illustration标签，保留纯文本
  const content = summary.replace(/<illustration\s+data-ref="[^"]+"\s*><\/illustration>/g, '');
  
  return { content, images };
}

export default function SpecSummary({ summary, references, productName }: SpecSummaryProps) {
  const [selectedRef, setSelectedRef] = useState<SpecSource | null>(null);
  
  // 如果没有引用也没有总结，显示空状态
  if ((!references || references.length === 0) && (!summary || !summary.trim())) {
    return (
      <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
        <p className="text-sm text-gray-500 text-center">
          没有找到"{productName}"的规格参数
        </p>
      </div>
    );
  }
  
  // 如果没有引用但有总结（可能是原始规格），继续显示总结内容
  
  // 根据slice_id查找对应的引用
  const findReferenceBySliceId = (sliceId: string): SpecSource | null => {
    return references.find(ref => ref.slice_id === sliceId) || null;
  };
  
  // 解析总结内容，提取引用标签和图片
  const { content: summaryContent, images: summaryImages } = summary 
    ? parseIllustrations(summary) 
    : { content: '', images: [] };
  
  // 使用Markdown解析
  const markdownNodes = summaryContent ? parseMarkdown(summaryContent) : [];
  
  // 渲染Markdown节点
  const renderMarkdownNode = (node: MarkdownNode, index: number, depth: number = 0): React.ReactNode => {
    switch (node.type) {
      case 'h1':
        return (
          <h1 key={index} className="text-2xl font-bold text-gray-900 mt-6 mb-4 pb-2 border-b-2 border-blue-300">
            {node.content}
          </h1>
        );
      case 'h2':
        return (
          <h2 key={index} className="text-xl font-bold text-gray-900 mt-5 mb-3 pb-1 border-b border-blue-200">
            {node.content}
          </h2>
        );
      case 'h3':
        return (
          <h3 key={index} className="text-lg font-semibold text-gray-800 mt-4 mb-2">
            {node.content}
          </h3>
        );
      case 'h4':
        return (
          <h4 key={index} className="text-base font-semibold text-gray-800 mt-3 mb-2 text-blue-700">
            {node.content}
          </h4>
        );
      case 'list':
        return (
          <ul key={index} className={`list-none space-y-2 ${depth > 0 ? 'ml-6' : ''}`}>
            {node.children?.map((child, childIndex) => renderMarkdownNode(child, childIndex, depth + 1))}
          </ul>
        );
      case 'listItem':
        return (
          <li key={index} className="flex items-start gap-2 py-1">
            <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center text-xs font-semibold text-blue-600 bg-blue-50 rounded-full border border-blue-200 mt-0.5">
              {node.content}
            </span>
            <div className="flex-1 text-sm text-gray-700 leading-relaxed">
              {node.children?.map((child, childIndex) => renderMarkdownNode(child, childIndex, depth + 1))}
            </div>
          </li>
        );
      case 'bold':
        return (
          <strong key={index} className="font-semibold text-gray-900">
            {node.content}
          </strong>
        );
      case 'reference':
        if (node.refId) {
          const ref = findReferenceBySliceId(node.refId);
          if (ref) {
            return (
              <button
                key={index}
                onClick={() => setSelectedRef(ref)}
                className="inline-flex items-center justify-center w-5 h-5 mx-1 text-xs font-semibold text-blue-600 bg-blue-100 border border-blue-300 rounded-full hover:bg-blue-200 hover:border-blue-400 transition-colors cursor-pointer align-middle"
                title={`点击查看来源：${ref.doc_name || '未知文档'}`}
              >
                {references.findIndex(r => r.slice_id === node.refId) + 1}
              </button>
            );
          }
        }
        return null;
      case 'text':
        if (node.children && node.children.length > 0) {
          return (
            <span key={index}>
              {node.children.map((child, childIndex) => renderMarkdownNode(child, childIndex, depth))}
            </span>
          );
        }
        return <span key={index}>{node.content}</span>;
      default:
        return null;
    }
  };
  
  return (
    <div className="space-y-4">
      {/* 规格参数总结内容 - 结构化展示 */}
      {summary && markdownNodes.length > 0 && (
        <div className="p-5 bg-white border border-blue-200 rounded-lg shadow-sm">
          <div className="prose prose-sm max-w-none">
            {markdownNodes.map((node, index) => renderMarkdownNode(node, index))}
          </div>
          
          {/* 显示总结中的图片 */}
          {summaryImages.length > 0 && (
            <div className="mt-4 space-y-3">
              {summaryImages.map((img, index) => {
                const ref = findReferenceBySliceId(img.refId);
                if (ref && ref.image_url) {
                  return (
                    <div key={index} className="border border-gray-200 rounded-lg p-3 bg-gray-50">
                      {ref.doc_name && (
                        <div className="text-xs text-gray-600 mb-2 font-medium">
                          {ref.doc_name}
                        </div>
                      )}
                      <SourceReference
                        reference={ref}
                        variant="card"
                        showDocName={false}
                        compact={true}
                      />
                    </div>
                  );
                }
                return null;
              })}
            </div>
          )}
        </div>
      )}
      
      {/* 如果没有总结或总结为空，但有references，显示原始chunk内容列表 */}
      {(!summary || markdownNodes.length === 0) && references && references.length > 0 && (
        <div className="space-y-3">
          {references.map((ref, index) => (
            <div key={ref.slice_id || index}>
              <SourceReference
                reference={ref}
                index={index}
                showIndex={true}
                variant="card"
              />
            </div>
          ))}
        </div>
      )}
      
      {/* 如果有总结但markdown解析失败，直接显示原始文本 */}
      {summary && markdownNodes.length === 0 && (
        <div className="p-5 bg-white border border-blue-200 rounded-lg shadow-sm">
          <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
            {summary}
          </div>
        </div>
      )}
      
      {/* 引用原文弹窗 */}
      {selectedRef && (
        <SourceReference
          reference={selectedRef}
          variant="modal"
          onClose={() => setSelectedRef(null)}
        />
      )}
    </div>
  );
}

