import { create } from 'zustand';

export interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  timestamp: Date;
  isStreaming?: boolean;
}

export interface InterviewSession {
  id: string;
  role: string;
  company: string;
  type: 'coding' | 'behavioral' | 'system-design' | 'ml';
  status: 'idle' | 'recording' | 'coding' | 'submitting' | 'completed';
  startTime?: Date;
}

interface InterviewState {
  currentSession: InterviewSession | null;
  messages: ChatMessage[];
  transcript: string[];
  activeQuestion: {
    id: string;
    title: string;
    description: string;
    difficulty: 'easy' | 'medium' | 'hard';
    starterCode?: string;
  } | null;
  code: string;
  language: string;
  consoleOutput: string;
  timerSeconds: number;
  isMuted: boolean;
  isListening: boolean;
  isStreamingResponse: boolean;
  currentStreamText: string;
  
  // Actions
  startSession: (session: Omit<InterviewSession, 'status'>) => void;
  endSession: () => void;
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  updateStreamText: (text: string) => void;
  commitStreamMessage: () => void;
  addTranscriptLine: (text: string) => void;
  setCode: (code: string) => void;
  setLanguage: (lang: string) => void;
  setConsoleOutput: (output: string) => void;
  tickTimer: () => void;
  resetTimer: () => void;
  toggleMute: () => void;
  setListening: (listening: boolean) => void;
}

export const useInterviewStore = create<InterviewState>((set, get) => ({
  currentSession: null,
  messages: [],
  transcript: [],
  activeQuestion: null,
  code: '',
  language: 'typescript',
  consoleOutput: '',
  timerSeconds: 0,
  isMuted: false,
  isListening: false,
  isStreamingResponse: false,
  currentStreamText: '',

  startSession: (session) => {
    const starterCode = session.type === 'coding' 
      ? `function solveQuestion(input) {\n  // Write your solution here\n  return null;\n}`
      : undefined;

    set({
      currentSession: { ...session, status: session.type === 'coding' ? 'coding' : 'recording', startTime: new Date() },
      messages: [
        {
          id: 'welcome',
          sender: 'ai',
          text: `Welcome to your mock interview for the ${session.role} position at ${session.company}. Whenever you are ready, please read the question and let me know if you have any initial thoughts.`,
          timestamp: new Date(),
        }
      ],
      transcript: [],
      activeQuestion: {
        id: 'q1',
        title: session.type === 'coding' ? 'Design a Rate Limiter' : 'Describe a Complex Technical Challenge',
        description: session.type === 'coding'
          ? 'Implement a scalable API rate limiter supporting multiple sliding-window algorithms. Keep memory usage and write performance in mind.'
          : 'Explain a technical hurdle you encountered recently, how you diagnosed the root causes, and how you evaluated potential design alternatives.',
        difficulty: 'hard',
        starterCode,
      },
      code: starterCode || '',
      consoleOutput: 'Console ready. Press "Run Code" to execute tests...',
      timerSeconds: 0,
      isMuted: false,
      isListening: false,
      isStreamingResponse: false,
      currentStreamText: '',
    });
  },

  endSession: () => {
    set((state) => ({
      currentSession: state.currentSession ? { ...state.currentSession, status: 'completed' } : null,
      isListening: false,
    }));
  },

  addMessage: (msg) => {
    const newMsg: ChatMessage = {
      ...msg,
      id: Math.random().toString(36).substr(2, 9),
      timestamp: new Date(),
    };
    set((state) => ({ messages: [...state.messages, newMsg] }));
  },

  updateStreamText: (text) => {
    set({
      isStreamingResponse: true,
      currentStreamText: text,
    });
  },

  commitStreamMessage: () => {
    const { currentStreamText } = get();
    if (!currentStreamText) return;
    
    const newMsg: ChatMessage = {
      id: Math.random().toString(36).substr(2, 9),
      sender: 'ai',
      text: currentStreamText,
      timestamp: new Date(),
    };

    set((state) => ({
      messages: [...state.messages, newMsg],
      isStreamingResponse: false,
      currentStreamText: '',
    }));
  },

  addTranscriptLine: (line) => {
    set((state) => ({ transcript: [...state.transcript, line] }));
  },

  setCode: (code) => set({ code }),
  setLanguage: (language) => set({ language }),
  setConsoleOutput: (consoleOutput) => set({ consoleOutput }),
  tickTimer: () => set((state) => ({ timerSeconds: state.timerSeconds + 1 })),
  resetTimer: () => set({ timerSeconds: 0 }),
  toggleMute: () => set((state) => ({ isMuted: !state.isMuted })),
  setListening: (isListening) => set({ isListening }),
}));
