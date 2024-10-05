# billion-hearts-assignment
# Take Home Assignment for Billion Hearts

## High Level Design

<img width="691" alt="image" src="https://github.com/user-attachments/assets/191b8c28-b67e-4894-ba9b-6e2a8a9a77c5">

## Components and their brief explanation

- Client - It is the user interacting with the "Image Upload" service via the load balancer.
-  Load Balancer - It is used to distribute traffic between instances of the "Image Upload" service.
- Image Upload - It is the service that has all the core CRUD APIs related to image upload and management. 
- Metadata DB - It is the database table that stores the metadata associated with each image.
- Object Store (S3) - For image upload - we just store the image metadata in the the table mentioned in (d). However the actual image is stored on an object store like S3. We can access the image from S3 via it's storage url 
- Message Broker (Rabbit MQ)
    - We use a light weight message broker to communicate between Image Upload and Image Analysis services.
    - We have split this as Image Analysis can be a process that is time consuming and can happen in the background while Image Upload is something that needs to happen really fast.
    - The assumption made is on any "Create/Update" on an image we would be passing a notification to our Image Analysis service to trigger an analysis.
    -  The kind of data we would look to pass via the message broker would be {storageURL, imageId, userId} - the storageURL would be used to fetch the image from S3; imageId and userId can be used to update the analysis output to the specific image and user based on requirements
    -  Using message broker to communicate between services as REST calls from service A to B would introduce tight coupling between the two services.
- Image Analysis - It is a separate service that would contain the image analysis logic - currently we have not set up any actions on success/failure of image analysis as that would depend on the use case we are solving for

## API Documentation

- Upload Image Metadata
    - Endpoint: POST /images/
    - Description: Upload metadata for a new image
    - Request Body: ImageUploadRequest
        - original_filename: string
        - user_id: integer
        - width: integer
        - height: integer
        - file_size: integer
        - file_type: string
    - Response: Image object
    - Status Codes:
        - 200: Success
        - 404: User not found
        - 422: Validation error
- List Images for User
    - Endpoint: GET /users/{user_id}/images
    - Description: Retrieve all images for a specific user
    - Path Parameters: user_id (integer)
    - Response: List of Image objects
    - Status Codes:
       - 200: Success
       - 404: User not found or no images found
- Get Image Details
    - Endpoint: GET /images/{image_id}
    - Description: Retrieve details of a specific image
    - Path Parameters: image_id (integer)
    - Response: Image object
    - Status Codes:
       - 200: Success
       - 404: Image not found
- Download Image
    - Endpoint: GET /images/{image_id}/download
    - Description: Download a specific image (currently returns metadata)
    - Path Parameters: image_id (integer)
    - Response: Image object
    - Status Codes:
       - 200: Success
       - 404: Image not found
- Update Image Metadata
   - Endpoint: PUT /images/{image_id}
   - Description: Update metadata for a specific image
   - Path Parameters: image_id (integer)
   - Request Body: ImageUpdateRequest
       - Fields to update (e.g., original_filename, width, height)
   - Response: Updated Image object
    - Status Codes:
       - 200: Success
       - 404: Image not found
       - 422: Validation error
- Delete Image
    - Endpoint: DELETE /images/{image_id}
    - Description: Delete a specific image
    - Path Parameters: image_id (integer)
    - Response: Confirmation message
    - Status Codes:
       - 200: Success
       - 404: Image not found
- Create User
    - Endpoint: POST /users/
    - Description: Create a new user
    - Request Body: UserCreateRequest
       - id: integer
       - username: string
    - Response: User object
    - Status Codes:
       - 200: Success
       - 422: Validation error
         
## Python Data Model
```
   class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True, autoincrement=False) 
    username = Column(String, unique=True, index=True)
    images = relationship("Image", back_populates="user")
```
```
class Image(Base)
    __tablename__ = 'images'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    original_filename = Column(String)
    upload_date = Column(DateTime, default=func.now())
    width = Column(Integer)
    height = Column(Integer)
    file_size = Column(Integer)
    file_type = Column(String)
    storage_path = Column(String)
    user = relationship("User", back_populates="images")
```

- Created a User data model as images should logically be mapped to a user - defined one to many relationship between User and Image and many to one relationship between Image and User
- Also added a storage_path for 'Image' as that would map to the storage url in S3 where the image is actually stored


## Setup Information

The submission is done on FASTApi and uses an SQLite DB for the database. To set this up on your local-
1) Clone the repository on your local
2) Run this command to download the requirements
 ```pip install -r requirements.txt ```
3) Run this command to bring up the application
 ```uvicorn app.main:app --reload --port 8080```
4) The application comes up on port 8080. You can view the swagger to test the APIs using this url - ```http://127.0.0.1:8080/docs```


## Testing Help
- I have created a user with 'user id' 1. Whenever you create a new image you can use the '1' as a user id or create a new user id with the 'create user' endpoint present in swagger
- You can use a random user id like 9999 or image-id 9999 to test out negative scenarios (invalid user, invalid image) for few of the relevant APIs
  
