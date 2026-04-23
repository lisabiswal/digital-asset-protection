# Implementation Plan: Digital Sports Media Asset Protection System

## Overview

This implementation plan converts the visual fingerprinting system design into actionable Python development tasks. The system uses FastAPI backend on Cloud Run with React frontend, implementing a pipeline of Upload → Extract Frames → CNN Embeddings → FAISS Query → Ranked Results using MobileNetV2 and FAISS for similarity search.

## Tasks

- [x] 1. Set up project structure and core dependencies
  - Create backend directory structure with FastAPI project
  - Set up requirements.txt with core dependencies (FastAPI, OpenCV, PyTorch, FAISS, SQLite)
  - Create main.py with basic FastAPI app and health endpoint
  - Set up GCS client configuration and service account handling
  - _Requirements: System must handle video uploads and provide health status_

- [ ] 2. Implement frame extraction service
  - [ ] 2.1 Create frame extraction module using OpenCV
    - Write `utils/frames.py` with `extractFrames()` function
    - Implement 1fps frame extraction from video files
    - Add video metadata extraction (duration, frame count)
    - _Requirements: Extract frames at 1fps intervals for visual fingerprinting_
  
  - [ ]* 2.2 Write unit tests for frame extraction
    - Test frame extraction with sample video files
    - Validate frame count matches expected duration
    - Test error handling for corrupted videos
    - _Requirements: Frame extraction must be reliable and consistent_

- [ ] 3. Implement CNN embedding generation
  - [ ] 3.1 Create embedding service using MobileNetV2
    - Write `utils/embeddings.py` with `generateEmbedding()` function
    - Implement frame preprocessing to 224x224 ImageNet format
    - Load MobileNetV2 pretrained model and generate 1280-dim embeddings
    - Add L2 normalization for cosine similarity
    - _Requirements: Generate normalized visual embeddings for similarity search_
  
  - [ ]* 3.2 Write property test for embedding normalization
    - **Property 2: Embedding Normalization**
    - **Validates: All embeddings have L2 norm = 1.0 and dimension = 1280**
    - _Requirements: Embeddings must be properly normalized for accurate similarity_
  
  - [ ]* 3.3 Write unit tests for embedding generation
    - Test embedding generation with known image inputs
    - Validate embedding dimensions and normalization
    - Test batch processing functionality
    - _Requirements: Embedding generation must be consistent and accurate_

- [ ] 4. Implement FAISS similarity search
  - [ ] 4.1 Create FAISS index management
    - Write `utils/faiss_index.py` with `FAISSIndex` class
    - Implement index loading from disk
    - Add similarity query functionality with configurable k-neighbors
    - _Requirements: Fast similarity search against indexed video embeddings_
  
  - [ ]* 4.2 Write property test for similarity score bounds
    - **Property 3: Similarity Score Bounds**
    - **Validates: All similarity scores are between 0.0 and 1.0**
    - _Requirements: Similarity sc3ores must be valid cosine similarity values_

- [ ] 5. Checkpoint - Core pipeline validation
  - Ensure frame extraction, embedding generation, and FAISS query work together
  - Test with sample video files end-to-end
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement match aggregation and ranking
  - [ ] 6.1 Create match aggregation service
    - Write `utils/match_aggregator.py` with aggregation logic
    - Implement frame-level to video-level match aggregation
    - Add confidence calculation based on match ratio and similarity
    - Implement result ranking by confidence and similarity scores
    - _Requirements: Aggregate frame matches into ranked video results_
  
  - [ ]* 6.2 Write property test for match aggregation correctness
    - **Property 4: Match Aggregation Correctness**
    - **Validates: Video matches correctly aggregate frame-level matches**
    - _Requirements: Match aggregation must preserve accuracy and consistency_
  
  - [ ]* 6.3 Write property test for confidence calculation consistency
    - **Property 5: Confidence Calculation Consistency**
    - **Validates: Confidence levels match expected thresholds (strong/partial/weak)**
    - _Requirements: Confidence calculation must be consistent and meaningful_

- [ ] 7. Implement data models and validation
  - [ ] 7.1 Create Pydantic models for API schemas
    - Write `models/schemas.py` with VideoMetadata, FrameMatch, VideoMatch models
    - Implement validation rules for all data structures
    - Add request/response models for all API endpoints
    - _Requirements: Type-safe data models with proper validation_
  
  - [ ]* 7.2 Write unit tests for data model validation
    - Test validation rules for all models
    - Test edge cases and error conditions
    - Validate serialization/deserialization
    - _Requirements: Data models must enforce business rules and constraints_

- [ ] 8. Implement GCS integration
  - [ ] 8.1 Create GCS upload and download utilities
    - Write `utils/gcs.py` with upload/download functions
    - Implement video file storage to GCS buckets
    - Add error handling for storage failures and quota limits
    - _Requirements: Reliable cloud storage for uploaded videos_
  
  - [ ]* 8.2 Write integration tests for GCS operations
    - Test file upload and download operations
    - Test error handling for network issues
    - Validate file integrity after upload/download
    - _Requirements: GCS integration must be reliable and handle failures gracefully_

