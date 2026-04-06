import yfinance as yf
import os
import yaml

def download_data():
    with open('configs/model_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    symbol = config['data']['symbol']
    path = config['data']['raw_path']
    
    df = yf.download(symbol, period="1y", progress=False)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path)
    print(f"Saved data in: {path}")

if __name__ == "__main__":
    download_data()