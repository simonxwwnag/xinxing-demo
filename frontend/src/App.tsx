import { useState, useEffect } from 'react';
import FileUpload from './components/FileUpload';
import KnowledgeQA from './components/KnowledgeQA';
import KnowledgeQAResult from './components/KnowledgeQAResult';
import CertificatePersonnelQuery from './components/CertificatePersonnelQuery';
import CertificatePersonnelResult from './components/CertificatePersonnelResult';
import ProductList from './components/ProductList';
import ProjectSelector from './components/ProjectSelector';
import { getProducts, updateProduct, deleteProduct, getProjects } from './services/api';
import type { Product, Project, CertificatePersonnelResultData } from './types';

type ViewMode = 'upload' | 'qa' | 'certificate';

function App() {
  const [products, setProducts] = useState<Product[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('upload');
  const [qaResult, setQaResult] = useState<any>(null);
  const [certificateResult, setCertificateResult] = useState<CertificatePersonnelResultData | null>(null);
  
  // 调试：监听certificateResult变化
  useEffect(() => {
    console.log('[App] certificateResult更新:', certificateResult);
    console.log('[App] certificateResult.personnel_list:', certificateResult?.personnel_list);
    console.log('[App] certificateResult.personnel_list长度:', certificateResult?.personnel_list?.length);
  }, [certificateResult]);

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      loadProducts();
    } else {
      setProducts([]);
    }
  }, [selectedProjectId]);

  const loadProjects = async () => {
    try {
      const data = await getProjects();
      setProjects(data);
      // 如果有项目且没有选中项目，自动选择第一个
      if (data.length > 0 && !selectedProjectId) {
        setSelectedProjectId(data[0].id);
      }
      // 如果当前选中的项目不在列表中（可能被删除了），自动选择第一个
      if (data.length > 0 && selectedProjectId && !data.find(p => p.id === selectedProjectId)) {
        setSelectedProjectId(data[0].id);
      }
    } catch (error) {
      console.error('加载项目列表失败:', error);
    }
  };

  const loadProducts = async () => {
    if (!selectedProjectId) {
      setProducts([]);
      return;
    }
    try {
      setLoading(true);
      const data = await getProducts(selectedProjectId);
      setProducts(data);
    } catch (error) {
      console.error('加载产品列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadSuccess = () => {
    loadProducts();
    setViewMode('upload'); // 上传成功后切换到上传视图
  };

  const handleProjectsChange = () => {
    loadProjects();
  };

  const handleProductUpdate = async (id: string, updates: Partial<Product>) => {
    try {
      await updateProduct(id, updates);
      await loadProducts();
    } catch (error) {
      console.error('更新产品失败:', error);
    }
  };

  const handleRefresh = async () => {
    await loadProducts();
  };

  const handleProductDelete = async (id: string) => {
    try {
      await deleteProduct(id);
      await loadProducts();
    } catch (error) {
      console.error('删除产品失败:', error);
      throw error; // 让ProductList组件处理错误显示
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* 头部 */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="px-6 py-4">
          <h1 className="text-2xl font-bold gradient-text">智能业务分析系统</h1>
          <p className="text-gray-600 mt-1 text-sm">采购清单智能分析 · 知识库问答 · 证书人员查询</p>
        </div>
        {/* 项目选择器 */}
        <ProjectSelector
          projects={projects}
          selectedProjectId={selectedProjectId}
          onSelect={setSelectedProjectId}
          onProjectsChange={handleProjectsChange}
        />
      </header>

      {/* 主内容：左右布局 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧：功能选择 */}
        <div className="w-80 border-r border-gray-200 bg-white flex flex-col">
          {/* 功能切换按钮 */}
          <div className="p-4 border-b border-gray-200">
            <div className="grid grid-cols-3 gap-2">
              <button
                onClick={() => setViewMode('upload')}
                className={`px-3 py-2 rounded-lg font-medium transition-colors text-sm ${
                  viewMode === 'upload'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                文档上传
              </button>
              <button
                onClick={() => setViewMode('qa')}
                className={`px-3 py-2 rounded-lg font-medium transition-colors text-sm ${
                  viewMode === 'qa'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                知识库问答
              </button>
              <button
                onClick={() => setViewMode('certificate')}
                className={`px-3 py-2 rounded-lg font-medium transition-colors text-sm ${
                  viewMode === 'certificate'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                证书人员
              </button>
            </div>
          </div>

          {/* 功能内容区域 */}
          <div className="flex-1 overflow-hidden">
            {viewMode === 'upload' ? (
              <FileUpload 
                onSuccess={handleUploadSuccess}
                projectId={selectedProjectId}
                disabled={!selectedProjectId}
              />
            ) : viewMode === 'qa' ? (
              <KnowledgeQA onResultChange={setQaResult} />
            ) : (
              <CertificatePersonnelQuery onResultChange={setCertificateResult} />
            )}
          </div>
        </div>

        {/* 右侧：内容显示区 */}
        <div className="flex-1 bg-gray-50 overflow-hidden">
          {loading ? (
            <div className="flex justify-center items-center h-full">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600"></div>
            </div>
          ) : viewMode === 'upload' ? (
            selectedProjectId ? (
              <ProductList
                products={products}
                onUpdate={handleProductUpdate}
                onDelete={handleProductDelete}
                onRefresh={handleRefresh}
              />
            ) : (
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
                  <p>请先选择一个项目</p>
                </div>
              </div>
            )
          ) : viewMode === 'qa' ? (
            <KnowledgeQAResult result={qaResult} />
          ) : (
            <CertificatePersonnelResult result={certificateResult} />
          )}
        </div>
      </div>
    </div>
  );
}

export default App;

