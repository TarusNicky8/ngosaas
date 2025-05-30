import React, { useState } from 'react';
import { uploadDocument } from '../services/api';

interface UploadProps {
  onUploadSuccess: () => void; // Callback to refresh documents list
}

const Upload: React.FC<UploadProps> = ({ onUploadSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [organization, setOrganization] = useState('');
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const token = localStorage.getItem('token') || '';

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !title || !organization) {
      setMessage("Please fill all fields and select a file.");
      return;
    }

    setUploading(true);
    setMessage(null);

    try {
      // Corrected: Pass title, organization, file, and token as separate arguments
      await uploadDocument(title, organization, file, token);
      setMessage("Document uploaded successfully!");
      setFile(null);
      setTitle('');
      setOrganization('');
      onUploadSuccess(); // Trigger document list refresh
    } catch (error: any) {
      console.error("Upload failed", error);
      setMessage(`Upload failed: ${error.message || 'Unknown error'}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-6 bg-gray-50 rounded-lg shadow-inner">
      {message && (
        <div className={`p-3 rounded-md text-center ${message.includes('successfully') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
          {message}
        </div>
      )}
      <div>
        <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">Document Title</label>
        <input
          type="text"
          id="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g., Annual Report 2024"
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          required
        />
      </div>
      <div>
        <label htmlFor="organization" className="block text-sm font-medium text-gray-700 mb-1">Your Organization</label>
        <input
          type="text"
          id="organization"
          value={organization}
          onChange={(e) => setOrganization(e.target.value)}
          placeholder="e.g., NGO Name Inc."
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          required
        />
      </div>
      <div>
        <label htmlFor="file-upload" className="block text-sm font-medium text-gray-700 mb-1">Upload File</label>
        <input
          type="file"
          id="file-upload"
          onChange={handleFileChange}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
          required
        />
        {file && <p className="mt-2 text-sm text-gray-500">Selected file: {file.name}</p>}
      </div>
      <button
        type="submit"
        disabled={uploading}
        className="w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition duration-150 ease-in-out"
      >
        {uploading ? 'Uploading...' : 'Upload Document'}
      </button>
    </form>
  );
};

export default Upload;
