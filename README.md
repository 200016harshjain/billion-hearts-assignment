# billion-hearts-assignment
Take Home Assignment for Billion Hearts

High Level Design

<img width="691" alt="image" src="https://github.com/user-attachments/assets/191b8c28-b67e-4894-ba9b-6e2a8a9a77c5">

Components and their brief explanation

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

Setup Information

The submission is done on FASTApi and uses an SQLite DB for the database. To set this up on your local-
1) Clone the repository on your local
2) Run this command to download the requirements
 ```pip install -r requirements.txt ```
3) Run this command to bring up the application
 ```uvicorn app.main:app --reload --port 8080```
4) The application comes up on port 8080. You can view the swagger to test the APIs using this url - ```http://127.0.0.1:8080/docs```


Testing Help
- I have created a user with 'user id' 1. Whenever you create a new image you can use the '1' as a user id or create a new user id with the 'create user' endpoint present in swagger
- You can use a random user id like 9999 or image-id 9999 to test out negative scenarios (invalid user, invalid image) for few of the relevant APIs
  
