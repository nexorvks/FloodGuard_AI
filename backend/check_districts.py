
from pathlib import Path
import geopandas as gpd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

files = list(DATA_DIR.rglob("LGD_Districts.parquet"))

if not files:
    print("Dataset not found. Check the DATA_DIR path.")
else:
    gdf = gpd.read_parquet(files[0])

    print("FILE:", files[0].name)
    print("ROWS:", len(gdf))
    print("COLUMNS:", gdf.columns.tolist())
    print("CRS:", gdf.crs)
    print("GEOMETRY TYPES:")
    print(gdf.geometry.geom_type.value_counts().to_dict())

    print("\nSAMPLE DATA (excluding geometry):")
    print(gdf.drop(columns="geometry").head(3).to_string(index=False))
