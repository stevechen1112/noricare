"""
食品營養成分資料庫（ODS）匯入範本
- 讀取 工作表1
- 跳過第1行說明（header=1）
- 產出 food_items + food_nutrients 兩張表的 CSV（或可改寫為 DB 寫入）
"""
from pathlib import Path
import pandas as pd

ODS_PATH = Path(r"c:\Users\User\Desktop\personalhealth\食品營養成分資料庫2024UPDATE2.ods")
OUTPUT_DIR = Path(r"c:\Users\User\Desktop\personalhealth\_food_db_export")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 1) 讀取 ODS（僅工作表1）
xl = pd.ExcelFile(ODS_PATH, engine="odf")
sheet_name = "工作表1"

df = pd.read_excel(ODS_PATH, engine="odf", sheet_name=sheet_name, header=1)

# 2) 主表欄位
food_items_cols = {
    "整合編號": "food_id",
    "食品分類": "category",
    "樣品名稱": "name",
    "俗名": "alias",
    "內容物描述": "description",
    "廢棄率(%)": "refuse_rate_percent",
}

food_items = df[list(food_items_cols.keys())].rename(columns=food_items_cols)

# 3) 明細欄位（示例，可擴充）
NUTRIENT_MAP = {
    "熱量(kcal)": ("energy_kcal", "kcal"),
    "粗蛋白(g)": ("protein_g", "g"),
    "粗脂肪(g)": ("fat_g", "g"),
    "總碳水化合物(g)": ("carbs_g", "g"),
    "膳食纖維(g)": ("fiber_g", "g"),
    "維生素D總量(IU)": ("vitamin_d_iu", "IU"),
    "維生素B12(ug)": ("vitamin_b12_ug", "ug"),
    "葉酸(ug)": ("folate_ug", "ug"),
    "鈣(mg)": ("calcium_mg", "mg"),
    "鐵(mg)": ("iron_mg", "mg"),
    "鉀(mg)": ("potassium_mg", "mg"),
    "鈉(mg)": ("sodium_mg", "mg"),
}

records = []
for src_col, (nutrient_key, unit) in NUTRIENT_MAP.items():
    if src_col not in df.columns:
        continue
    temp = df[["整合編號", src_col]].copy()
    temp = temp.rename(columns={"整合編號": "food_id", src_col: "nutrient_value"})
    temp["nutrient_key"] = nutrient_key
    temp["unit"] = unit
    temp["basis"] = "per_100g"
    records.append(temp)

food_nutrients = pd.concat(records, ignore_index=True) if records else pd.DataFrame(
    columns=["food_id", "nutrient_key", "nutrient_value", "unit", "basis"]
)

# 4) 清理：保留 NULL，不強制補 0
food_items.to_csv(OUTPUT_DIR / "food_items.csv", index=False, encoding="utf-8-sig")
food_nutrients.to_csv(OUTPUT_DIR / "food_nutrients.csv", index=False, encoding="utf-8-sig")

print("Exported:")
print(OUTPUT_DIR / "food_items.csv")
print(OUTPUT_DIR / "food_nutrients.csv")
