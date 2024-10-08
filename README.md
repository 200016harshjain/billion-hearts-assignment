# billion-hearts-assignment
# Take Home Assignment for Billion Hearts

## High Level Design

<img width="880" alt="image" src="https://github.com/user-attachments/assets/ea8e997f-b125-4a25-af0e-b78ea6f76e13">


## Components and their brief explanation

- Client - It is the user interacting with our services via the load balancer.
- Load Balancer - It is used to distribute traffic between instances of the "Image Upload and Retrieval" service.
- Image Upload and Retrieval - It is the service that has all the core CRUD APIs related to image upload and management. Assuming that P99 100ms is just on 'Image Upload and Retrieval' and 'Image Analysis' is a longer workload with different SLAs.
- CDN - We introduce a CDN to speed up our reads from Image Upload and Retrieval Service. Since we expect this to be read heavy service (10:1) - the faster reads via CDN would really help meet our SLAs.
- Metadata DB - It is the database table that stores the metadata associated with each image.
- Object Store (S3) - For image upload - we just store the image metadata in the Metadata table. However the actual image is stored on an object store like S3. We can access the image from S3 via it's storage url. 
- Message Broker (Rabbit MQ)
    - We use a light weight message broker to communicate between Image Upload/Retrieval and Image Analysis services.
    - We have split this as Image Analysis is assumed to be a longer workload that can happen in the background while Image Upload is something that needs to happen really fast.
    - Another assumption made is on  "Create and Update" on an image we would be passing a notification to our Image Analysis service to trigger an analysis.
    - The kind of data we would look to pass via the message broker would be {storageURL, imageId, userId} - the storageURL would be used to fetch the image from S3; imageId and userId can be used to map the analysis output to the specific image and user based on requirements.
    - Use a message broker to communicate between services as REST calls from service A to B would introduce tight coupling between the two services.
- Image Analysis - It is a separate service that would contain the image analysis logic. 
## API Documentation

- Upload Image Metadata
    - Endpoint: POST /images/
    - Description: Upload metadata for a new image
    - Authentication: Required
    - Request Body: ImageUploadRequest
        - original_filename: string
        - user_id: integer
        - width: integer
        - height: integer
        - file_size: integer
        - file_type: string
    - Response: Image object
    - Status Codes:
        - 200: Successful response (Image object)
        - 403: Not authorized to upload for this user
        - 404: User does not exist
- List Images for User
    - Endpoint: GET /users/{user_id}/images
    - Description: Retrieve all images for a specific user
    - Authentication: Required
    - Path Parameters: user_id (integer)
    - Response: List of Image objects
    - Status Codes:
       - 200: Success
       - 403: Unauthorized access to user images
       - 404: User not found or No images found for this user
- Get Image Details
    - Endpoint: GET /images/{image_id}
    - Description: Retrieve details of a specific image
    - Authentication: Required
    - Path Parameters: image_id (integer)
    - Response: Image object
    - Status Codes:
       - 200: Successful response (Image object)
       - 403: Unauthorized access to user image
       - 404: Image not found
- Download Image
    - Endpoint: GET /images/{image_id}/download
    - Description: Download a specific image (currently returns metadata)
    - Authentication: Required
    - Path Parameters: image_id (integer)
    - Response: Image object
    - Status Codes:
       - 200: Successful response (Image object)
       - 403: Unauthorized access to user image
       - 404: Image not found
- Update Image Metadata
   - Endpoint: PUT /images/{image_id}
   - Description: Update metadata for a specific image
   - Authentication: Required
   - Path Parameters: image_id (integer)
   - Request Body: ImageUpdateRequest
       - Fields to update (e.g., original_filename, width, height)
   - Response: Updated Image object
    - Status Codes:
       - 200: Successful response (Updated Image object)
       - 403: Unauthorized access to user image
       - 404: Image not found
- Delete Image
    - Endpoint: DELETE /images/{image_id}
    - Description: Delete a specific image
    - Authentication: Required
    - Path Parameters: image_id (integer)
    - Response: Confirmation message
    - Status Codes:
       - 200: Image deleted successfully
       - 403: Unauthorized access to user image
       - 404: Image not found
- Create User
    - Endpoint: POST /users/
    - Description: Create a new user
    - Authentication: Not required
    - Request Body: UserCreateRequest
       - id: integer
       - username: string
       - password: string
    - Response: User object
    - Status Codes:
       - 201: UserResponse (Created User Object)
       - 400: Username already registered
- Token
  - Description: Login to obtain access token
  - Authentication: Not required
  - Request Body: OAuth2PasswordRequestForm
  - Responses:
    - 200: Successful response (Token object)
    - 401: Incorrect username or password
## Python Data Model
```
   class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True) 
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

- Created a User data model as images should logically be mapped to a user - defined one to many relationship between User and Image and many to one relationship between Image and User.
- Also added a storage_path for 'Image' as that would map to the storage url in S3 where the image is actually stored


## Setup Information

The submission is done on FASTApi and uses an SQLite DB for the database. To set this up on your local-
1) Clone the repository on your local
2) Run this command to download the requirements
 ```pip install -r requirements.txt ```
3) Run this command to bring up the application
 ```uvicorn app.main:app --reload --port 8080``` - 
    In case you have done (1) but are getting 'uvicorn: command not found' - please try ```python -m uvicorn app.main:app --reload --port 8080```
4) The application comes up on port 8080. You can use swagger to test the APIs using this url - ```http://127.0.0.1:8080/docs```


## Testing Help
- Since we've implemented JWT - you can authenticate using id and password to test the endpoints
- Sample Users
   - First User
      - username : "harsh"
      - password : "test"
      - id: 1
  - Second User
      - username : "nupur"
      - password : "testing"
      - id: 2
- You can also create a new user using the ```/users/``` endpoint.
- Run test suite ```pytest tests/test_main.py```

## Bonus 
- Notifying users post image analysis
  - I have assumed that the image analysis process is not real time - it is a longer running workload.
  - With that assumption
        - A notification service that is responsible to send notifications to client.
        - The image analysis service would then communicate to this notification service over a light weight message broker.
  - If that assumption is not true
        - Image upload and analysis is to have an SLA of 100 ms then I would rework the design.
            - Effectively have one service for upload and analysis to save on message broker latency and prevent an extra read from S3 and the overall dev effort in maintaining another service.
            - If the SLA for both is 100ms one can imagine that users would upload an image and only on succesful analysis would we move to the next step.  The idea is that image upload and analysis are tightly coupled
              in our user workflow and hence we can make that tradeoff of having tight coupling in code to meet our SLAs and have lesser overhead in maintaining an extra service.
- Implemented JWT - all endpoints are authorized and a user can only access that belong to them.
    
     
  
