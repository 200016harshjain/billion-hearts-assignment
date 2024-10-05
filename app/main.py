from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, User, Image
from app.schemas import ImageUploadRequest, ImageUpdateRequest, UserCreateRequest, Token
from app.auth.jwt import verify_password, get_password_hash, create_access_token
from app.auth.dependencies import get_current_user
from datetime import timedelta
from app.database import get_db 

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.post("/images/")
def upload_image_metadata(image_data: ImageUploadRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
def list_images_for_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    images = user.images
    if not images:
        raise HTTPException(status_code=404, detail="No images found for this user")
    
    return images

@app.get("/images/{image_id}")
def get_image_details(image_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image

@app.get("/images/{image_id}/download")
def download_image(image_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    image = db.query(Image).filter(Image.id == image_id).first()
    #Downloading the image would actually be done from the 'storage_path' - returning metadata for now
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image

@app.put("/images/{image_id}")
def update_image_metadata(image_id: int, image_update: ImageUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
def delete_image(image_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    # deletion would also include deleting the image from the S3 Store
    db.delete(image)
    db.commit()
    return {"detail": "Image deleted successfully"}


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# Modify the create_user endpoint to hash the password
@app.post("/users/")
def create_user(user: UserCreateRequest, db: Session = Depends(get_db)):
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, id=user.id, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return "User"