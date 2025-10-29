import './App.css';
import { useState, useRef, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [messages, setMessages] = useState([]);
  const [currInput, setCurrInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [degreeworksData, setDegreeWorksData] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null)
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
        user_id: "1",
        conversation_id: "1", 
        completed_courses: degreeworksData?.completed_courses || [],
        required: degreeworksData?.requirements || {}
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

  const onFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const onFileUpload = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      // Send form to backend
      const response = await fetch('http://localhost:8000/uploadFile/', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data) {
        setDegreeWorksData(data);
      } else {
        console.log("No degreeworks data.");
      }
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed');
    }

  };

  return (
    <div className="App">
      <h1>Academic Assistant</h1>

      <div className="uploadFile">
        <h3>Upload degreeworks pdf</h3>
        <input type="file" accept=".pdf" onChange={onFileChange} />
        <button onClick={onFileUpload}>Upload!</button>
        { degreeworksData && <div>File received!</div>}
      </div>

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