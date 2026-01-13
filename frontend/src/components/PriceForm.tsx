import { useState, useEffect } from 'react';
import type { Product } from '../types';
import { updateProduct } from '../services/api';

interface PriceFormProps {
  product: Product;
  onUpdate: (id: string, updates: Partial<Product>) => void;
}

export default function PriceForm({ product, onUpdate }: PriceFormProps) {
  const [price, setPrice] = useState(product.price?.toString() || '');
  const [priceUnit, setPriceUnit] = useState(product.price_unit || '');
  const [notes, setNotes] = useState(product.notes || '');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setPrice(product.price?.toString() || '');
    setPriceUnit(product.price_unit || '');
    setNotes(product.notes || '');
  }, [product]);

  const handleSave = async () => {
    if (!price && !priceUnit && !notes) {
      return;
    }

    setSaving(true);
    try {
      const updates: any = {};
      if (price) {
        updates.price = parseFloat(price);
      }
      if (priceUnit) {
        updates.price_unit = priceUnit;
      }
      if (notes) {
        updates.notes = notes;
      }

      // 如果填写了价格相关信息，自动标记为询价完成
      if (price || priceUnit || notes) {
        updates.inquiry_completed = true;
      }

      await updateProduct(product.id, updates);
      onUpdate(product.id, updates);
    } catch (error) {
      console.error('保存失败:', error);
    } finally {
      setSaving(false);
    }
  };

  const hasChanges =
    price !== (product.price?.toString() || '') ||
    priceUnit !== (product.price_unit || '') ||
    notes !== (product.notes || '');

  return (
    <div className="mt-4 pt-4 border-t border-gray-200">
      <h4 className="text-sm font-semibold text-gray-700 mb-3">价格信息</h4>
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-600 mb-1">价格</label>
            <input
              type="number"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder="请输入价格"
              className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">单位</label>
            <input
              type="text"
              value={priceUnit}
              onChange={(e) => setPriceUnit(e.target.value)}
              placeholder="如：元/件"
              className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs text-gray-600 mb-1">备注</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="请输入备注信息"
            rows={2}
            className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors resize-none"
          />
        </div>

        {hasChanges && (
          <button
            onClick={handleSave}
            disabled={saving}
            className="w-full px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? '保存中...' : '保存并标记询价完成'}
          </button>
        )}
      </div>
    </div>
  );
}

