import { useState, useEffect } from 'react';
import type { CertificatePersonnelResultData } from '../types';
import { matchCertificates, type CertificateFile } from '../services/api';
import SourceReference from './SourceReference';

interface CertificatePersonnelResultProps {
  result: CertificatePersonnelResultData | null;
}

export default function CertificatePersonnelResult({ result }: CertificatePersonnelResultProps) {
  const [certificateMap, setCertificateMap] = useState<Map<string, CertificateFile[]>>(new Map());
  const [loadingCertificates, setLoadingCertificates] = useState(false);

  // 当结果更新时，加载证书文件
  useEffect(() => {
    if (result && result.personnel_list && result.personnel_list.length > 0) {
      console.log('[证书人员查询] 结果更新，开始加载证书文件', {
        personnelCount: result.personnel_list.length,
        names: result.personnel_list.map(p => p.name).filter(Boolean)
      });
      loadCertificates();
    } else {
      // 清空证书映射
      setCertificateMap(new Map());
      setLoadingCertificates(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result]);

  const loadCertificates = async () => {
    if (!result) return;
    
    setLoadingCertificates(true);
    try {
      // 提取所有人员姓名
      const names = result.personnel_list
        .map(p => p.name)
        .filter((name): name is string => !!name && name.trim() !== '');
      
      console.log('[证书人员查询] 提取的人员姓名:', names);
      
      if (names.length > 0) {
        const certificates = await matchCertificates(names);
        console.log('[证书人员查询] 匹配到的证书文件:', certificates);
        
        // 按姓名分组
        const map = new Map<string, CertificateFile[]>();
        certificates.forEach(cert => {
          const existing = map.get(cert.name) || [];
          existing.push(cert);
          map.set(cert.name, existing);
        });
        
        console.log('[证书人员查询] 证书映射:', Array.from(map.entries()));
        setCertificateMap(map);
      } else {
        console.warn('[证书人员查询] 未找到有效的人员姓名');
      }
    } catch (error) {
      console.error('加载证书文件失败:', error);
    } finally {
      setLoadingCertificates(false);
    }
  };

  // 将相对路径转换为完整URL
  const getFullFileUrl = (fileUrl: string): string => {
    if (!fileUrl) return '';
    
    // 如果已经是完整URL，直接返回
    if (fileUrl.startsWith('http://') || fileUrl.startsWith('https://') || fileUrl.startsWith('data:')) {
      return fileUrl;
    }
    
    // 如果是相对路径，添加基础URL
    if (fileUrl.startsWith('/')) {
      return `${window.location.origin}${fileUrl}`;
    }
    
    // 否则添加 /api 前缀
    return `${window.location.origin}/api${fileUrl}`;
  };

  const handleDownload = (cert: CertificateFile) => {
    try {
      const fileUrl = getFullFileUrl(cert.file_url);
      
      // 使用 fetch 下载文件
      fetch(fileUrl)
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.blob();
        })
        .then(blob => {
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = cert.file_name;
          link.style.display = 'none';
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
        })
        .catch(error => {
          console.error('下载文件失败:', error);
          // 如果下载失败，尝试直接打开
          window.open(fileUrl, '_blank');
        });
    } catch (error) {
      console.error('下载文件失败:', error);
      // 如果下载失败，尝试直接打开
      const fileUrl = getFullFileUrl(cert.file_url);
      window.open(fileUrl, '_blank');
    }
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
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <p>请在左侧输入查询条件进行查询</p>
        </div>
      </div>
    );
  }

  // 尝试从content中解析人员信息
  const parsePersonnelInfo = (content: string | undefined) => {
    const info: Record<string, string> = {};
    
    // 如果content为空或未定义，直接返回空对象
    if (!content || typeof content !== 'string') {
      return info;
    }
    
    // 尝试提取常见字段
    const patterns: Record<string, RegExp> = {
      name: /姓名[：:]\s*([^\n\r]+)/i,
      department: /部门[：:]\s*([^\n\r]+)/i,
      category: /类别[：:]\s*([^\n\r]+)/i,
      certificate_name: /证书名称[：:]\s*([^\n\r]+)/i,
      certificate_number: /证书编号[：:]\s*([^\n\r]+)/i,
      issue_date: /发证日期[：:]\s*([^\n\r]+)/i,
      expiry_date: /到期日期[：:]\s*([^\n\r]+)|有效期[至到][：:]\s*([^\n\r]+)/i,
      free_status: /空闲状态[：:]\s*([^\n\r]+)/i,
    };

    for (const [key, pattern] of Object.entries(patterns)) {
      const match = content.match(pattern);
      if (match) {
        info[key] = match[1] || match[2] || '';
      }
    }

    return info;
  };


  // 如果没有结果，显示提示
  if (!result) {
    return (
      <div className="h-full flex flex-col overflow-hidden">
        <div className="p-6 border-b border-gray-200 bg-white">
          <h2 className="text-xl font-semibold text-gray-900">查询结果</h2>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <p className="text-gray-500">暂无查询结果</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="p-6 border-b border-gray-200 bg-white">
        <h2 className="text-xl font-semibold text-gray-900">查询结果</h2>
      </div>
      
      <div className="flex-1 overflow-y-auto p-6">
        <div className="space-y-6">
          {/* 查询问题 */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">查询问题</h3>
            <p className="text-gray-900 text-lg">{result.question || '无'}</p>
          </div>

          {/* 人员列表 */}
          {result.personnel_list && Array.isArray(result.personnel_list) && result.personnel_list.length > 0 ? (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-3">
                匹配人员 ({result.personnel_list.length}人)
              </h3>
              <div className="space-y-4">
                {result.personnel_list.map((personnel, index) => {
                  // 优先使用结构化的字段，如果不存在则尝试从content中解析
                  const parsedInfo = personnel.content ? parsePersonnelInfo(personnel.content) : {};
                  
                  // 格式化日期，移除时间部分
                  const formatDate = (dateStr: string | undefined) => {
                    if (!dateStr) return '';
                    // 移除时间部分，只保留日期
                    return dateStr.split(' ')[0].split('T')[0];
                  };
                  
                  const displayInfo = {
                    name: personnel.name || parsedInfo.name || '',
                    department: personnel.department || parsedInfo.department || '',
                    category: personnel.category || parsedInfo.category || '',
                    certificate_name: personnel.certificate_name || parsedInfo.certificate_name || '',
                    certificate_number: personnel.certificate_number || parsedInfo.certificate_number || '',
                    issue_date: formatDate(personnel.issue_date || parsedInfo.issue_date),
                    expiry_date: formatDate(personnel.expiry_date || parsedInfo.expiry_date),
                    free_status: personnel.free_status || parsedInfo.free_status || '',
                  };
                  
                  const personName = displayInfo.name || `人员 ${index + 1}`;
                  // 尝试多种方式匹配证书（去除空格、全角半角等）
                  const nameVariants = [
                    displayInfo.name,
                    displayInfo.name?.trim(),
                    displayInfo.name?.replace(/\s+/g, ''),
                    displayInfo.name?.replace(/\s+/g, ' '),
                  ].filter(Boolean) as string[];
                  
                  let certificates: CertificateFile[] = [];
                  for (const nameVariant of nameVariants) {
                    const found = certificateMap.get(nameVariant);
                    if (found && found.length > 0) {
                      certificates = found;
                      break;
                    }
                  }

                  return (
                    <div
                      key={personnel.slice_id || index}
                      className="p-5 bg-white border border-gray-200 rounded-lg hover:border-blue-300 transition-colors shadow-sm"
                    >
                      <div className="flex items-start gap-4">
                        {/* 左侧：人员信息 */}
                        <div className="flex-1">
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex-1">
                              <h4 className="text-lg font-semibold text-gray-900 mb-2">
                                {personName}
                              </h4>
                            </div>
                            {displayInfo.free_status && (
                              <div className="ml-4">
                                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                                  displayInfo.free_status.includes('空闲') || displayInfo.free_status.includes('可用')
                                    ? 'bg-green-100 text-green-700'
                                    : 'bg-gray-100 text-gray-700'
                                }`}>
                                  {displayInfo.free_status}
                                </span>
                              </div>
                            )}
                          </div>
                          <div className="grid grid-cols-2 gap-3 text-sm">
                            {displayInfo.department ? (
                              <div>
                                <span className="text-gray-500">部门：</span>
                                <span className="text-gray-900 font-medium ml-1">{displayInfo.department}</span>
                              </div>
                            ) : null}
                            {displayInfo.category ? (
                              <div>
                                <span className="text-gray-500">类别：</span>
                                <span className="text-gray-900 font-medium ml-1">{displayInfo.category}</span>
                              </div>
                            ) : null}
                            {displayInfo.certificate_name ? (
                              <div className="col-span-2">
                                <span className="text-gray-500">证书名称：</span>
                                <span className="text-gray-900 font-medium ml-1">{displayInfo.certificate_name}</span>
                              </div>
                            ) : null}
                            {displayInfo.certificate_number ? (
                              <div className="col-span-2">
                                <span className="text-gray-500">证书编号：</span>
                                <span className="text-gray-900 font-mono text-xs ml-1">{displayInfo.certificate_number}</span>
                              </div>
                            ) : null}
                            {displayInfo.issue_date ? (
                              <div>
                                <span className="text-gray-500">发证日期：</span>
                                <span className="text-gray-900 ml-1">{displayInfo.issue_date}</span>
                              </div>
                            ) : null}
                            {displayInfo.expiry_date ? (
                              <div>
                                <span className="text-gray-500">到期日期：</span>
                                <span className="text-gray-900 ml-1">{displayInfo.expiry_date}</span>
                              </div>
                            ) : null}
                            {displayInfo.free_status ? (
                              <div className="col-span-2">
                                <span className="text-gray-500">空闲状态：</span>
                                <span className={`font-medium ml-1 ${
                                  (displayInfo.free_status.includes('空闲') || displayInfo.free_status.includes('可用'))
                                    ? 'text-green-600' : 'text-gray-900'
                                }`}>
                                  {displayInfo.free_status}
                                </span>
                              </div>
                            ) : null}
                          </div>
                          
                          {/* 原始内容 */}
                          {personnel.content && (
                            <details className="mt-3">
                              <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
                                查看原始内容
                              </summary>
                              <div className="mt-2 p-3 bg-gray-50 rounded border border-gray-200">
                                <p className="text-xs text-gray-600 whitespace-pre-wrap leading-relaxed">
                                  {personnel.content}
                                </p>
                              </div>
                            </details>
                          )}
                        </div>

                        {/* 右侧：证书图片 */}
                        {certificates.length > 0 && (
                          <div className="flex-shrink-0 w-48">
                            <div className="space-y-2">
                              {certificates.map((cert, certIdx) => {
                                const isImage = /\.(jpg|jpeg|png|gif)$/i.test(cert.file_name);
                                const isPdf = /\.pdf$/i.test(cert.file_name);
                                
                                return (
                                  <div
                                    key={certIdx}
                                    className="border border-gray-200 rounded-lg overflow-hidden bg-gray-50"
                                  >
                                    {isImage ? (
                                      <div className="relative group">
                                        <img
                                          src={getFullFileUrl(cert.file_url)}
                                          alt={cert.file_name}
                                          className="w-full h-auto cursor-pointer hover:opacity-90 transition-opacity"
                                          onClick={(e) => {
                                            // 如果点击的是下载按钮区域，不打开新窗口
                                            if ((e.target as HTMLElement).closest('button')) {
                                              return;
                                            }
                                            // 否则打开新窗口查看大图
                                            const fileUrl = getFullFileUrl(cert.file_url);
                                            window.open(fileUrl, '_blank');
                                          }}
                                          onError={(e) => {
                                            console.error('图片加载失败:', cert.file_url);
                                            const target = e.currentTarget;
                                            target.style.display = 'none';
                                          }}
                                        />
                                        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all flex items-center justify-center pointer-events-none">
                                          <button
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              handleDownload(cert);
                                            }}
                                            className="opacity-0 group-hover:opacity-100 px-4 py-2 bg-white rounded shadow-lg text-sm text-gray-700 hover:bg-gray-100 transition-opacity pointer-events-auto"
                                            title="下载证书"
                                          >
                                            下载
                                          </button>
                                        </div>
                                      </div>
                                    ) : isPdf ? (
                                      <div className="p-4 text-center">
                                        <svg
                                          className="w-12 h-12 mx-auto mb-2 text-red-500"
                                          fill="none"
                                          stroke="currentColor"
                                          viewBox="0 0 24 24"
                                        >
                                          <path
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth={2}
                                            d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                                          />
                                        </svg>
                                        <p className="text-xs text-gray-600 mb-2 truncate" title={cert.file_name}>
                                          {cert.file_name}
                                        </p>
                                        <button
                                          onClick={() => handleDownload(cert)}
                                          className="px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700 transition-colors"
                                        >
                                          下载PDF
                                        </button>
                                      </div>
                                    ) : null}
                                    <div className="p-2 bg-white border-t border-gray-200">
                                      <p className="text-xs text-gray-500 truncate mb-2" title={cert.file_name}>
                                        {cert.file_name}
                                      </p>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleDownload(cert);
                                        }}
                                        className="w-full px-2 py-1.5 bg-blue-600 text-white rounded text-xs hover:bg-blue-700 transition-colors flex items-center justify-center gap-1"
                                        title="下载文件"
                                      >
                                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                        </svg>
                                        下载
                                      </button>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}
                        
                        {loadingCertificates && certificates.length === 0 && (
                          <div className="flex-shrink-0 w-48 flex items-center justify-center">
                            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-600"></div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
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
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
              <p>未找到匹配的人员信息</p>
            </div>
          )}

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
        </div>
      </div>
    </div>
  );
}
