import pandas as pd
from typing import List, Dict, Any
from models.schemas import ProductCreateFromExcel

class ExcelParser:
    """Excel文件解析服务"""
    
    REQUIRED_COLUMNS = ["项目编码", "项目名称", "项目特征", "计量单位", "工程量"]
    
    @staticmethod
    def _normalize_column_name(col_name: str) -> str:
        """规范化列名，去除空格和特殊字符"""
        if pd.isna(col_name):
            return ""
        return str(col_name).strip().replace('\u3000', ' ')  # 替换全角空格
    
    @staticmethod
    def _find_column(df: pd.DataFrame, target_name: str) -> str:
        """查找匹配的列名（支持模糊匹配）"""
        target_normalized = ExcelParser._normalize_column_name(target_name)
        
        # 先尝试精确匹配
        for col in df.columns:
            if ExcelParser._normalize_column_name(col) == target_normalized:
                return col
        
        # 如果精确匹配失败，尝试包含匹配
        for col in df.columns:
            col_normalized = ExcelParser._normalize_column_name(col)
            if target_normalized in col_normalized or col_normalized in target_normalized:
                return col
        
        return None
    
    @staticmethod
    def parse_excel(file_path: str) -> List[ProductCreateFromExcel]:
        """
        解析Excel文件，支持灵活的列名匹配
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            产品列表（不包含project_id，需要在调用时添加）
            
        Raises:
            ValueError: 如果缺少必需字段或数据格式错误
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            print(f"[Excel解析] 读取到的列名: {list(df.columns)}")
            print(f"[Excel解析] 数据行数: {len(df)}")
            
            # 查找必需的列
            column_mapping = {}
            for required_col in ExcelParser.REQUIRED_COLUMNS:
                found_col = ExcelParser._find_column(df, required_col)
                if found_col:
                    column_mapping[required_col] = found_col
                    print(f"[Excel解析] 找到列 '{required_col}' -> '{found_col}'")
                else:
                    print(f"[Excel解析] 警告: 未找到列 '{required_col}'")
            
            # 检查必需字段
            missing_columns = [col for col in ExcelParser.REQUIRED_COLUMNS if col not in column_mapping]
            if missing_columns:
                raise ValueError(f"Excel文件缺少必需字段: {', '.join(missing_columns)}。实际列名: {', '.join(df.columns.tolist())}")
            
            # 解析数据
            products = []
            for index, row in df.iterrows():
                try:
                    # 数据清洗和验证
                    project_code_col = column_mapping["项目编码"]
                    project_name_col = column_mapping["项目名称"]
                    project_features_col = column_mapping["项目特征"]
                    unit_col = column_mapping["计量单位"]
                    quantity_col = column_mapping["工程量"]
                    
                    project_code = str(row[project_code_col]).strip() if pd.notna(row[project_code_col]) else ""
                    project_name = str(row[project_name_col]).strip() if pd.notna(row[project_name_col]) else ""
                    project_features = str(row[project_features_col]).strip() if pd.notna(row[project_features_col]) else None
                    unit = str(row[unit_col]).strip() if pd.notna(row[unit_col]) else ""
                    
                    # 处理工程量，可能是数字或字符串
                    quantity_value = row[quantity_col]
                    if pd.notna(quantity_value):
                        try:
                            quantity = float(quantity_value)
                        except (ValueError, TypeError):
                            # 如果是字符串，尝试提取数字
                            quantity_str = str(quantity_value).strip()
                            quantity = float(quantity_str) if quantity_str else 0.0
                    else:
                        quantity = 0.0
                    
                    # 验证必需字段
                    if not project_code or not project_name or not unit:
                        print(f"[Excel解析] 跳过第 {index + 2} 行（索引{index + 1}）: 缺少必需字段")
                        continue  # 跳过无效行
                    
                    # 创建ProductCreateFromExcel（不包含project_id，需要在调用时添加）
                    product = ProductCreateFromExcel(
                        project_code=project_code,
                        project_name=project_name,
                        project_features=project_features if project_features else None,
                        unit=unit,
                        quantity=quantity
                    )
                    products.append(product)
                    print(f"[Excel解析] 成功解析第 {index + 2} 行: {project_name}")
                except Exception as e:
                    # 记录错误但继续处理其他行
                    print(f"[Excel解析] 解析第 {index + 2} 行时出错: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            if not products:
                raise ValueError("Excel文件中没有有效的数据行")
            
            print(f"[Excel解析] 成功解析 {len(products)} 个产品")
            return products
            
        except ValueError:
            raise
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise ValueError(f"解析Excel文件失败: {str(e)}")

