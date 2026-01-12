import { useState } from 'react';
import SourceReference from './SourceReference';
import type { SpecSource } from '../types';

interface KnowledgeQAResultProps {
  result: {
    question: string;
    answer: string;
    references: SpecSource[];
  } | null;
}

interface ParsedPersonnelInfo {
  name: string;
  department?: string;
  category?: string;
  certificate_name?: string;
  certificate_number?: string;
  issue_date?: string;
  expiry_date?: string;
  referenceIds?: string[];
}

export default function KnowledgeQAResult({ result }: KnowledgeQAResultProps) {
  const [expandedRefs, setExpandedRefs] = useState<Set<string>>(new Set());

  // 解析答案中的人员信息
  const parsePersonnelFromAnswer = (answer: string): ParsedPersonnelInfo[] => {
    const personnelList: ParsedPersonnelInfo[] = [];
    const referencePattern = /<reference\s+data-ref="([^"]+)"[^>]*><\/reference>/g;
    
    // 按段落分割（空行分隔）
    const sections = answer.split(/\n\s*\n/);
    
    for (const section of sections) {
      const lines = section.split('\n').map(l => l.trim()).filter(l => l);
      if (lines.length === 0) continue;
      
      // 尝试匹配人员信息块
      // 格式1: **姓名 (Name):** 或 **姓名：**
      // 格式2: 姓名： 或 姓名:
      const firstLine = lines[0];
      let nameMatch = firstLine.match(/^\*\*([^*]+?)\*\*[：:]/);
      if (!nameMatch) {
        nameMatch = firstLine.match(/^\*\*([^*]+?)\*\*$/);
      }
      if (!nameMatch) {
        nameMatch = firstLine.match(/^([^\n：:]+?)[：:]/);
      }
      
      // 如果第一行看起来像姓名（不包含常见字段名，长度合理）
      if (nameMatch) {
        const potentialName = nameMatch[1].trim();
        // 移除可能的英文名和括号
        const cleanName = potentialName.replace(/\s*\([^)]+\)\s*$/, '').trim();
        
        // 检查是否是有效的姓名（不是字段名）
        const fieldNames = ['部门', '类别', '证书名称', '证书编号', '发证日期', '到期日期', '有效期', '关于'];
        const isFieldName = fieldNames.some(field => cleanName.includes(field));
        
        if (cleanName.length > 0 && cleanName.length < 20 && !isFieldName) {
          const person: ParsedPersonnelInfo = {
            name: cleanName,
            referenceIds: []
          };
          
          // 解析后续行的信息
          for (let i = 1; i < lines.length; i++) {
            const line = lines[i];
            
            // 提取部门
            const deptMatch = line.match(/^部门[：:]\s*(.+)$/);
            if (deptMatch) {
              person.department = deptMatch[1].trim();
              continue;
            }
            
            // 提取类别
            const catMatch = line.match(/^类别[：:]\s*(.+)$/);
            if (catMatch) {
              person.category = catMatch[1].trim();
              continue;
            }
            
            // 提取证书名称
            const certNameMatch = line.match(/^证书名称[：:]\s*(.+)$/);
            if (certNameMatch) {
              person.certificate_name = certNameMatch[1].trim();
              continue;
            }
            
            // 提取证书编号
            const certNumMatch = line.match(/^证书编号[：:]\s*(.+)$/);
            if (certNumMatch) {
              person.certificate_number = certNumMatch[1].trim();
              continue;
            }
            
            // 提取发证日期
            const issueMatch = line.match(/^发证日期[：:]\s*(.+)$/);
            if (issueMatch) {
              person.issue_date = issueMatch[1].trim();
              continue;
            }
            
            // 提取到期日期
            const expiryMatch = line.match(/^(?:到期日期|有效期至)[：:]\s*(.+)$/);
            if (expiryMatch) {
              person.expiry_date = expiryMatch[1].trim();
              continue;
            }
            
            // 提取引用ID
            let refMatch;
            const lineCopy = line;
            while ((refMatch = referencePattern.exec(lineCopy)) !== null) {
              if (person.referenceIds && !person.referenceIds.includes(refMatch[1])) {
                person.referenceIds.push(refMatch[1]);
              }
            }
          }
          
          // 如果提取到了有效信息，添加到列表
          if (person.name && (person.department || person.category || person.certificate_name)) {
            personnelList.push(person);
          }
        }
      }
    }
    
    // 如果没有找到结构化信息，尝试更宽松的匹配
    if (personnelList.length === 0) {
      // 尝试匹配列表格式：* 姓名：部门：xxx 类别：xxx
      const listPattern = /[•\*\-\d+]\s*([^\n：:]+?)[：:]\s*([^\n]+)/g;
      let match;
      const seenNames = new Set<string>();
      
      while ((match = listPattern.exec(answer)) !== null) {
        const name = match[1].trim();
        const rest = match[2].trim();
        
        if (name.length > 0 && name.length < 15 && !seenNames.has(name)) {
          seenNames.add(name);
          
          const person: ParsedPersonnelInfo = {
            name: name,
            referenceIds: []
          };
          
          // 从rest中提取信息
          const deptMatch = rest.match(/部门[：:]\s*([^\n，,]+)/);
          if (deptMatch) person.department = deptMatch[1].trim();
          
          const catMatch = rest.match(/类别[：:]\s*([^\n，,]+)/);
          if (catMatch) person.category = catMatch[1].trim();
          
          if (person.department || person.category) {
            personnelList.push(person);
          }
        }
      }
    }
    
    return personnelList;
  };

  // 处理答案文本，提取reference标签并创建可点击的引用
  const processAnswerText = (answer: string) => {
    // 提取所有reference标签和illustration标签
    const referencePattern = /<reference\s+data-ref="([^"]+)"[^>]*><\/reference>/g;
    const illustrationPattern = /<illustration\s+data-ref="([^"]+)"[^>]*><\/illustration>/g;
    const parts: Array<{ type: 'text' | 'reference' | 'illustration'; content: string; refId?: string }> = [];
    let lastIndex = 0;
    
    // 收集所有标签位置
    const tags: Array<{ index: number; type: 'reference' | 'illustration'; refId: string; length: number }> = [];
    
    let match;
    while ((match = referencePattern.exec(answer)) !== null) {
      tags.push({
        index: match.index,
        type: 'reference',
        refId: match[1],
        length: match[0].length
      });
    }
    
    while ((match = illustrationPattern.exec(answer)) !== null) {
      tags.push({
        index: match.index,
        type: 'illustration',
        refId: match[1],
        length: match[0].length
      });
    }
    
    // 按位置排序
    tags.sort((a, b) => a.index - b.index);
    
    // 构建parts数组
    for (const tag of tags) {
      // 添加标签前的文本
      if (tag.index > lastIndex) {
        const textContent = answer.substring(lastIndex, tag.index).trim();
        if (textContent) {
          parts.push({
            type: 'text',
            content: textContent
          });
        }
      }
      
      // 添加标签
      parts.push({
        type: tag.type,
        content: '',
        refId: tag.refId
      });
      
      lastIndex = tag.index + tag.length;
    }
    
    // 添加剩余文本
    if (lastIndex < answer.length) {
      const remainingText = answer.substring(lastIndex).trim();
      if (remainingText) {
        parts.push({
          type: 'text',
          content: remainingText
        });
      }
    }
    
    return parts.length > 0 ? parts : [{ type: 'text', content: answer }];
  };

  // 根据refId查找对应的reference
  const findReferenceById = (refId: string) => {
    return result?.references.find(ref => 
      ref.slice_id === refId || 
      ref.slice_id.endsWith(refId) || 
      refId.endsWith(ref.slice_id)
    );
  };

  const toggleReference = (refId: string) => {
    const newExpanded = new Set(expandedRefs);
    if (newExpanded.has(refId)) {
      newExpanded.delete(refId);
    } else {
      newExpanded.add(refId);
    }
    setExpandedRefs(newExpanded);
  };

  if (!result) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        <div className="text-center">
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
          <p>请在左侧输入问题进行查询</p>
        </div>
      </div>
    );
  }

  // 解析答案中的人员信息
  const personnelList = parsePersonnelFromAnswer(result.answer);
  const answerParts = processAnswerText(result.answer);
  
  // 判断是否应该显示结构化的人员列表
  const shouldShowPersonnelList = personnelList.length > 0 && personnelList.length <= 20;

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="p-6 border-b border-gray-200 bg-white">
        <h2 className="text-xl font-semibold text-gray-900">问答结果</h2>
      </div>
      
      <div className="flex-1 overflow-y-auto p-6">
        <div className="space-y-6">
          {/* 问题 */}
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2">问题</h3>
            <p className="text-gray-900 text-lg">{result.question}</p>
          </div>

          {/* 结构化人员列表 */}
          {shouldShowPersonnelList && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-3">
                匹配结果 ({personnelList.length}人)
              </h3>
              <div className="space-y-4">
                {personnelList.map((personnel, index) => {
                  // 查找相关的references
                  const relatedRefs = personnel.referenceIds
                    ?.map(refId => findReferenceById(refId))
                    .filter(Boolean) || [];
                  
                  return (
                    <div
                      key={index}
                      className="p-5 bg-white border border-gray-200 rounded-lg hover:border-blue-300 transition-colors shadow-sm"
                    >
                      <div className="flex items-start gap-4">
                        <div className="flex-1">
                          <h4 className="text-lg font-semibold text-gray-900 mb-3">
                            {personnel.name}
                          </h4>
                          <div className="grid grid-cols-2 gap-3 text-sm">
                            {personnel.department && (
                              <div>
                                <span className="text-gray-500">部门：</span>
                                <span className="text-gray-900 font-medium">{personnel.department}</span>
                              </div>
                            )}
                            {personnel.category && (
                              <div>
                                <span className="text-gray-500">类别：</span>
                                <span className="text-gray-900 font-medium">{personnel.category}</span>
                              </div>
                            )}
                            {personnel.certificate_name && (
                              <div>
                                <span className="text-gray-500">证书名称：</span>
                                <span className="text-gray-900 font-medium">{personnel.certificate_name}</span>
                              </div>
                            )}
                            {personnel.certificate_number && (
                              <div>
                                <span className="text-gray-500">证书编号：</span>
                                <span className="text-gray-900 font-mono text-xs">{personnel.certificate_number}</span>
                              </div>
                            )}
                            {personnel.issue_date && (
                              <div>
                                <span className="text-gray-500">发证日期：</span>
                                <span className="text-gray-900">{personnel.issue_date}</span>
                              </div>
                            )}
                            {personnel.expiry_date && (
                              <div>
                                <span className="text-gray-500">到期日期：</span>
                                <span className="text-gray-900">{personnel.expiry_date}</span>
                              </div>
                            )}
                          </div>
                          
                          {/* 相关引用 */}
                          {relatedRefs.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-gray-200">
                              <div className="flex flex-wrap gap-2">
                                {relatedRefs.map((ref, refIdx) => (
                                  <button
                                    key={refIdx}
                                    onClick={() => ref && toggleReference(ref.slice_id)}
                                    className="text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded hover:bg-blue-100 transition-colors"
                                  >
                                    {ref?.doc_name || `引用 ${refIdx + 1}`}
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 专家答案 */}
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-3">专家答案</h3>
            <div className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg shadow-sm">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <div className="text-gray-900 leading-relaxed whitespace-pre-wrap text-base">
                    {answerParts.map((part, idx) => {
                      if (part.type === 'reference' && 'refId' in part && part.refId) {
                        const refId = part.refId;
                        const ref = findReferenceById(refId);
                        if (!ref) return null;
                        
                        return (
                          <SourceReference
                            key={idx}
                            reference={ref}
                            variant="inline"
                          />
                        );
                      }
                      
                      if (part.type === 'illustration' && 'refId' in part && part.refId) {
                        const refId = part.refId;
                        const ref = findReferenceById(refId);
                        if (ref && ref.image_url) {
                          return (
                            <div key={idx} className="my-4">
                              <SourceReference
                                reference={ref}
                                variant="card"
                              />
                            </div>
                          );
                        }
                        return null;
                      }
                      
                      return <span key={idx}>{part.content}</span>;
                    })}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 知识库参考 */}
          {result.references.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-3">
                知识库参考 ({result.references.length}条)
              </h3>
              <div className="space-y-3">
                {result.references.map((ref, index) => (
                  <SourceReference
                    key={ref.slice_id || index}
                    reference={ref}
                    index={index}
                    showIndex={false}
                    variant="card"
                  />
                ))}
              </div>
            </div>
          )}

          {result.references.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <p>未找到相关参考内容</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

