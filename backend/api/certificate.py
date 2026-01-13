from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from typing import List, Optional
from urllib.parse import quote, unquote
import os
import glob
from utils.config import Config

router = APIRouter()

# 证书文件目录（从配置文件读取）
CERTIFICATE_DIR = Config.CERTIFICATE_DIR

class CertificateFile(BaseModel):
    """证书文件信息"""
    name: str = Field(..., description="人员姓名")
    file_path: str = Field(..., description="文件路径")
    file_name: str = Field(..., description="文件名")
    file_url: str = Field(..., description="文件访问URL")

class CertificateMatchRequest(BaseModel):
    """证书匹配请求"""
    names: List[str] = Field(..., description="人员姓名列表")

class CertificateMatchResponse(BaseModel):
    """证书匹配响应"""
    certificates: List[CertificateFile] = Field(default_factory=list, description="匹配的证书文件列表")

def find_certificate_files(name: str, certificate_dir: str) -> List[dict]:
    """
    根据人员姓名查找匹配的证书文件
    
    Args:
        name: 人员姓名
        certificate_dir: 证书文件目录
        
    Returns:
        匹配的证书文件列表
    """
    if not os.path.exists(certificate_dir):
        return []
    
    matched_files = []
    # 清理姓名，去除空格
    clean_name = name.strip()
    
    # 遍历目录中的所有文件
    for file_path in glob.glob(os.path.join(certificate_dir, "*")):
        if os.path.isfile(file_path):
            file_name = os.path.basename(file_path)
            # 检查文件名中是否包含人员姓名
            if clean_name in file_name:
                file_url = f"/api/certificate/file/{quote(file_name)}"
                matched_files.append({
                    "name": clean_name,
                    "file_path": file_path,
                    "file_name": file_name,
                    "file_url": file_url
                })
    
    return matched_files

@router.post("/match", response_model=CertificateMatchResponse)
async def match_certificates(request: CertificateMatchRequest):
    """
    根据人员姓名列表匹配证书文件
    """
    try:
        certificates = []
        for name in request.names:
            matched = find_certificate_files(name, CERTIFICATE_DIR)
            certificates.extend(matched)
        
        return CertificateMatchResponse(certificates=certificates)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匹配证书文件失败: {str(e)}")

@router.get("/file/{file_name:path}")
async def get_certificate_file(file_name: str):
    """
    获取证书文件（支持图片和PDF）
    正确处理中文文件名编码
    """
    try:
        # URL解码文件名
        decoded_file_name = unquote(file_name, encoding='utf-8')
        file_path = os.path.join(CERTIFICATE_DIR, decoded_file_name)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 根据文件扩展名确定媒体类型
        ext = os.path.splitext(decoded_file_name)[1].lower()
        media_type_map = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
        }
        media_type = media_type_map.get(ext, 'application/octet-stream')
        
        # 读取文件内容
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # 构建 Content-Disposition 头，正确处理中文文件名
        # 使用 RFC 5987 编码处理中文文件名
        encoded_filename = quote(decoded_file_name, safe='')
        content_disposition = f"inline; filename*=UTF-8''{encoded_filename}"
        
        # 为了兼容性，也添加一个 ASCII 编码的 filename
        # 如果文件名包含非 ASCII 字符，使用 URL 编码
        try:
            ascii_filename = decoded_file_name.encode('ascii').decode('ascii')
            content_disposition = f"inline; filename=\"{ascii_filename}\"; filename*=UTF-8''{encoded_filename}"
        except UnicodeEncodeError:
            # 如果无法编码为 ASCII，只使用 UTF-8 编码的版本
            pass
        
        headers = {
            "Content-Disposition": content_disposition,
            "Content-Type": media_type,
        }
        
        return Response(
            content=file_content,
            media_type=media_type,
            headers=headers
        )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取文件失败: {str(e)}")

