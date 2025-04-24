import React, { useEffect, useState } from 'react';

function ResultsPage() {
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null); // Add error state
  const userData = JSON.parse(localStorage.getItem('userData'));

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const response = await fetch('http://localhost:5000/similarity', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_experience: userData.formerExperience,
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        setResults(data);
      } catch (err) {
        setError(err.message); // Set error message
      }
    };

    fetchResults();
  }, [userData]);

  if (error) {
    return <div>Error: {error}</div>; // Display error message
  }

  if (!results) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h1>Welcome, {userData.name}</h1>
      <h2>Top Match</h2>
      <p>
        {results.matched_job} in {results.matched_state} (Score: {results.score})
      </p>
      <h2>Top Suggestions</h2>
      <ul>
        {results.top_matches.map((match, index) => (
          <li key={index}>
            {match.job} in {match.state} (Score: {match.score})
          </li>
        ))}
      </ul>
    </div>
  );
}

export default ResultsPage;
