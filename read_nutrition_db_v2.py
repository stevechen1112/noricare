"""
重新讀取食品營養成分資料庫，正確處理標題行
"""
import pandas as pd
import json

file_path = r"C:\Users\User\Desktop\personalhealth\食品營養成分資料庫2024UPDATE2.ods"

# 嘗試不同的標題行位置
for header_row in [0, 1, 2]:
    try:
        print(f"\n嘗試標題行 = {header_row}")
        df = pd.read_excel(file_path, sheet_name=0, engine='odf', header=header_row)
        
        print(f"資料形狀: {df.shape}")
        print(f"\n前 5 個欄位:")
        for i, col in enumerate(list(df.columns)[:10], 1):
            print(f"  {i}. {col}")
        
        # 如果欄位名看起來合理，就使用這個
        if not df.columns[0].startswith('*') and not df.columns[0].startswith('Unnamed'):
            print(f"\n✅ 使用標題行 {header_row}")
            
            # 顯示食品分類統計
            if '食品分類' in df.columns:
                print(f"\n食品分類統計:")
                print(df['食品分類'].value_counts().head(20))
            
            # 顯示關鍵欄位範例
            key_cols = ['整合編號', '食品分類', '樣品名稱', '熱量(kcal)', '粗蛋白(g)', '粗脂肪(g)', '總碳水化合物(g)']
            available_cols = [col for col in key_cols if col in df.columns]
            
            if available_cols:
                print(f"\n範例資料（前 10 筆）:")
                print(df[available_cols].head(10).to_string(index=False))
            
            # 保存清理後的資料
            csv_clean_path = file_path.replace('.ods', '_clean.csv')
            df.to_csv(csv_clean_path, index=False, encoding='utf-8-sig')
            print(f"\n✅ 清理後資料已保存: {csv_clean_path}")
            
            # 保存資料摘要
            summary = {
                "total_rows": int(df.shape[0]),
                "total_columns": int(df.shape[1]),
                "columns": df.columns.tolist(),
                "food_categories": df['食品分類'].value_counts().to_dict() if '食品分類' in df.columns else {},
                "sample_data": df.head(3).to_dict(orient='records')
            }
            
            json_path = file_path.replace('.ods', '_summary.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            print(f"✅ 資料摘要已保存: {json_path}")
            
            break
    except Exception as e:
        print(f"標題行 {header_row} 失敗: {e}")
        continue
