import os
import json

def create_mock_map_data():
    # ساختن پوشه در صورت عدم وجود
    os.makedirs("data_pipeline/data", exist_ok=True)
    output_file = "data_pipeline/data/tehran_district6.json"
    
    # یه نقشه تستی و کوچولو (Mock) می‌سازیم که برنامه کار کنه
    mock_data = {
        "version": 0.6,
        "generator": "Urban Explore Mock Engine",
        "elements": [
            {"type": "node", "id": 1, "lat": 35.7000, "lon": 51.3900},
            {"type": "node", "id": 2, "lat": 35.7100, "lon": 51.4000},
            {
                "type": "way", 
                "id": 3, 
                "nodes": [1, 2], 
                "tags": {"highway": "pedestrian", "name": "Koocheh Testi (Mock)"}
            }
        ]
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(mock_data, f, indent=4)
        
    print(f"Eyval! Naghsheh tesi (Mock) ba movafaghriat sakhteh shod: {output_file}")

if __name__ == "__main__":
    create_mock_map_data()