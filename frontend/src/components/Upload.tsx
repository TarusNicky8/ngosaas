// frontend/components/Upload.tsx
import React, { useState } from 'react';
import { uploadDocument } from '../services/api';

interface UploadProps {
  onUploadSuccess: () => void;
}

const Upload: React.FC<UploadProps> = ({ onUploadSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState('');
  const token = localStorage.getItem('token') || '';

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    try {
      await uploadDocument('Sample Title', 'Sample Org', file, token);
      setMessage('Upload successful');
      setFile(null);
      onUploadSuccess();
    } catch (error) {
      setMessage('Upload failed');
      console.error(error);
    }
  };

  return (
    <div>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload} disabled={!file}>
        Upload
      </button>
      {message && <p>{message}</p>}
    </div>
  );
};

export default Upload;
