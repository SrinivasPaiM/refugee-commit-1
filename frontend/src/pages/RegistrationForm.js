import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function RegistrationForm() {
  const [name, setName] = useState('');
  const [country, setCountry] = useState('');
  const [preferredJob, setPreferredJob] = useState('');
  const [formerExperience, setFormerExperience] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    const userData = {
      name,
      country,
      preferredJob,
      formerExperience: formerExperience.split(',').map((exp) => exp.trim()),
    };
    localStorage.setItem('userData', JSON.stringify(userData));
    navigate('/results');
  };

  return (
    <div>
      <h1>Registration Form</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Name:
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </label>
        <br />
        <label>
          Country of Origin:
          <input
            type="text"
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            required
          />
        </label>
        <br />
        <label>
          Preferred Job:
          <input
            type="text"
            value={preferredJob}
            onChange={(e) => setPreferredJob(e.target.value)}
            required
          />
        </label>
        <br />
        <label>
          Former Job Experience (comma-separated):
          <input
            type="text"
            value={formerExperience}
            onChange={(e) => setFormerExperience(e.target.value)}
            required
          />
        </label>
        <br />
        <button type="submit">Submit</button>
      </form>
    </div>
  );
}

export default RegistrationForm;
