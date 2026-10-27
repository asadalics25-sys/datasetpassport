# **DatasetPassport** 

Product Requirements Document 

_Version 1.0 | Initial Project Specification | Full-stack Web Application_ 

**Dataset Auditing and ML Experiment Tracking Platform** 

DatasetPassport PRD  •  Page 1 

## **1. Product Overview** 

DatasetPassport is a web-based platform that helps users inspect datasets, understand their structure and quality, train a basic machine learning model, and track experiments in one place. 

Users can upload CSV datasets, view dataset profiling results, select a target column, train a classification model, review evaluation metrics, and view a history of their experiments. 

The project aims to make the early stages of a machine learning workflow easier to understand, more organized, and accessible to students and beginners. 

## **2. Problem Statement** 

Before training a machine learning model, users need to understand their dataset, identify missing values, inspect column types, and determine whether the data is suitable for training. These tasks are often performed using separate tools and scripts. Beginners may also struggle to keep track of model configurations and evaluation results across experiments. 

DatasetPassport addresses these problems by combining dataset profiling and basic machine learning experiment tracking in a single interface. 

## **3. Product Goals** 

- Enable users to upload and inspect CSV datasets. 

- Provide a clear summary of dataset structure and data quality. 

- Allow users to train a classification model using a selected target column. 

- Display model evaluation metrics in an understandable format. 

- Maintain a history of experiments during the active backend session. 

- Provide a foundation for future dataset versioning and reproducibility features. 

### **Success Criteria** 

- A valid CSV file can be uploaded and profiled successfully. 

- Users can view row counts, column information, data types, and missing-value summaries. 

- Users can select a valid target column and run model training. 

- Evaluation metrics are displayed after successful training. 

- Successful experiments appear in history while the backend remains running. 

- Invalid files and unsuitable training data produce understandable error messages. 

## **4. Target Users** 

### **Primary Users** 

- Students learning data science and machine learning. 

- Beginners experimenting with classification datasets. 

- Developers building and testing basic ML workflows. 

- Educators demonstrating dataset inspection and model evaluation. 

### **User Needs** 

- Understand a dataset before training a model. 

- Identify potential data-quality issues. 

DatasetPassport PRD  •  Page 2 

- Train a baseline model without writing a complete ML pipeline. 

- Compare experiment results. 

- Learn how dataset preparation affects model performance. 

## **5. Scope** 

### **In Scope — Current Version** 

- CSV dataset upload. 

- Dataset profiling and column summaries. 

- Missing-value inspection. 

- Target-column selection. 

- Basic classification model training. 

- Automatic handling of missing feature values. 

- Encoding of categorical features. 

- Model evaluation using standard classification metrics. 

- Experiment history stored in backend memory. 

- Sample CSV dataset for demonstration. 

### **Out of Scope — Initial Version** 

- Persistent experiment storage. 

- User accounts and authentication. 

- Team collaboration. 

- Automated model selection. 

- Regression and deep learning workflows. 

- Full dataset version control. 

- Production deployment and enterprise security. 

- Dataset change detection using SHA-256 fingerprints. 

These features may be considered for future releases. 

## **6. Functional Requirements** 

### **FR-01: Dataset Upload** 

Users must be able to upload a CSV file through the web interface. 

#### **Requirements** 

- Accept CSV files. 

- Enforce the configured upload-size limit of 10 MB. 

- Parse the uploaded file for profiling and training. 

- Return a useful error for invalid or unreadable files. 

#### **Acceptance Criteria** 

- A valid CSV uploads successfully. 

- An invalid file does not crash the application. 

- Oversized uploads are rejected. 

DatasetPassport PRD  •  Page 3 

### **FR-02: Dataset Profiling** 

The application must summarize the uploaded dataset. 

#### **Requirements** 

- Display row and column counts. 

- Display column names and data types. 

- Report missing values by column. 

- Provide a summary of dataset structure. 

#### **Acceptance Criteria** 

- Results correspond to the uploaded CSV. 

- Missing-value counts are accurate. 

- Users can identify columns that may need cleaning. 

### **FR-03: Target-Column Selection** 

Users must be able to choose the column the model should predict. 

#### **Requirements** 

- Present available columns as target candidates. 

- Use the selected column as the classification label. 

- Validate the selected target before training. 

#### **Acceptance Criteria** 

- A valid target can be selected. 

- Unsuitable targets fail gracefully. 

- Relevant validation errors are communicated. 

### **FR-04: Model Training** 

The platform must train a baseline classification model. 

#### **Requirements** 

- Use a Decision Tree Classifier. 

- Separate data into training and test subsets. 

- Preprocess missing numerical and categorical feature values. 

- Encode categorical features where required. 

- Use a reproducible random seed for the split. 

#### **Acceptance Criteria** 

- Suitable data can be used for training. 

- Preprocessing is applied before evaluation. 

- Training errors are understandable. 

### **FR-05: Model Evaluation** 

Display metrics that help users understand model performance. 

#### **Requirements** 

- Calculate accuracy. 

- Calculate weighted precision. 

- Calculate weighted recall. 

- Calculate weighted F1 score. 

- Display metrics after successful training. 

DatasetPassport PRD  •  Page 4 

#### **Acceptance Criteria** 

- Metrics are produced by the trained model. 

- Values correspond to held-out test data. 

- Results are not presented as a guarantee of real-world performance. 

### **FR-06: Experiment History** 

Users can review experiments performed during the current backend session. 

#### **Requirements** 

- Record successful experiment results. 

- Include the target column and evaluation metrics. 

- Display recorded experiments in the frontend. 

#### **Acceptance Criteria** 

- Successful runs appear in history. 

- Multiple runs can be listed. 

- The temporary nature of history is documented. 

