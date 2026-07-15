import React, { useEffect, useState, useRef } from 'react';
import { useLocation } from 'wouter';
import { useInterviewStore } from '@/store/useInterviewStore';
import { InterviewLayout } from '@/components/layouts/InterviewLayout';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { 
  Play, 
  Send, 
  Sparkles, 
  Terminal, 
  BookOpen, 
  Bot, 
  User, 
  Mic, 
  MicOff,
  CornerDownLeft,
  ChevronRight,
  Code,
  MessageSquareText
} from 'lucide-react';
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable';

export default function InterviewSession() {
  const [, setLocation] = useLocation();
  const { 
    currentSession, 
    messages, 
    addMessage, 
    activeQuestion,
    code,
    setCode,
    language,
    consoleOutput,
    setConsoleOutput,
    isListening,
    updateStreamText,
    commitStreamMessage,
    isStreamingResponse,
    currentStreamText
  } = useInterviewStore();

  const [inputVal, setInputVal] = useState('');
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentStreamText]);

  // If no session active, redirect back
  if (!currentSession) {
    return (
      <div className="h-screen flex items-center justify-center">
        <Button onClick={() => setLocation('/interviews/new')}>Create New Interview</Button>
      </div>
    );
  }

  // Simulate AI Streaming Response on User Message
  const handleSendMessage = () => {
    if (!inputVal.trim() || isStreamingResponse) return;
    
    // 1. Add User Message
    addMessage({
      sender: 'user',
      text: inputVal,
    });
    setInputVal('');

    // 2. Mock AI Stream
    setTimeout(() => {
      let fullReply = "Thanks for sharing that approach. Let's break down the execution logic. Specifically, how do you plan to handle potential race conditions when updating the sliding-window counters concurrently? What synchronization patterns could we introduce?";
      if (currentSession.type === 'behavioral') {
        fullReply = "That sounds like a challenging situation. How did you align the stakeholders on the final resolution path, and what specific compromises or tradeoffs did you have to negotiate during the design review?";
      }

      let currentIdx = 0;
      const interval = setInterval(() => {
        if (currentIdx < fullReply.length) {
          updateStreamText(fullReply.slice(0, currentIdx + 1));
          currentIdx += 3; // Speeds up the typing tick
        } else {
          clearInterval(interval);
          commitStreamMessage();
        }
      }, 30);
    }, 800);
  };

  // Compile / Run Code simulation
  const handleRunCode = () => {
    setConsoleOutput('Compiling code bundle...');
    setTimeout(() => {
      setConsoleOutput('Running sliding-window concurrency test suites...\n\n[PASS] Test Case 1: Simple Rate Limits\n[PASS] Test Case 2: Concurrent API Spikes\n[FAIL] Test Case 3: Distributed Synchronization Ticks (Network latency mismatch)\n\n3/4 Tests Passed. Evaluated with latency spikes.');
    }, 1200);
  };

  return (
    <InterviewLayout>
      <ResizablePanelGroup direction="horizontal" className="h-full border-t border-border">
        {/* Left Side: Question Details and Chat Transcript */}
        <ResizablePanel defaultSize={45} minSize={30}>
          <ResizablePanelGroup direction="vertical">
            
            {/* Question Details Panel */}
            <ResizablePanel defaultSize={40} minSize={25}>
              <div className="h-full flex flex-col bg-card select-text">
                <div className="h-10 border-b border-border flex items-center px-4 shrink-0 bg-muted/40 font-semibold text-xs select-none gap-2">
                  <BookOpen className="h-3.5 w-3.5 text-muted-foreground" />
                  <span>Problem Description</span>
                </div>
                <div className="flex-1 overflow-y-auto p-5 space-y-4">
                  {activeQuestion && (
                    <>
                      <h3 className="text-lg font-bold text-foreground">{activeQuestion.title}</h3>
                      <div className="text-sm leading-relaxed text-muted-foreground whitespace-pre-wrap">
                        {activeQuestion.description}
                      </div>
                    </>
                  )}
                  
                  {/* Tips Alert */}
                  <div className="p-3.5 bg-violet-500/5 border border-violet-500/10 rounded-lg text-xs flex items-start gap-2.5 select-none">
                    <Sparkles className="h-4 w-4 text-violet-500 shrink-0 mt-0.5" />
                    <div className="space-y-1">
                      <p className="font-semibold text-violet-700 dark:text-violet-300">AI Mentor Tip</p>
                      <p className="text-muted-foreground">You can communicate verbally by turning on 'AI Listening' or type in the chat below. Describe your tradeoffs aloud.</p>
                    </div>
                  </div>
                </div>
              </div>
            </ResizablePanel>

            <ResizableHandle withHandle />

            {/* AI Chat & Transcript Panel */}
            <ResizablePanel defaultSize={60} minSize={35}>
              <div className="h-full flex flex-col bg-background">
                {/* Panel Header */}
                <div className="h-10 border-b border-border flex items-center justify-between px-4 shrink-0 bg-muted/40 font-semibold text-xs select-none">
                  <div className="flex items-center gap-2">
                    <MessageSquareText className="h-3.5 w-3.5 text-muted-foreground" />
                    <span>AI Interviewer & Transcript</span>
                  </div>
                  {isListening && (
                    <div className="flex items-center gap-1 text-[10px] text-emerald-600 dark:text-emerald-400 font-bold tracking-wide uppercase">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
                      <span>Live Mic Active</span>
                    </div>
                  )}
                </div>

                {/* Messages Timeline */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4 select-text">
                  {messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex gap-3 max-w-[85%] ${
                        msg.sender === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
                      }`}
                    >
                      <div className={`w-6 h-6 rounded-md border flex items-center justify-center shrink-0 text-xs select-none ${
                        msg.sender === 'user' 
                          ? 'bg-muted border-border text-foreground' 
                          : 'bg-foreground border-transparent text-background'
                      }`}>
                        {msg.sender === 'user' ? <User className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
                      </div>
                      <div className={`p-3 rounded-lg text-xs leading-relaxed ${
                        msg.sender === 'user'
                          ? 'bg-foreground/5 text-foreground border border-border'
                          : 'bg-card text-foreground border border-border'
                      }`}>
                        {msg.text}
                      </div>
                    </div>
                  ))}

                  {/* Streaming indicator */}
                  {isStreamingResponse && (
                    <div className="flex gap-3 max-w-[85%] mr-auto">
                      <div className="w-6 h-6 rounded-md bg-foreground text-background flex items-center justify-center shrink-0 text-xs select-none">
                        <Bot className="h-3.5 w-3.5" />
                      </div>
                      <div className="p-3 rounded-lg text-xs leading-relaxed bg-card text-foreground border border-border">
                        {currentStreamText}
                        <span className="inline-block w-1.5 h-3.5 bg-foreground/60 ml-0.5 animate-pulse align-middle" />
                      </div>
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </div>

                {/* Chat Inputs */}
                <div className="p-3 border-t border-border shrink-0 bg-card">
                  <div className="relative flex items-center rounded-full border border-border bg-background focus-within:border-foreground/35 px-2 py-0.5 select-none">
                    <Input
                      placeholder={isListening ? "Mic is listening... or type here..." : "Ask a question, propose solution..."}
                      value={inputVal}
                      onChange={(e) => setInputVal(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                      className="border-transparent focus-visible:ring-0 text-xs h-8 shadow-none flex-1 bg-transparent placeholder:text-muted-foreground/65"
                    />
                    <div className="flex items-center gap-1">
                      <Button 
                        onClick={handleSendMessage} 
                        size="icon" 
                        className="h-7 w-7 rounded-full bg-foreground text-background hover:bg-foreground/90 shrink-0"
                      >
                        <Send className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                  <div className="flex items-center justify-between mt-2 px-1 text-[10px] text-muted-foreground select-none font-medium">
                    <span>Press Enter to send</span>
                    <span>AI responses stream in real-time</span>
                  </div>
                </div>
              </div>
            </ResizablePanel>

          </ResizablePanelGroup>
        </ResizablePanel>

        <ResizableHandle withHandle />

        {/* Right Side: Monaco Code Editor and Execution Console */}
        <ResizablePanel defaultSize={55} minSize={30}>
          {currentSession.type === 'coding' ? (
            <ResizablePanelGroup direction="vertical">
              
              {/* Code Editor Panel */}
              <ResizablePanel defaultSize={70} minSize={40}>
                <div className="h-full flex flex-col bg-card select-none">
                  {/* Editor Header Toolbar */}
                  <div className="h-10 border-b border-border flex items-center justify-between px-4 shrink-0 bg-muted/40 font-semibold text-xs">
                    <div className="flex items-center gap-2">
                      <Code className="h-3.5 w-3.5 text-muted-foreground" />
                      <span>workspace.ts</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono text-muted-foreground px-2 py-0.5 border border-border bg-background rounded-md capitalize">
                        {language}
                      </span>
                    </div>
                  </div>
                  {/* Editor Textarea with Syntax Mocking */}
                  <div className="flex-1 p-0 relative">
                    <textarea
                      value={code}
                      onChange={(e) => setCode(e.target.value)}
                      className="w-full h-full bg-background/30 p-5 font-mono text-xs leading-relaxed resize-none border-0 outline-none focus:ring-0 select-text"
                      spellCheck="false"
                    />
                  </div>
                </div>
              </ResizablePanel>

              <ResizableHandle withHandle />

              {/* Console Output Panel */}
              <ResizablePanel defaultSize={30} minSize={20}>
                <div className="h-full flex flex-col bg-card select-none">
                  {/* Console Header */}
                  <div className="h-10 border-b border-border flex items-center justify-between px-4 shrink-0 bg-muted/40 font-semibold text-xs">
                    <div className="flex items-center gap-2">
                      <Terminal className="h-3.5 w-3.5 text-muted-foreground" />
                      <span>Execution Console</span>
                    </div>
                    <Button 
                      onClick={handleRunCode}
                      className="rounded-full gap-1 h-7 text-[10px] px-3 bg-[#4285F4] hover:bg-[#3b77db] text-white border-0 shrink-0 font-semibold"
                    >
                      <Play className="h-2.5 w-2.5 fill-current" />
                      Run Code
                    </Button>
                  </div>
                  {/* Console Log Area */}
                  <div className="flex-1 overflow-y-auto p-4 bg-background/25 text-xs font-mono leading-relaxed whitespace-pre-wrap select-text text-muted-foreground">
                    {consoleOutput}
                  </div>
                </div>
              </ResizablePanel>

            </ResizablePanelGroup>
          ) : (
            // Non-coding (Behavioral / System Design) custom full screen overview
            <div className="h-full flex flex-col items-center justify-center p-8 bg-card select-none text-center space-y-6">
              <div className="w-16 h-16 rounded-full bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 flex items-center justify-center animate-pulse">
                <Bot className="h-8 w-8" />
              </div>
              <div className="max-w-md space-y-2">
                <h3 className="text-lg font-bold">Active Audio Interviewing Workspace</h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  This workspace evaluates your answers based on system design paradigms or structural behavioral metrics (STAR method). Make sure to talk through your points.
                </p>
              </div>
              
              <div className="w-full max-w-sm border border-border bg-background p-4 rounded-xl flex items-center justify-between select-text text-left">
                <div className="space-y-0.5">
                  <p className="text-xs font-semibold">Active AI Audio Model</p>
                  <p className="text-[10px] text-muted-foreground">GPT-4o Adaptive Voice (realtime-low-latency)</p>
                </div>
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping shrink-0" />
              </div>
            </div>
          )}
        </ResizablePanel>
      </ResizablePanelGroup>
    </InterviewLayout>
  );
}
export { InterviewSession };
