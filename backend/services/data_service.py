import json
import os
from typing import List, Optional
from datetime import datetime
import uuid
from models.schemas import Product, ProductCreate, ProductUpdate
from utils.config import Config

class DataService:
    """数据存储服务"""
    
    def __init__(self):
        self.data_dir = Config.DATA_DIR
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _get_products_file(self, project_id: str) -> str:
        """获取项目的产品文件路径"""
        return os.path.join(self.data_dir, f"products_{project_id}.json")
    
    def _load_products(self, project_id: str) -> List[dict]:
        """加载指定项目的产品数据"""
        products_file = self._get_products_file(project_id)
        try:
            if os.path.exists(products_file):
                with open(products_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception:
            return []
    
    def _save_products(self, project_id: str, products: List[dict]):
        """保存项目的产品数据"""
        products_file = self._get_products_file(project_id)
        with open(products_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
    
    def create_product(self, product: ProductCreate, specs: List = None, suppliers: List = None) -> Product:
        """创建新产品"""
        products = self._load_products(product.project_id)
        
        new_product = {
            "id": str(uuid.uuid4()),
            "project_id": product.project_id,
            "project_code": product.project_code,
            "project_name": product.project_name,
            "project_features": product.project_features,
            "unit": product.unit,
            "quantity": product.quantity,
            "other_specs": specs or [],
            "suppliers": suppliers or [],
            "price": None,
            "price_unit": None,
            "notes": None,
            "inquiry_completed": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        products.append(new_product)
        self._save_products(product.project_id, products)
        
        return Product(**new_product)
    
    def get_all_products(self, project_id: Optional[str] = None) -> List[Product]:
        """获取所有产品，如果指定project_id则只返回该项目的产品"""
        if project_id:
            products = self._load_products(project_id)
            return [Product(**p) for p in products]
        else:
            # 返回所有项目的产品
            all_products = []
            for filename in os.listdir(self.data_dir):
                if filename.startswith("products_") and filename.endswith(".json"):
                    project_id_from_file = filename.replace("products_", "").replace(".json", "")
                    products = self._load_products(project_id_from_file)
                    all_products.extend([Product(**p) for p in products])
            return all_products
    
    def get_product(self, product_id: str, project_id: Optional[str] = None) -> Optional[Product]:
        """根据ID获取产品"""
        if project_id:
            products = self._load_products(project_id)
            for p in products:
                if p["id"] == product_id:
                    return Product(**p)
        else:
            # 在所有项目中查找
            for filename in os.listdir(self.data_dir):
                if filename.startswith("products_") and filename.endswith(".json"):
                    project_id_from_file = filename.replace("products_", "").replace(".json", "")
                    products = self._load_products(project_id_from_file)
                    for p in products:
                        if p["id"] == product_id:
                            return Product(**p)
        return None
    
    def update_product(self, product_id: str, update_data: ProductUpdate, project_id: Optional[str] = None) -> Optional[Product]:
        """更新产品信息"""
        product = self.get_product(product_id, project_id)
        if not product:
            return None
        
        products = self._load_products(product.project_id)
        
        for p in products:
            if p["id"] == product_id:
                # 更新字段
                if update_data.price is not None:
                    p["price"] = update_data.price
                if update_data.price_unit is not None:
                    p["price_unit"] = update_data.price_unit
                if update_data.notes is not None:
                    p["notes"] = update_data.notes
                if update_data.inquiry_completed is not None:
                    p["inquiry_completed"] = update_data.inquiry_completed
                
                p["updated_at"] = datetime.now().isoformat()
                
                self._save_products(product.project_id, products)
                return Product(**p)
        
        return None
    
    def mark_inquiry_completed(self, product_id: str, project_id: Optional[str] = None) -> Optional[Product]:
        """标记询价完成"""
        return self.update_product(product_id, ProductUpdate(inquiry_completed=True), project_id)
    
    def update_product_specs_and_suppliers(self, product_id: str, specs: List, suppliers: List, spec_summary: Optional[str] = None, project_id: Optional[str] = None) -> Optional[Product]:
        """更新产品的规格和供应商信息"""
        product = self.get_product(product_id, project_id)
        if not product:
            return None
        
        # 调试：检查保存前的suppliers数据
        for i, supplier in enumerate(suppliers[:3], 1):
            if isinstance(supplier, dict):
                content = supplier.get('content', '')
                content_len = len(content) if content else 0
                print(f"[DataService] 保存前供应商 {i}: {supplier.get('name', 'N/A')}, content长度: {content_len}")
        
        products = self._load_products(product.project_id)
        
        for p in products:
            if p["id"] == product_id:
                p["other_specs"] = specs
                p["suppliers"] = suppliers
                if spec_summary is not None:
                    p["spec_summary"] = spec_summary
                p["updated_at"] = datetime.now().isoformat()
                
                # 调试：检查保存后的suppliers数据
                for i, supplier in enumerate(p["suppliers"][:3], 1):
                    if isinstance(supplier, dict):
                        content = supplier.get('content', '')
                        content_len = len(content) if content else 0
                        print(f"[DataService] 保存后供应商 {i}: {supplier.get('name', 'N/A')}, content长度: {content_len}")
                
                self._save_products(product.project_id, products)
                
                # 调试：检查从文件读取后的数据
                loaded_products = self._load_products(product.project_id)
                for loaded_p in loaded_products:
                    if loaded_p["id"] == product_id:
                        for i, supplier in enumerate(loaded_p["suppliers"][:3], 1):
                            if isinstance(supplier, dict):
                                content = supplier.get('content', '')
                                content_len = len(content) if content else 0
                                print(f"[DataService] 读取后供应商 {i}: {supplier.get('name', 'N/A')}, content长度: {content_len}")
                        break
                
                return Product(**p)
        
        return None
    
    def delete_product(self, product_id: str, project_id: Optional[str] = None) -> bool:
        """删除产品"""
        product = self.get_product(product_id, project_id)
        if not product:
            return False
        
        products = self._load_products(product.project_id)
        original_count = len(products)
        
        products = [p for p in products if p["id"] != product_id]
        
        if len(products) < original_count:
            self._save_products(product.project_id, products)
            return True
        
        return False

