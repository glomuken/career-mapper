import React, { useState } from 'react';
import axios from 'axios';

const questions = [
  { key: 'name', question: 'What is your name?' },
  { key: 'location', question: 'What country or city are you currently in?' },
  { key: 'industry', question: 'What industry are/were you working in?' },
  { key: 'careerStage', question: 'What is your current career stage (e.g., student, junior, senior, manager)?' },
  { key: 'breakReason', question: 'Why are you planning a break? (Optional)' },
  { key: 'duration', question: 'How long do you expect the break to be (e.g., 3 months, 1 year)?' },
  { key: 'skills', question: 'What are your top 3 skills or areas of expertise?' },
  { key: 'preferredEngagement', question: 'How would you prefer to stay engaged during your break? (e.g., learning, freelance, mentoring, volunteering)' }
];

export default function CareerBreakBot() {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [responses, setResponses] = useState({});
  const [inputValue, setInputValue] = useState('');
  const [plan, setPlan] = useState('');
  const [loading, setLoading] = useState(false);

  const handleNext = async () => {
    const currentKey = questions[currentQuestionIndex].key;
    setResponses(prev => ({ ...prev, [currentKey]: inputValue }));
    setInputValue('');

    if (currentQuestionIndex + 1 < questions.length) {
      setCurrentQuestionIndex(prev => prev + 1);
    } else {
      // All questions answered, send to backend
      setLoading(true);
      try {
        const res = await axios.post('http://localhost:5000/api/career-break-plan', responses);
        setPlan(res.data.plan);
      } catch (err) {
        console.error('Error getting plan:', err);
        setPlan('Something went wrong. Please try again later.');
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="max-w-xl mx-auto p-4 bg-white rounded shadow-md mt-10">
      {!plan && (
        <>
          <h2 className="text-xl font-bold mb-4">Career Break Bot 🤖</h2>
          <p className="mb-2">{questions[currentQuestionIndex].question}</p>
          <input
            className="border p-2 w-full mb-4"
            type="text"
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleNext()}
          />
          <button
            onClick={handleNext}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Next
          </button>
        </>
      )}

      {loading && <p className="text-gray-500 mt-4">Generating your plan...</p>}

      {plan && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold mb-2">Your Personalized Plan:</h3>
          <pre className="bg-gray-100 p-4 whitespace-pre-wrap">{plan}</pre>
        </div>
      )}
    </div>
  );
}