Current limitation: Experiment records are stored in memory and are lost when the backend restarts. 

## **7. Non-Functional Requirements** 

### **Performance** 

- Support uploads up to 10 MB. 

- Complete profiling and baseline training in a reasonable time for small datasets on a typical development computer. 

### **Usability** 

- Provide a simple, beginner-friendly interface. 

- Use clear labels for upload, profiling, training, and results. 

- Present errors in understandable language. 

### **Reliability** 

- Validate uploaded data before processing. 

- Handle missing values and common data-format issues where supported. 

- Avoid exposing raw tracebacks as normal user-facing errors. 

### **Security and Privacy** 

- Validate uploaded files and their contents. 

- Avoid logging sensitive dataset contents unnecessarily. 

- Treat uploaded data as potentially sensitive. 

- Do not claim authentication or production-grade data protection in the current version. 

### **Maintainability** 

- Keep frontend and backend responsibilities separated. 

- Use documented API endpoints. 

- Organize code into understandable files and modules. 

DatasetPassport PRD  •  Page 5 

## **8. User Workflow** 

1. Open DatasetPassport in a browser. 

2. Upload a CSV dataset. 

3. Select Profile Dataset to inspect its structure. 

4. Review row counts, column information, and missing values. 

5. Select a suitable target column. 

6. Select Train Model. 

7. Review accuracy, precision, recall, and F1 score. 

8. Review the experiment in experiment history. 

9. Upload another dataset or run another experiment as needed. 

## **9. Sample Dataset** 

The project includes the demonstration file sample_data/student_data.csv. 

|**Column**|**Description**|**Example**|
|---|---|---|
|**study_hours**|Hours spent studying|4.5|
|**attendance**|Attendance percentage|85|
|**passed**|Classification target|Yes|



The sample contains 20 synthetic records. It demonstrates the workflow and does not represent real student outcomes or establish meaningful predictive performance. 

For the demonstration, select passed as the target column. The model uses the other columns as input features. 

## **10. Technical Architecture** 

### **Frontend** 

- React: Builds the interactive user interface. 

- JavaScript: Handles client-side application logic. 

- Vite: Runs the frontend development server. 

- CSS: Styles the application. 

### **Backend** 

- Python: Implements data processing and API logic. 

- FastAPI: Exposes HTTP endpoints. 

- Pandas: Reads and profiles CSV datasets. 

- Scikit-learn: Handles preprocessing, training, and evaluation. 

- Uvicorn: Runs the FastAPI application. 

### **Main API Endpoints** 

|**Endpoint**|**Purpose**|
|---|---|
|**GET /**|Check whether the backend is responding|
|**POST /api/profile**|Profile an uploaded dataset|
|**POST /api/train**|Train and evaluate a classification model|
|**GET /api/experiments**|Retrieve current experiment history|



DatasetPassport PRD  •  Page 6 

Request and response formats are defined by the backend and can be inspected through FastAPI interactive documentation at /docs. 

## **11. Assumptions and Constraints** 

- Users have Python and Node.js installed for local development. 

- The application is initially run locally. 

- Input data is supplied in CSV format. 

- Training is limited to supported classification tasks. 

- Dataset size and data quality affect training success. 

- Experiment history is temporary. 

- Results depend on the dataset, selected target, preprocessing, and train/test split. 

## **12. Risks and Mitigations** 

|**Risk**|**Mitigation**|
|---|---|
|**Invalid or malformed CSV**|Validate input and return clear errors|
|**Missing values**|Apply supported preprocessing and report missingness|
|**Too few examples or unsuitable target labels**|Validate training data before fitting|
|**Misinterpretation of metrics**|Explain that scores do not guarantee generalization|
|**Experiment history lost after restart**|Document limitation and plan persistent storage|
|**Sensitive information in uploaded data**|Encourage non-sensitive datasets and minimize<br>unnecessary logging|



## **13. Future Enhancements** 

### **Phase 2 — Reproducibility** 

- Calculate a SHA-256 fingerprint for each uploaded dataset. 

- Store fingerprints with experiment records. 

- Record model parameters, preprocessing settings, and dataset metadata. 

- Add persistent storage using SQLite or PostgreSQL. 

### **Phase 3 — Improved Analysis** 

- Add data visualizations and class-distribution summaries. 

- Add configurable train/test splits. 

- Support additional classification algorithms. 

- Add confusion matrices and feature-importance summaries. 

- Improve validation for imbalanced or very small datasets. 

### **Phase 4 — Advanced Platform** 

- Add user accounts and experiment ownership. 

- Add dataset and experiment comparison. 

- Add exportable experiment reports. 

- Support regression tasks and additional dataset formats. 

- Prepare secure deployment and monitoring. 

DatasetPassport PRD  •  Page 7 

## **14. Definition of Done** 

- ☐ The frontend and backend run locally using documented setup. 

- ☐ Users can upload a valid CSV dataset. 

- ☐ Dataset profiling displays correct summary information. 

- ☐ Users can select a target column. 

- ☐ The application trains a baseline classifier on suitable data. 

- ☐ Evaluation metrics are displayed after training. 

- ☐ Successful experiments appear in session history. 

- ☐ Invalid input and training errors are handled clearly. 

- ☐ The sample dataset and setup instructions are included. 

- ☐ Known limitations are documented. 

## **15. Summary** 

DatasetPassport provides a beginner-friendly environment for exploring datasets and running baseline machine learning experiments. Its first version focuses on uploading data, profiling it, training a classification model, and reviewing evaluation results. 

Future development should prioritize persistent experiment storage, SHA-256 dataset fingerprinting, improved data-quality insights, and stronger reproducibility. 

**Product vision:** Help users move from raw datasets to understandable, trackable machine learning experiments in one place. 

DatasetPassport PRD  •  Page 8 

