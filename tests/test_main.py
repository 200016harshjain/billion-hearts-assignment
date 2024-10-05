import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, SessionLocal, engine
from app.main import app, get_db
from app.models import User, Image

# Use an in-memory SQLite database for testing purposes
SQLALCHEMY_DATABASE_URL = "sqlite:///:test:"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override the dependency to use the test database
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Create the test database and tables
@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# TO-DO : Can have a utility to create test data at the start of each run for lesser code in individual tests

def test_create_user():
    response = client.post("/users/", json={"id": 1, "username": "testuser"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["username"] == "testuser"

def test_upload_image_metadata_success():
    image_data = {
        "original_filename": "testfile.jpeg",
        "user_id": 1,
        "width": 800,
        "height": 600,
        "file_size": 1024,
        "file_type": "jpeg"
    }
    response = client.post("/images/", json=image_data)
    print(response.json())
    assert response.status_code == 200
    assert response.json()["original_filename"] == "testfile.jpeg"
    assert response.json()["user_id"] == 1


def test_upload_image_metadata_missing_field():
    image_data = {
        "original_filename": "testfile.jpeg",
        "user_id": 1,
        "width": 800,
        "height": 600,
        "file_type": "jpeg"
    }
    response = client.post("/images/", json=image_data)
    print(response.json())
    assert response.status_code == 422
   
def test_upload_image_metadata_invalid_file_type():
    image_data = {
        "original_filename": "testfile.jpeg",
        "user_id": 1,
        "width": 800,
        "height": 600,
        "file_size": 1024,
        "file_type": "pdf"
    }
    response = client.post("/images/", json=image_data)
    print(response.json())
    assert response.status_code == 422

def test_upload_image_metadata_user_does_not_exist():
    image_data = {
        "original_filename": "testfile.jpeg",
        "user_id": 2,
        "width": 800,
        "height": 600,
        "file_size": 1024,
        "file_type": "jpeg"
    }
    response = client.post("/images/", json=image_data)
    print(response.json())
    assert response.status_code == 404

def test_list_images_for_user_success():
    #user the earlier created image for the user 1
    response = client.get(f"/users/1/images")
    assert response.status_code == 200
    assert len(response.json()) == 1
    
def test_list_images_for_nonexistent_user():
    response = client.get("/users/999/images")
    assert response.status_code == 404

def test_list_images_for_user_with_no_images():
    # Create a user without images
    user_response = client.post("/users/", json={"id":3,"username": "emptyuser"})
    response = client.get(f"/users/3/images")
    assert response.status_code == 404

def test_get_image_details_success():
    response = client.get("/images/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["original_filename"] == "testfile.jpeg"
    assert response.json()["user_id"] == 1

def test_get_image_details_nonexistent():
    response = client.get("/images/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Image not found"

def test_get_image_details_invalid_id():
    response = client.get("/images/invalid")
    assert response.status_code == 422  #

# Currently download and get_image_details are the same as we don't explicitly have an image to download hence skipping tests

def test_update_image_metadata_success():
    # Update the image metadata
    update_data = {
        "original_filename": "updated.jpg",
        "width": 1024,
        "height": 768
    }
    response = client.put(f"/images/1", json=update_data)
    assert response.status_code == 200
    assert response.json()["original_filename"] == "updated.jpg"
    assert response.json()["width"] == 1024
    assert response.json()["height"] == 768

def test_update_nonexistent_image():
    update_data = {"original_filename": "nonexistent.jpg"}
    response = client.put("/images/9999", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Image not found"

def test_update_image_invalid_data():
    update_data = {"width": "invalid"}
    response = client.put("/images/1", json=update_data)
    assert response.status_code == 422  # Unprocessable Entity for invalid input

def test_delete_image_success():
    # Delete the image
    response = client.delete(f"/images/1")
    assert response.status_code == 200
    assert response.json()["detail"] == "Image deleted successfully"

    # Verify the image is no longer accessible
    get_response = client.get(f"/images/1")
    assert get_response.status_code == 404

def test_delete_nonexistent_image():
    response = client.delete("/images/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Image not found"

def test_delete_image_invalid_id():
    response = client.delete("/images/invalid")
    assert response.status_code == 422  




