import json
import os
from typing import List, Optional
from datetime import datetime
import uuid
from models.schemas import Project, ProjectCreate
from utils.config import Config

class ProjectService:
    """项目管理服务"""
    
    def __init__(self):
        self.data_file = Config.PROJECTS_FILE
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        """确保数据文件存在"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
    
    def _load_projects(self) -> List[dict]:
        """加载所有项目数据"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    
    def _save_projects(self, projects: List[dict]):
        """保存项目数据"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(projects, f, ensure_ascii=False, indent=2)
    
    def create_project(self, project: ProjectCreate) -> Project:
        """创建新项目"""
        projects = self._load_projects()
        
        new_project = {
            "id": str(uuid.uuid4()),
            "name": project.name,
            "description": project.description,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        projects.append(new_project)
        self._save_projects(projects)
        
        return Project(**new_project)
    
    def get_all_projects(self) -> List[Project]:
        """获取所有项目"""
        projects = self._load_projects()
        return [Project(**p) for p in projects]
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """根据ID获取项目"""
        projects = self._load_projects()
        for p in projects:
            if p["id"] == project_id:
                return Project(**p)
        return None
    
    def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        projects = self._load_projects()
        original_count = len(projects)
        
        projects = [p for p in projects if p["id"] != project_id]
        
        if len(projects) < original_count:
            self._save_projects(projects)
            return True
        
        return False

