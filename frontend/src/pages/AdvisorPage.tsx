import React, { useState, useEffect, useRef } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { 
  Sparkles, 
  Send, 
  Bot, 
  User, 
  ShieldCheck, 
  ChevronDown, 
  ChevronUp, 
  Database,
  CheckCircle2,
  RefreshCw,
  Zap,
} from 'lucide-react';
import { api } from '../services/api';


interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  context_used?: any;
  ai_provider?: string;
  action_executed?: any;
}

export const AdvisorPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [expandedContextId, setExpandedContextId] = useState<string | null>(null);
  const [lastFailedMessage, setLastFailedMessage] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const [suggestedChips, setSuggestedChips] = useState<string[]>([
    'What should I study today?',
    'Check my attendance status',
    'How do I improve my CGPA?',
    'When is my next exam?',
  ]);

  const loadHistory = async () => {
    try {
      const history = await api.get<any[]>('/api/advisor/history');
      if (history && history.length > 0) {
        const latest = history[0];
        setConversationId(latest.id);
        const formatted: ChatMessage[] = latest.messages.map((m: any) => ({
          id: m.id,
          role: m.role,
          content: m.content,
        }));
        setMessages(formatted);
      } else {
        // Welcoming companion opener
        setMessages([
          {
            id: 'welcome',
            role: 'assistant',
            content:
              "Heyy! 👋 I'm your AI Academic Advisor and study companion.\n\nI have access to your real attendance, marks, goals, and upcoming exam deadlines. Ask me anything about what to prioritize today, attendance buffers, or planning your study schedule!",
          },
        ]);
      }
    } catch (err) {
      console.error('Failed to load advisor history:', err);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (messageToSend?: string) => {
    const text = (messageToSend || input).trim();
    if (!text || loading) return;

    setLastFailedMessage(null);
    const userMsg: ChatMessage = {
      id: `usr-${Date.now()}`,
      role: 'user',
      content: text,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    const assistantId = `asst-${Date.now()}`;
    const asstMsg: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
    };
    
    setMessages((prev) => [...prev, asstMsg]);

    try {
      const res = await api.postStream('/api/advisor/stream', {
        message: text,
        conversation_id: conversationId,
      });

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error('No readable stream');

      let done = false;
      let fullText = '';
      let buffer = '';

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          // keep the last incomplete line in buffer
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.slice(6);
              if (dataStr === '[DONE]') continue;
              
              try {
                const parsed = JSON.parse(dataStr);
                if (parsed.type === 'text') {
                  fullText += parsed.text;
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantId ? { ...m, content: fullText } : m
                    )
                  );
                } else if (parsed.type === 'metadata') {
                  const meta = parsed.data;
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantId
                        ? {
                            ...m,
                            context_used: meta.context_used,
                            ai_provider: meta.ai_provider,
                            action_executed: meta.action_executed,
                          }
                        : m
                    )
                  );
                  if (meta.suggested_followups) {
                    setSuggestedChips(meta.suggested_followups);
                  }
                }
              } catch (e) {
                console.error('Failed to parse SSE chunk', e);
              }
            }
          }
        }
      }
      
      // If we are at the first message and no conversationId yet, 
      // we don't have a direct way to get it from the stream metadata unless we add it.
      // But the backend will group by student_id automatically if we just re-fetch history later,
      // or we can just leave conversationId as null and let the backend keep creating it until page reload.
      // Actually, let's just fetch history again in the background if conversationId is null to get the ID.
      if (!conversationId) {
        loadHistory();
      }

    } catch (err: any) {
      console.error('Chat error:', err);
      setLastFailedMessage(text);
      setMessages((prev) => [
        ...prev.filter(m => m.id !== assistantId), // remove the empty assistant message
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: "I ran into a temporary connection issue. Your academic records are completely safe. Please click retry below or ask again!",
        },
      ]);
    } finally {
      setLoading(false);
      setTimeout(() => textareaRef.current?.focus(), 50);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="space-y-5 max-w-4xl mx-auto pb-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white flex items-center justify-center shadow-sm">
              <Sparkles className="w-4 h-4" />
            </div>
            <span>AI Academic Companion</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Personalized academic guidance grounded in your verified attendance and course data.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-full border border-emerald-200/80 shadow-2xs">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Grounded in Verified Records</span>
          </div>
        </div>
      </div>

      {/* Suggested Follow-up Prompt Chips */}
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1 mr-1">
          <Zap className="w-3 h-3 text-amber-500" />
          <span>Suggestions:</span>
        </span>
        {suggestedChips.map((chip, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(chip)}
            disabled={loading}
            className="text-xs bg-white hover:bg-indigo-50 hover:text-indigo-700 hover:border-indigo-200 text-slate-700 px-3 py-1 rounded-full border border-slate-200/90 transition-all shadow-2xs disabled:opacity-50 active:scale-95"
          >
            {chip}
          </button>
        ))}
      </div>

      {/* Chat Transcript Box */}
      <Card className="min-h-[500px] flex flex-col justify-between p-0 overflow-hidden shadow-sm border border-slate-200/80 bg-slate-50/30">
        <div className="p-4 md:p-6 space-y-4 max-h-[540px] overflow-y-auto">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex gap-3 ${
                m.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {m.role === 'assistant' && (
                <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-700 text-white flex items-center justify-center shrink-0 shadow-xs mt-0.5">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div className="space-y-1.5 max-w-2xl">
                {/* Action Executed Badge */}
                {m.action_executed && m.action_executed.success && (
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-[11px] font-semibold shadow-2xs">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    <span>{m.action_executed.confirmation || 'Database updated successfully'}</span>
                  </div>
                )}

                {/* Message Bubble */}
                <div
                  className={`rounded-2xl p-4 text-sm leading-relaxed ${
                    m.role === 'user'
                      ? 'bg-indigo-600 text-white font-medium shadow-xs rounded-tr-xs'
                      : 'bg-white text-slate-800 border border-slate-200/80 shadow-2xs rounded-tl-xs'
                  }`}
                >
                  <div className="whitespace-pre-wrap">{m.content}</div>
                </div>

                {/* Grounding Context Snapshot Dropdown */}
                {m.context_used && Object.keys(m.context_used).length > 0 && (
                  <div className="pl-1">
                    <button
                      onClick={() =>
                        setExpandedContextId(
                          expandedContextId === m.id ? null : m.id
                        )
                      }
                      className="inline-flex items-center gap-1.5 text-[11px] text-slate-400 hover:text-indigo-600 transition-colors"
                    >
                      <Database className="w-3 h-3" />
                      <span>
                        {expandedContextId === m.id
                          ? 'Hide Verified Database Context'
                          : 'View Verified Database Facts'}
                      </span>
                      {expandedContextId === m.id ? (
                        <ChevronUp className="w-3 h-3" />
                      ) : (
                        <ChevronDown className="w-3 h-3" />
                      )}
                    </button>

                    {expandedContextId === m.id && (
                      <div className="mt-2 p-3 bg-slate-900 text-emerald-400 font-mono text-[11px] rounded-xl overflow-x-auto max-h-48 border border-slate-800 shadow-inner">
                        <pre>{JSON.stringify(m.context_used, null, 2)}</pre>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {m.role === 'user' && (
                <div className="w-8 h-8 rounded-xl bg-slate-800 text-white flex items-center justify-center shrink-0 shadow-xs mt-0.5">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}

          {/* Typing Animation */}
          {loading && (
            <div className="flex gap-3 items-center">
              <div className="w-8 h-8 rounded-xl bg-indigo-600 text-white flex items-center justify-center shrink-0 shadow-xs animate-pulse">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-white border border-slate-200/80 rounded-2xl rounded-tl-xs px-4 py-3 shadow-2xs flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-indigo-600 animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full bg-indigo-600 animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full bg-indigo-600 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}

          {/* Retry Button if last failed */}
          {lastFailedMessage && !loading && (
            <div className="flex justify-center pt-2">
              <button
                onClick={() => handleSend(lastFailedMessage)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-rose-50 text-rose-700 hover:bg-rose-100 rounded-xl text-xs font-semibold border border-rose-200 transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Retry Message</span>
              </button>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-3.5 bg-white border-t border-slate-100 flex items-center gap-2">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            disabled={loading}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Talk to your advisor... (Press Enter to send, Shift+Enter for new line)"
            className="flex-1 text-sm bg-slate-50 border border-slate-200/90 rounded-xl px-4 py-2.5 outline-none focus:border-indigo-600 focus:bg-white transition-all disabled:opacity-50 resize-none max-h-32 min-h-[42px]"
          />
          <Button
            onClick={() => handleSend()}
            isLoading={loading}
            disabled={loading || !input.trim()}
            rightIcon={<Send className="w-4 h-4" />}
          >
            Send
          </Button>
        </div>
      </Card>
    </div>
  );
};
