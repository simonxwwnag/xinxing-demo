from fastapi import APIRouter, HTTPException
from typing import List
from services.project_service import ProjectService
from models.schemas import Project, ProjectCreate

router = APIRouter()
project_service = ProjectService()

@router.get("/projects", response_model=List[Project])
async def get_all_projects():
    """获取所有项目"""
    try:
        return project_service.get_all_projects()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")

@router.post("/projects", response_model=Project)
async def create_project(project: ProjectCreate):
    """创建新项目"""
    try:
        return project_service.create_project(project)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建项目失败: {str(e)}")

@router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """获取项目详情"""
    try:
        project = project_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目失败: {str(e)}")

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """删除项目"""
    try:
        success = project_service.delete_project(project_id)
        if not success:
            raise HTTPException(status_code=404, detail="项目不存在")
        return {"message": "项目已删除", "project_id": project_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除项目失败: {str(e)}")