- [ ] 9. Implement core FastAPI endpoints
  - [ ] 9.1 Create video upload endpoint
    - Implement `POST /upload` with multipart file handling
    - Add file validation (format, size limits)
    - Store uploaded videos to GCS and return upload_id
    - _Requirements: Accept video uploads and provide unique identifiers_
  
  - [ ] 9.2 Create video processing endpoint
    - Implement `POST /process/{upload_id}` for frame extraction and embedding
    - Add async processing with status tracking
    - Store embeddings for subsequent scanning
    - _Requirements: Process uploaded videos and generate embeddings_
  
  - [ ] 9.3 Create similarity scanning endpoint
    - Implement `POST /scan` for FAISS similarity search
    - Add match aggregation and ranking logic
    - Store scan results for retrieval
    - _Requirements: Execute similarity search and rank results_
  
  - [ ] 9.4 Create match results endpoint
    - Implement `GET /matches?upload_id=X` for result retrieval
    - Return ranked matches with metadata and confidence scores
    - Add pagination for large result sets
    - _Requirements: Provide ranked match results with detailed metadata_

- [ ] 10. Checkpoint - API integration testing
  - Test complete API workflow: upload → process → scan → results
  - Validate all endpoints with real video files
  - Ensure error handling works across all endpoints
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Implement SQLite metadata storage
  - [ ] 11.1 Create database schema and connection management
    - Write database initialization script with videos table schema
    - Implement connection pooling and transaction management
    - Add video metadata CRUD operations
    - _Requirements: Persistent storage for video metadata and FAISS index mappings_
  
  - [ ]* 11.2 Write integration tests for database operations
    - Test video metadata storage and retrieval
    - Test transaction handling and rollback scenarios
    - Validate data integrity and constraints
    - _Requirements: Database operations must be reliable and maintain data integrity_

- [ ] 12. Create dataset indexing script
  - [ ] 12.1 Implement offline dataset processing
    - Write `scripts/build_index.py` for batch video processing
    - Process dataset videos to generate FAISS index
    - Store video metadata in SQLite database
    - Map FAISS indices to video IDs and frame positions
    - _Requirements: Pre-process dataset videos for similarity search_
  
  - [ ]* 12.2 Write property test for frame extraction consistency
    - **Property 1: Frame Extraction Consistency**
    - **Validates: Frame count matches video duration at 1fps**
    - _Requirements: Frame extraction must be consistent across all videos_

- [ ] 13. Implement Docker containerization
  - [ ] 13.1 Create production Dockerfile
    - Write multi-stage Dockerfile with Python 3.11 slim base
    - Bundle pre-built FAISS index and SQLite database in image
    - Configure container for Cloud Run deployment
    - Optimize image size and startup time
    - _Requirements: Containerized deployment with embedded dataset_
  
  - [ ] 13.2 Create deployment scripts
    - Write Cloud Run deployment configuration
    - Set up environment variables and service account
    - Configure memory, CPU, and timeout settings
    - _Requirements: Automated deployment to Google Cloud Run_

- [ ] 14. Implement error handling and logging
  - [ ] 14.1 Add comprehensive error handling
    - Implement error handling for all processing stages
    - Add proper HTTP status codes and error messages
    - Handle GCS failures, FAISS errors, and processing timeouts
    - _Requirements: Graceful error handling with informative messages_
  
  - [ ] 14.2 Add structured logging
    - Implement structured logging for all operations
    - Add performance metrics and timing information
    - Configure log levels for development and production
    - _Requirements: Comprehensive logging for monitoring and debugging_

- [ ] 15. Performance optimization and tuning
  - [ ] 15.1 Optimize processing pipeline
    - Implement batch processing for multiple frames
    - Add caching for frequently accessed data
    - Optimize memory usage during video processing
    - _Requirements: Efficient processing within Cloud Run resource limits_
  
  - [ ] 15.2 Tune similarity matching thresholds
    - Test and adjust MATCH_THRESHOLD for optimal accuracy
    - Calibrate confidence calculation parameters
    - Validate performance with dataset variants (exact, trimmed, edited)
    - _Requirements: Accurate detection of exact copies, trimmed clips, and edited versions_

- [ ] 16. Final integration and deployment
  - [ ] 16.1 Build and test production Docker image
    - Build final Docker image with all components
    - Test container startup and health checks
    - Validate FAISS index loading and API functionality
    - _Requirements: Production-ready container with all features_
  
  - [ ] 16.2 Deploy to Cloud Run and validate
    - Deploy container to Google Cloud Run
    - Test all endpoints on live deployment
    - Validate performance and error handling
    - _Requirements: Fully functional deployment on Google Cloud Run_
  
  - [ ]* 16.3 Write end-to-end integration tests
    - Test complete workflow with various video types
    - Validate detection accuracy with dataset variants
    - Test error scenarios and recovery
    - _Requirements: Comprehensive validation of system functionality_

- [ ] 17. Final checkpoint - System validation
  - Ensure all core functionality works end-to-end
  - Validate detection of exact copies, trimmed clips, and edited versions
  - Confirm system meets 5-day prototype requirements
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP delivery
- Each task references specific system requirements for traceability
- Checkpoints ensure incremental validation and early issue detection
- Property tests validate universal correctness properties from the design
- Unit tests validate specific examples and edge cases
- Focus on Python implementation using FastAPI, OpenCV, PyTorch, and FAISS
- System targets detection of exact copies, trimmed clips, and edited versions within 5-day prototype timeline