from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from PIL import Image
import requests
from io import BytesIO
from transformers import BlipProcessor, BlipForConditionalGeneration
import uvicorn
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("PixName-ML")

# Загружаем модель один раз при старте
logger.info("Loading BLIP processor and model...")
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
logger.info("Model loaded successfully.")

app = FastAPI(
    title="PixName Telegram Bot Backend API",
    version="0.1",
    root_path="/api"
)

class ImageRequest(BaseModel):
    image_url: str

@app.get("/health")
async def health():
    """Healthcheck для Docker"""
    return {"status": "ok"}

@app.post("/caption")
async def generate_caption(request: ImageRequest):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(request.image_url, headers=headers, timeout=10)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Ошибка загрузки изображения: {response.status_code}")

        image = Image.open(BytesIO(response.content)).convert("RGB")
        inputs = processor(image, return_tensors="pt")

        out = model.generate(
            **inputs,
            num_beams=3,
            num_return_sequences=3,
            do_sample=True
        )

        captions_en = [processor.decode(ids, skip_special_tokens=True) for ids in out]

        result = [{"en": [caption]} for caption in captions_en]  # список словарей
        logger.info(f"Generated captions: {result}")
        return {"captions": result}

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=8080)
