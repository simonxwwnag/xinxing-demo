import { useState, useCallback } from 'react';
import { uploadExcel } from '../services/api';

interface FileUploadProps {
  onSuccess: () => void;
  projectId: string | null;
  disabled?: boolean;
}

export default function FileUpload({ onSuccess, projectId, disabled }: FileUploadProps) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(async (file: File) => {
    if (!projectId) {
      setError('请先选择一个项目');
      return;
    }
    
    if (!file.name.match(/\.(xlsx|xls)$/i)) {
      setError('只支持Excel文件 (.xlsx, .xls)');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      await uploadExcel(file, projectId);
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || '上传失败，请重试');
    } finally {
      setUploading(false);
    }
  }, [projectId, onSuccess]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      handleFile(file);
    }
  }, [handleFile]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
  }, []);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
  }, [handleFile]);

  return (
    <div
      className={`h-full flex flex-col p-6 border-2 border-dashed transition-all duration-300 ${
        disabled
          ? 'border-gray-200 bg-gray-50 opacity-50'
          : dragging
          ? 'border-blue-500 bg-blue-50 scale-[1.02]'
          : 'border-gray-300 hover:border-blue-400'
      } ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
      onDrop={disabled ? undefined : handleDrop}
      onDragOver={disabled ? undefined : handleDragOver}
      onDragLeave={disabled ? undefined : handleDragLeave}
    >
      <div className="flex-1 flex flex-col items-center justify-center text-center">
        <div className="mb-6">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 mb-4">
            <svg
              className="w-10 h-10 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>
        </div>

        <h3 className="text-xl font-semibold mb-2 text-gray-900">
          {uploading 
            ? '正在上传...' 
            : disabled
            ? '请先选择一个项目' 
            : '拖拽Excel文件到此处'}
        </h3>
        {!disabled && !uploading && (
          <p className="text-gray-600 mb-4">
            或 <span className="text-blue-600 font-medium">点击选择文件</span>
          </p>
        )}

        <label className="inline-block">
          <input
            type="file"
            accept=".xlsx,.xls"
            onChange={handleFileInput}
            className="hidden"
            disabled={uploading || disabled}
          />
          <span className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-lg cursor-pointer hover:from-blue-700 hover:to-purple-700 transition-all shadow-md hover:shadow-lg">
            {uploading ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
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
                上传中...
              </>
            ) : (
              '选择文件'
            )}
          </span>
        </label>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 max-w-md">
            {error}
          </div>
        )}

        <p className="text-sm text-gray-500 mt-6 max-w-md">
          支持格式: .xlsx, .xls | 必需字段: 项目编码、项目名称、项目特征、计量单位、工程量
        </p>
      </div>
    </div>
  );
}

