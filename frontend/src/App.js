import './App.css';
import { useState, useRef, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [messages, setMessages] = useState([]);
  const [currInput, setCurrInput] = useState("");
  const [convID, setConvID] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const client = axios.create({ 
    baseURL: 'http://localhost:8000'
  });

  function handleChange(e) {
    setCurrInput(e.target.value)
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setIsLoading(true);
    setMessages([
      ...messages, 
      {"role": "user", "content": currInput},
      {"role": "assistant", "content": "Assistant is thinking..."}
    ]);

    const userMessage = currInput;
    setCurrInput("");

    try {
      // Send user input to backend
      const response = await client.post('/chat', {
        message: userMessage, 
        conversation_id: "1"
      });

      setIsLoading(false);

      // Update messages with user message and assistant response
      setMessages(prev => [
        ...prev.slice(0, -1),  // Remove "thinking" message
        {"role": "assistant", "content": response.data.response}
      ]);
    } catch (error) {
      console.error(`Error occured: ${error}`);

      setMessages(prev => [
        ...prev.slice(0, -1),
        {"role": "assistant", "content": "Sorry, I've encountered an error. Please try again."}
      ]);

      setIsLoading(false);
    }
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="App">
      <h1>Academic Assistant</h1>
      <div className="chatBox">
        <ul className="showMessages">
          {messages.map((message, index) => (
            <li key={index} className={message.role}>{message.content}</li>
          ))}
          <div ref={messagesEndRef} />
        </ul>

        <form onSubmit={handleSubmit}>
          <label>
            <input
              type="text"
              value={currInput}
              onChange={handleChange}
              disabled={isLoading}
            />
            <button type="submit" disabled={isLoading}>Submit</button>
          </label>
        </form>
      </div>
    </div>
  );
}

export default App;