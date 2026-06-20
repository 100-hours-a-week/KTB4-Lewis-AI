from app.pipeline import ingest_all

if __name__ == "__main__":
    count = ingest_all()
    print(f"{count}개 청크를 적재했습니다.")
