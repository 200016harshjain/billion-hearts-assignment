from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, User, Image
from app.schemas import ImageUploadRequest, ImageUpdateRequest, UserCreateRequest

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/images/")
def upload_image_metadata(image_data: ImageUploadRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == image_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User does not exist")
    new_image = Image(**image_data.dict())
    # new_image.storage_path would be the url of the image post uploading to S3 Store
    db.add(new_image)
    db.commit()
    db.refresh(new_image)
    return new_image

@app.get("/users/{user_id}/images")
def list_images_for_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    images = user.images
    if not images:
        raise HTTPException(status_code=404, detail="No images found for this user")
    
    return images

@app.get("/images/{image_id}")
def get_image_details(image_id: int, db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image

@app.get("/images/{image_id}/download")
def download_image(image_id: int, db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.id == image_id).first()
    #Downloading the image would actually be done from the 'storage_path' - returning metadata for now
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image

@app.put("/images/{image_id}")
def update_image_metadata(image_id: int, image_update: ImageUpdateRequest, db: Session = Depends(get_db)):
    #updating image data may include  updating the image in the S3 Store based on requirements
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    for key, value in image_update.dict(exclude_unset=True).items():
        setattr(image, key, value)

    db.commit()
    db.refresh(image)
    return image

@app.delete("/images/{image_id}")
def delete_image(image_id: int, db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    # deletion would also include deleting the image from the S3 Store
    db.delete(image)
    db.commit()
    return {"detail": "Image deleted successfully"}

#created a user endpoint for creating test data
@app.post("/users/")
def create_user(user: UserCreateRequest, db: Session = Depends(get_db)):
    db_user = User(id = user.id,username=user.username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
