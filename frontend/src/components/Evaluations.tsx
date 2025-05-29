// frontend/components/Evaluations.tsx
import React from 'react';

interface Evaluation {
  id: number;
  comment?: string;
  status?: string;
  reviewer_id: number;
}

interface EvaluationsProps {
  evaluations: Evaluation[];
}

const Evaluations: React.FC<EvaluationsProps> = ({ evaluations }) => {
  if (evaluations.length === 0) {
    return <p>No evaluations yet.</p>;
  }
  return (
    <div>
      <h4>Evaluations</h4>
      <ul>
        {evaluations.map((evalItem) => (
          <li key={evalItem.id}>
            <p>Status: {evalItem.status ?? "N/A"}</p>
            <p>Comment: {evalItem.comment ?? "No comment"}</p>
            <p>Reviewer ID: {evalItem.reviewer_id}</p>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Evaluations;
