import React, { useState } from "react";

function App() {
  // State to store the selected file
  const [selectedFile, setSelectedFile] = useState(null);

  // State to store the server's response
  const [responseData, setResponseData] = useState(null);

  // State to store any error messages
  const [error, setError] = useState(null);

  // State to track loading status
  const [loading, setLoading] = useState(false);

  // State to track upload progress
  const [uploadProgress, setUploadProgress] = useState(0);

  // Function to handle file selection
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Check file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        setError("File size must be less than 10MB");
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
      setError(null);
    }
  };

  // Function to handle file upload
  const handleUpload = async () => {
    if (!selectedFile) {
      setError("Please select a file before uploading.");
      return;
    }

    setLoading(true);
    setError(null);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      console.log("Starting file upload...");
      console.log("File details:", {
        name: selectedFile.name,
        size: selectedFile.size,
        type: selectedFile.type
      });

      const response = await fetch("http://localhost:8000/api/upload/document", {
        method: "POST",
        body: formData,
        headers: {
          'Accept': 'application/json',
        },
        credentials: 'include'
      });

      console.log("Response status:", response.status);
      const data = await response.json();
      console.log("Response data:", data);

      if (!response.ok) {
        throw new Error(data.detail || `Upload failed with status ${response.status}`);
      }

      setResponseData(data);
    } catch (error) {
      console.error("Detailed error:", error);
      if (error.message.includes("Failed to fetch")) {
        setError("Unable to connect to the server. Please check if the server is running.");
      } else {
        setError(error.message || "An error occurred while uploading the file.");
      }
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div style={{ padding: "20px", maxWidth: "800px", margin: "0 auto" }}>
      <h1>Intelligent Document Insights Portal</h1>

      {/* File Input */}
      <div style={{ marginBottom: "20px" }}>
        <div style={{ marginBottom: "10px" }}>
          <input 
            type="file" 
            accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg" 
            onChange={handleFileChange}
            disabled={loading}
            style={{ marginRight: "10px" }}
          />
          <button 
            onClick={handleUpload} 
            disabled={loading || !selectedFile}
            style={{
              padding: "8px 16px",
              backgroundColor: loading ? "#ccc" : "#0078d4",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: loading ? "not-allowed" : "pointer"
            }}
          >
            {loading ? "Uploading..." : "Upload and Process"}
          </button>
        </div>

        {/* Upload Progress */}
        {loading && (
          <div style={{ marginTop: "10px" }}>
            <div style={{ 
              width: "100%", 
              height: "4px", 
              backgroundColor: "#f0f0f0", 
              borderRadius: "2px",
              overflow: "hidden"
            }}>
              <div style={{
                width: `${uploadProgress}%`,
                height: "100%",
                backgroundColor: "#0078d4",
                transition: "width 0.3s ease-in-out"
              }} />
            </div>
            <div style={{ marginTop: "5px", fontSize: "0.9em", color: "#666" }}>
              Uploading: {uploadProgress}%
            </div>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div style={{ 
          color: "#d32f2f", 
          marginBottom: "20px",
          padding: "10px",
          backgroundColor: "#ffebee",
          borderRadius: "4px",
          border: "1px solid #ffcdd2"
        }}>
          {error}
        </div>
      )}

      {/* Response Display */}
      {responseData && (
        <div style={{ 
          marginTop: "20px",
          padding: "20px",
          backgroundColor: "#f5f5f5",
          borderRadius: "4px"
        }}>
          <h2>Analysis Results:</h2>
          <pre style={{ 
            whiteSpace: "pre-wrap",
            wordWrap: "break-word",
            backgroundColor: "white",
            padding: "15px",
            borderRadius: "4px",
            border: "1px solid #e0e0e0"
          }}>
            {JSON.stringify(responseData, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

export default App;
