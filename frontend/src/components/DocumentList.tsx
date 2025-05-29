// frontend/components/DocumentList.tsx
import React from 'react';

interface Document {
  id: number;
  filename: string;
  grantee_id: number;
}

interface DocumentListProps {
  documents: Document[];
  onSelect: (docId: number) => void;
}

const DocumentList: React.FC<DocumentListProps> = ({ documents, onSelect }) => {
  return (
    <ul>
      {documents.map((doc) => (
        <li key={doc.id}>
          <button onClick={() => onSelect(doc.id)}>{doc.filename}</button>
        </li>
      ))}
    </ul>
  );
};

export default DocumentList;
