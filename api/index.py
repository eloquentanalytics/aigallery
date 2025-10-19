from fastapi import FastAPI

app = FastAPI()

@app.get("/api")
def read_root():
    return {"message": "Hello from Vercel!"}

@app.get("/api/health")
def health():
    return {"status": "ok"}

# For Vercel
handler = app