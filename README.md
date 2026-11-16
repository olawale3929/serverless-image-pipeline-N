# Serverless Image Processing Pipeline

A serverless application on AWS that automatically resizes images into thumbnails. Images can be processed in two ways:

1. **Upload to S3**: dropping an image into the originals bucket triggers the Lambda function directly.
2. **Call the API**: a `POST` request to API Gateway starts a Step Functions workflow that runs the same Lambda and reports success or failure.


### Workflow (Step Functions)

`ResizeImage` (Task) → `CheckResizeResult` (Choice) → `ResizeSucceeded` (Succeed) or `ResizeFailed` (Fail)

- The Lambda returns `{"status": "SUCCESS"}` or `{"status": "FAILED", "error": "..."}`.
- The Choice state routes on `$.status`.
- Transient Lambda service errors are retried up to 3 times with backoff; any other task error goes to `ResizeFailed`.

## Repository structure

```
.
 lambda/
    build.py               # Builds function.zip with Pillow for Lambda

 statemachine/
    image-resize-workflow.asl.json  # Step Functions definition

  apigateway/
   mapping-template.vtl          # Maps API request to StartExecution input

     iam/
     lambda-s3-policy.json         # Lambda: read originals, write resized

     apigw-start-execution-policy.json  # API Gateway: start the state machine
```


### 1. Create the S3 buckets
Create two general purpose buckets with **Block all public access** on: `<ORIGINALS_BUCKET>` and `<RESIZED_BUCKET>`.

### 2. Build the Lambda package
```
python lambda/build.py
```
This downloads the Linux build of Pillow for Python 3.12 / x86_64 and produces `lambda/function.zip`.

### 3. Create the Lambda function
- Name: `image-resizer`, Runtime: **Python 3.12**, Architecture: **x86_64** (must match the build)
- Upload `lambda/function.zip`
- Configuration: memory 512 MB, timeout 30 s
- Environment variable: `DEST_BUCKET = <RESIZED_BUCKET>`
- Add an inline policy to its execution role using `iam/lambda-s3-policy.json` (fill in the bucket names)

### 4. Add the S3 trigger
On the function, **Add trigger → S3**, bucket `<ORIGINALS_BUCKET>`, event type **All object create events**.

### 5. Create the state machine
Step Functions → Create state machine → Blank → Code view, paste `statemachine/image-resize-workflow.asl.json`. Name it `image-resize-workflow`, type **Standard**, create a new role, and set log level **ALL** (logs go to CloudWatch).

### 6. Create the API
1. IAM: create a role for the **API Gateway** use case named `apigw-start-stepfunction-role`, with an inline policy from `iam/apigw-start-execution-policy.json` (fill in region and account ID).
2. API Gateway → create a **REST API** (Regional), then a resource `/resize`.
3. Create a **POST** method: integration type **AWS service**, region `<REGION>`, service **Step Functions**, HTTP method POST, action `StartExecution`, execution role = the role from step 1.
4. In **Integration request**, set request body passthrough to **Never** and add a mapping template for `application/json` using `apigateway/mapping-template.vtl`.
5. **Deploy API** to a stage named `prod` and note the invoke URL.

## Usage

### upload to S3
Upload a `.jpg`, `.jpeg` or `.png` to `<ORIGINALS_BUCKET>`. Within a few seconds a thumbnail (max 128x128, aspect ratio preserved) with the same file name appears in `<RESIZED_BUCKET>`.







