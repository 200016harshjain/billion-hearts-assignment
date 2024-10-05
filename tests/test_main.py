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

def create_test_user_and_token():
    user_data = { "username": "testuser", "password": "testpassword"}
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200

    login_data = {"username": "testuser", "password": "testpassword"}
    response = client.post("/token", data=login_data)
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.fixture(scope="module")
def test_token():
    return create_test_user_and_token()

# TO-DO : Can have a utility to create test data at the start of each run for lesser code in individual tests


def test_upload_image_metadata_success(test_token):
    image_data = {
        "original_filename": "testfile.jpeg",
        "user_id": 1,
        "width": 800,
        "height": 600,
        "file_size": 1024,
        "file_type": "jpeg"
    }
    headers = {"Authorization": f"Bearer {test_token}"}
    response = client.post("/images/", json=image_data, headers=headers)
    print(response.json())
    assert response.status_code == 200
    assert response.json()["original_filename"] == "testfile.jpeg"
    assert response.json()["user_id"] == 1


def test_upload_image_metadata_missing_field(test_token):
    image_data = {
        "original_filename": "testfile.jpeg",
        "user_id": 1,
        "width": 800,
        "height": 600,
        "file_type": "jpeg"
    }
    headers = {"Authorization": f"Bearer {test_token}"}
    response = client.post("/images/", json=image_data, headers=headers)
    print(response.json())
    assert response.status_code == 422
   
def test_upload_image_metadata_invalid_file_type(test_token):
    image_data = {
        "original_filename": "testfile.jpeg",
        "user_id": 1,
        "width": 800,
        "height": 600,
        "file_size": 1024,
        "file_type": "pdf"
    }
    headers = {"Authorization": f"Bearer {test_token}"}
    response = client.post("/images/", json=image_data, headers=headers)
    print(response.json())
    assert response.status_code == 422

def test_upload_image_metadata_user_does_not_exist(test_token):
    image_data = {
        "original_filename": "testfile.jpeg",
        "user_id": 2,
        "width": 800,
        "height": 600,
        "file_size": 1024,
        "file_type": "jpeg"
    }
    headers = {"Authorization": f"Bearer {test_token}"}
    response = client.post("/images/", json=image_data, headers=headers)
    print(response.json())
    assert response.status_code == 403

def test_list_images_for_user_success(test_token):
    #using the earlier created image for the user 1
    headers = {"Authorization": f"Bearer {test_token}"}
    response = client.get(f"/users/1/images", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    

def test_list_images_for_user_with_no_images():
    # Create a user without images
    user_response = client.post("/users/", json={"username": "emptyuser", "password": "emptypassword"})
    login_data = {"username": "emptyuser", "password": "emptypassword"}
    response = client.post("/token", data=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(f"/users/2/images", headers=headers)
    assert response.status_code == 404

def test_get_image_details_success(test_token):
    headers = {"Authorization": f"Bearer {test_token}"}
    response = client.get("/images/1", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["original_filename"] == "testfile.jpeg"
    assert response.json()["user_id"] == 1


# Currently download and get_image_details are the same as we don't explicitly have an image to download hence skipping tests

def test_update_image_metadata_success(test_token):
    # Update the image metadata
    update_data = {
        "original_filename": "updated.jpg",
        "width": 1024,
        "height": 768
    }
    headers = {"Authorization": f"Bearer {test_token}"}
    response = client.put(f"/images/1", json=update_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["original_filename"] == "updated.jpg"
    assert response.json()["width"] == 1024
    assert response.json()["height"] == 768

def test_update_nonexistent_image(test_token):
    update_data = {"original_filename": "nonexistent.jpg"}
    headers = {"Authorization": f"Bearer {test_token}"}
    response = client.put("/images/9999", json=update_data, headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Image not found"

def test_update_image_invalid_data(test_token):
    headers = {"Authorization": f"Bearer {test_token}"}
    update_data = {"width": "invalid"}
    response = client.put("/images/1", json=update_data, headers=headers)
    assert response.status_code == 422  # Unprocessable Entity for invalid input

def test_delete_image_success(test_token):
    # Delete the image
    headers = {"Authorization": f"Bearer {test_token}"}
    response = client.delete(f"/images/1", headers=headers)
    assert response.status_code == 200
    assert response.json()["detail"] == "Image deleted successfully"

    # Verify the image is no longer accessible
    get_response = client.get(f"/images/1", headers=headers)
    assert get_response.status_code == 404

#deleted a few tests related to invalid inputs (999, invalid) post JWT 



