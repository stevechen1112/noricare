"""
讀取食品營養成分資料庫 .ods 檔案
"""
import sys
import json

try:
    import pandas as pd
    print("Pandas version:", pd.__version__)
except ImportError:
    print("需要安裝 pandas")
    print("執行: pip install pandas openpyxl odfpy")
    sys.exit(1)

file_path = r"C:\Users\User\Desktop\personalhealth\食品營養成分資料庫2024UPDATE2.ods"

try:
    # 讀取 ODS 檔案
    print(f"\n正在讀取: {file_path}")
    
    # ODS 文件可能有多個工作表
    # 先查看有哪些工作表
    try:
        import odf
        from odf import opendocument, table
        
        doc = opendocument.load(file_path)
        sheets = doc.spreadsheet.getElementsByType(table.Table)
        
        print(f"\n找到 {len(sheets)} 個工作表:")
        for i, sheet in enumerate(sheets):
            sheet_name = sheet.getAttribute('name')
            print(f"  {i+1}. {sheet_name}")
        
        # 讀取第一個工作表
        print(f"\n正在讀取第一個工作表...")
        df = pd.read_excel(file_path, sheet_name=0, engine='odf')
        
        print(f"\n✅ 成功讀取資料!")
        print(f"資料形狀: {df.shape[0]} 行 × {df.shape[1]} 列")
        print(f"\n欄位名稱:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i}. {col}")
        
        print(f"\n前 10 筆資料預覽:")
        print(df.head(10).to_string())
        
        # 保存為 CSV 方便查看
        csv_path = file_path.replace('.ods', '.csv')
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"\n✅ 已轉存為 CSV: {csv_path}")
        
        # 保存基本統計
        stats = {
            "total_rows": int(df.shape[0]),
            "total_columns": int(df.shape[1]),
            "columns": df.columns.tolist(),
            "sample_data": df.head(5).to_dict(orient='records')
        }
        
        json_path = file_path.replace('.ods', '_info.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"✅ 已保存資料資訊: {json_path}")
        
    except ImportError as e:
        print(f"\n⚠️ 需要安裝 odfpy 套件: pip install odfpy")
        print("嘗試使用替代方法...")
        
        # 嘗試用 pandas 直接讀取
        df = pd.read_excel(file_path, engine='odf')
        print(f"\n✅ 成功讀取資料!")
        print(f"資料形狀: {df.shape[0]} 行 × {df.shape[1]} 列")
        print(f"\n欄位: {list(df.columns)}")
        print(f"\n前 5 筆預覽:")
        print(df.head())
        
except FileNotFoundError:
    print(f"\n❌ 找不到檔案: {file_path}")
except Exception as e:
    print(f"\n❌ 讀取失敗: {e}")
    import traceback
    traceback.print_exc()
