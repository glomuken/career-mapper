import React, { useState } from "react";

export default function CareerFitQuestionnaire() {
  const questions = [
    "What is your highest level of education?",
    "Which subjects or fields do you enjoy the most?",
    "What kind of work environment do you prefer?",
    "Do you like working with people, technology, data, or creativity?",
    "What are your strongest skills?",
    "What motivates you most in a career?",
    "Are you willing to travel or relocate for work?"
  ];

  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [input, setInput] = useState("");
  const [results, setResults] = useState("");
  const [location, setLocation] = useState("");

  const handleNext = () => {
    if (input.trim() === "") return;
    setAnswers([...answers, input]);
    setInput("");
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      submitAnswers();
    }
  };

  const submitAnswers = async () => {
    try {
      const res = await fetch("http://localhost:5000/career-fit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers, location })
      });
      const data = await res.json();
      setResults(data.suggestions);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  return (
    <div style={{ background: '#2363eb', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ background: '#fff', borderRadius: '18px', boxShadow: '0 4px 32px rgba(35,99,235,0.10)', padding: '48px 40px', maxWidth: '520px', width: '100%' }}>
        <h2 style={{ color: '#2363eb', fontWeight: 700, fontSize: '2rem', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <i className="fas fa-user-check"></i> Career Fit Questionnaire
        </h2>

        {!results && (
          <>
            {currentIndex === 0 && (
              <input
                type="text"
                placeholder="Enter your location"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                style={{ padding: '14px', marginBottom: '18px', width: '100%', borderRadius: '8px', border: '2px solid #e1e5e9', fontSize: '1rem' }}
              />
            )}

            <p style={{ color: '#174bb3', fontWeight: 600, fontSize: '1.08rem', marginBottom: '10px' }}>{questions[currentIndex]}</p>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              style={{ padding: '14px', width: '100%', borderRadius: '8px', border: '2px solid #e1e5e9', fontSize: '1rem' }}
            />
            <button onClick={handleNext} style={{ marginTop: '18px', background: '#2363eb', color: '#fff', border: 'none', borderRadius: '8px', padding: '14px 32px', fontWeight: 600, fontSize: '1rem', cursor: 'pointer', transition: 'background 0.2s' }}>
              {currentIndex < questions.length - 1 ? <><i className="fas fa-arrow-right"></i> Next</> : <><i className="fas fa-check"></i> Finish</>}
            </button>
          </>
        )}

        {results && (
          <div style={{ marginTop: '32px', background: '#eaf1fb', padding: '24px', borderRadius: '12px', borderLeft: '5px solid #2363eb', color: '#174bb3' }}>
            <h3 style={{ fontWeight: 700, fontSize: '1.2rem', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <i className="fas fa-lightbulb"></i> Recommended Career Fields:
            </h3>
            <p>{results}</p>
          </div>
        )}
      </div>
    </div>
  );
}
