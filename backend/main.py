from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import upload, knowledge, search, data, project, mcp_helper, certificate

app = FastAPI(title="采购清单智能分析系统", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(project.router, prefix="/api/data", tags=["项目管理"])
app.include_router(upload.router, prefix="/api", tags=["上传"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["知识库"])
app.include_router(search.router, prefix="/api/search", tags=["搜索"])
app.include_router(data.router, prefix="/api/data", tags=["数据管理"])
app.include_router(mcp_helper.router, prefix="/api", tags=["MCP工具"])
app.include_router(certificate.router, prefix="/api/certificate", tags=["证书文件"])

@app.get("/")
async def root():
    return {"message": "采购清单智能分析系统API"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

