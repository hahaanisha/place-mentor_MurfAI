/* eslint-disable no-unused-vars */
import { useState, useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import SpeechRecognition, { useSpeechRecognition } from "react-speech-recognition";
import axios from "axios";
import InternalNavbar from "./InternalNavbar";

const InterviewPage = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const questionData = location.state || JSON.parse(localStorage.getItem("CurrentQuestion") || "null");

  const [userAnswer, setUserAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [feedbackRes, setFeedbackRes] = useState(null);
  const [timer, setTimer] = useState(60);
  const [timerActive, setTimerActive] = useState(false);
  const [hasSpoken, setHasSpoken] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);

  const timerRef = useRef(null);
  const Qcount = parseInt(localStorage.getItem("QuestionCount"), 10) || 1;

  const { transcript, listening, resetTranscript, browserSupportsSpeechRecognition } =
    useSpeechRecognition();

  // ===============================
  // 🚀 MURF AUDIO PLAY FUNCTION
  // ===============================
  const playMurfAudio = async (text) => {
    try {
      const response = await fetch("https://api.murf.ai/v1/speech/stream", {
        method: "POST",
        headers: {
          "api-key": "ap2_875ac707-e36c-46a6-af3d-722c2becaa49",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: text,
          voiceId: "Matthew",
          model: "FALCON",
          multiNativeLocale: "en-US",
        }),
      });

      const audioBuffer = await response.arrayBuffer();
      const blob = new Blob([audioBuffer], { type: "audio/mpeg" });
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);

      setTimeout(() => {
        const audio = document.getElementById("questionAudio");
        if (audio) audio.play().catch(() => {});
      }, 300);
    } catch (err) {
      console.error("Murf audio error:", err);
    }
  };

  // Redirect if question missing
  useEffect(() => {
    if (!questionData) {
      alert("No question data found. Redirecting...");
      navigate("/dashboard");
    } else {
      localStorage.setItem("CurrentQuestion", JSON.stringify(questionData));
    }
  }, []);

  // ⏳ Auto speak question ONCE when page opens
  useEffect(() => {
    if (questionData?.question && !hasSpoken) {
      playMurfAudio(questionData.question);
      setHasSpoken(true);
    }
  }, [questionData, hasSpoken]);

  // Timer logic
  useEffect(() => {
    if (timerActive && timer > 0) {
      timerRef.current = setInterval(() => setTimer((prev) => prev - 1), 1000);
    } else if (timer === 0) {
      clearInterval(timerRef.current);
      SpeechRecognition.stopListening();
      setUserAnswer(transcript);
      setTimerActive(false);
    }
    return () => clearInterval(timerRef.current);
  }, [timerActive, timer]);

  if (!browserSupportsSpeechRecognition) {
    return <div className="text-center mt-10">Browser doesn't support Speech Recognition</div>;
  }

  // Submit answer for evaluation
  const feedbackAnalysis = async () => {
    setLoading(true);
    try {
      const resumeSummary = localStorage.getItem("ResumeSummary") || "";

      const response = await axios.post("http://127.0.0.1:5000/evaluate-answer", {
        question: questionData?.question,
        user_answer: userAnswer,
        resume_summary: resumeSummary,
      });

      setFeedbackRes(response.data);

      const questions = JSON.parse(localStorage.getItem("InterviewQuestions")) || [];
      const index = Qcount - 1;
      questions[index] = {
        question: questionData?.question,
        attempted: true,
        marks: response.data?.score || 0,
      };
      localStorage.setItem("InterviewQuestions", JSON.stringify(questions));
    } catch (e) {
      console.error("Error in feedback:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleStartListening = () => {
    resetTranscript();
    setUserAnswer("");
    setTimer(60);
    setTimerActive(true);
    SpeechRecognition.startListening({ continuous: true });
  };

  const handleStopListening = () => {
    SpeechRecognition.stopListening();
    setUserAnswer(transcript);
    setTimerActive(false);
    clearInterval(timerRef.current);
  };

  // Repeat Question with Murf
  const repeatQuestionSpeech = () => {
    if (questionData?.question) playMurfAudio(questionData.question);
  };

  // Next Question
  const nextQuestion = async () => {
    setLoading(true);
    try {
      const storedPlan = localStorage.getItem("InterviewPlan");
      if (!storedPlan) throw new Error("InterviewPlan missing.");

      const parsedPlan = JSON.parse(storedPlan);
      const newCount = Qcount + 1;

      const response = await axios.post("http://127.0.0.1:5000/get-question", {
        sr_no: newCount,
        interview_plan: { interview_plan: parsedPlan },
      });

      localStorage.setItem("QuestionCount", newCount.toString());
      setUserAnswer("");
      resetTranscript();
      setTimer(60);
      setTimerActive(false);
      setFeedbackRes(null);
      setHasSpoken(false);

      navigate("/interview-page", { state: response.data, replace: true });
      window.location.reload();
    } catch (err) {
      console.error("Next question error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <InternalNavbar showQuitButton={true} showHomeButton={false} />

      <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-blue-50 pt-6">
        <audio id="questionAudio">
          {audioUrl && <source src={audioUrl} type="audio/mpeg" />}
        </audio>

        <div className="flex flex-col lg:flex-row gap-6 w-full max-w-6xl mx-auto p-6">
        
          {/* Question Card */}
          <div className="w-full lg:w-1/2 space-y-6">
            <Card className="w-full shadow-lg rounded-xl">
              <CardContent className="p-6 space-y-6">
                <h1 className="text-2xl font-bold text-center text-gray-800">
                  Interview Question
                </h1>
                <p className="text-lg font-medium text-gray-800">
                  {questionData?.question}
                </p>

                <Button
                  onClick={repeatQuestionSpeech}
                  className="mt-4 bg-yellow-600 hover:bg-yellow-500 text-white px-4 py-2 rounded font-bold"
                >
                  🔁 Repeat Question
                </Button>
              </CardContent>
            </Card>

            {/* Transcript Box */}
            <div className="bg-white p-6 rounded-xl shadow-md">
              <h2 className="font-semibold text-xl mb-4 text-gray-800">
                Your Spoken Answer:
              </h2>
              <p className="text-gray-700 whitespace-pre-wrap p-4 bg-gray-50 rounded-lg">
                {transcript || "Start speaking to see transcript..."}
              </p>
            </div>

            {/* Saved Answer */}
            {userAnswer && (
              <div className="bg-green-50 p-6 rounded-xl border border-green-300">
                <h2 className="font-semibold text-xl text-green-800 mb-2">
                  Saved Answer:
                </h2>
                <p className="text-green-800 whitespace-pre-wrap bg-green-100 p-4 rounded-lg">
                  {userAnswer}
                </p>
              </div>
            )}

            {/* Buttons */}
            <div className="flex justify-center gap-6 mt-6 items-center">
              <Button
                onClick={handleStartListening}
                disabled={listening || timerActive}
                className="h-12 text-lg bg-green-600 hover:bg-green-700"
              >
                🎤 Start Speaking
              </Button>

              <Button
                onClick={handleStopListening}
                disabled={!listening}
                className="h-12 text-lg bg-red-600 hover:bg-red-700"
              >
                🛑 Stop & Save
              </Button>

              {timerActive && (
                <span className="text-xl font-mono text-blue-700">
                  ⏱ {String(Math.floor(timer / 60)).padStart(2, "0")}:
                  {String(timer % 60).padStart(2, "0")}
                </span>
              )}
            </div>

            {userAnswer && (
              <div className="flex justify-center mt-6">
                <Button
                  onClick={feedbackAnalysis}
                  disabled={loading}
                  className="h-12 text-lg bg-blue-700 hover:bg-blue-800"
                >
                  {loading ? "Submitting..." : "Submit Answer"}
                </Button>
              </div>
            )}
          </div>

          {/* Feedback Section */}
          {feedbackRes && (
            <div className="w-full lg:w-1/2 bg-blue-50 p-6 rounded-xl border shadow-md">
              <h2 className="text-2xl font-bold text-blue-800 mb-6">
                AI Feedback Summary
              </h2>

              <div className="space-y-4">
                {feedbackRes.feedback && (
                  <div className="bg-white p-4 rounded-lg">
                    <p className="font-semibold text-blue-700">🧠 Feedback:</p>
                    <p>{feedbackRes.feedback}</p>
                  </div>
                )}

                {feedbackRes.correctedAnswer && (
                  <div className="bg-white p-4 rounded-lg">
                    <p className="font-semibold text-blue-700">✅ Corrected Answer:</p>
                    <p>{feedbackRes.correctedAnswer}</p>
                  </div>
                )}

                <div className="grid grid-cols-1 gap-4">
                  <p className="bg-white p-4 rounded-lg">
                    <strong>Repeat Required:</strong>{" "}
                    {feedbackRes.repeatStatus ? "Yes" : "No"}
                  </p>
                  <p className="bg-white p-4 rounded-lg">
                    <strong>Score:</strong> {feedbackRes.score} / 10
                  </p>
                </div>

                <div className="flex gap-4 justify-around mt-4">
                  <Button
                    onClick={repeatQuestionSpeech}
                    className="h-12 text-lg bg-purple-600 hover:bg-purple-700"
                  >
                    Repeat
                  </Button>

                  <Button
                    onClick={nextQuestion}
                    disabled={feedbackRes.score < 6}
                    className="h-12 text-lg bg-purple-600 hover:bg-purple-700"
                  >
                    Next Question
                  </Button>
                </div>

                <p className="text-red-500 text-sm text-center">
                  * Score must be 6 or above to continue
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default InterviewPage;
