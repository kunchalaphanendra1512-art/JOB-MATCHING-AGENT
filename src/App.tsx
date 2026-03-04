import React, { useState, useEffect, useRef } from 'react';
import {
  Briefcase,
  User,
  ShieldCheck,
  BarChart3,
  Upload,
  Search,
  CheckCircle2,
  AlertTriangle,
  FileText,
  MapPin,
  DollarSign,
  Clock,
  ChevronRight,
  BrainCircuit,
  Plus,
  Info,
  ArrowRight,
  Target,
  Zap,
  ShieldAlert,
  X,
  FileSearch,
  Trophy
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import ReactMarkdown from 'react-markdown';
import { processResumePDF, generateAnalysis, getEmbedding } from './services/gemini';

// --- Utility ---
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// --- Types ---
type View = 'candidate' | 'recruiter' | 'analytics' | 'login';

interface Resume {
  id: string;
  email: string;
  skills: string[];
  experience_years: number;
  location: string;
  salary_expectation: number;
  summary: string;
  trust_score: number;
  fraud_flags: string[];
  risk_level: 'Low' | 'Medium' | 'High';
}

interface Job {
  id: string;
  title: string;
  description: string;
  required_skills: string[];
  required_experience: number;
  location: string;
  salary_range_min: number;
  salary_range_max: number;
}

interface Match {
  id: string;
  resume_id: string;
  job_id: string;
  skill_score: number;
  experience_score: number;
  location_score: number;
  final_match_score: number;
  matched_skills: string[];
  skill_gaps: string[];
  trust_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  match_grade: string;
  explanation: string;
  mismatch_pct: number;
  email?: string;
  resume?: Resume;
}

// --- Components ---

const Card = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div className={cn("bg-white border border-zinc-200 rounded-2xl overflow-hidden shadow-sm", className)}>
    {children}
  </div>
);

const Badge = ({ children, variant = 'default' }: { children: React.ReactNode; variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'danger' }) => {
  const variants = {
    default: "bg-zinc-100 text-zinc-600 border-zinc-200",
    success: "bg-emerald-50 text-emerald-700 border-emerald-100",
    warning: "bg-amber-50 text-amber-700 border-amber-100",
    error: "bg-rose-50 text-rose-700 border-rose-100",
    info: "bg-indigo-50 text-indigo-700 border-indigo-100",
    danger: "bg-red-50 text-red-700 border-red-100"
  };
  return (
    <span className={cn("px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border", variants[variant])}>
      {children}
    </span>
  );
};

const ProgressBar = ({ value, color = 'zinc' }: { value: number, color?: 'zinc' | 'emerald' | 'rose' | 'indigo' }) => {
  const colors = {
    zinc: "bg-zinc-900",
    emerald: "bg-emerald-500",
    rose: "bg-rose-500",
    indigo: "bg-indigo-500"
  };
  return (
    <div className="w-full bg-zinc-100 h-2 rounded-full overflow-hidden">
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${value}%` }}
        className={cn("h-full transition-all duration-1000", colors[color])}
      />
    </div>
  );
};

// Error boundary to catch render-time exceptions and show a useful message
class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean, error?: any }> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError(error: any) {
    return { hasError: true, error };
  }
  componentDidCatch(error: any, info: any) {
    // eslint-disable-next-line no-console
    console.error('Unhandled error in UI:', error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-8">
          <div className="max-w-2xl w-full text-center">
            <h2 className="text-2xl font-bold mb-4">Something went wrong</h2>
            <pre className="text-xs p-4 bg-red-50 rounded-md overflow-auto text-left">{String(this.state.error)}</pre>
            <p className="mt-4 text-sm text-zinc-600">Open the developer console for details.</p>
          </div>
        </div>
      );
    }
    return this.props.children as any;
  }
}

const API_BASE_URL = import.meta.env.VITE_API_URL ?? '';

export default function App() {
  const [view, setView] = useState<View>('login');
  const [user, setUser] = useState<{ email: string, role: 'candidate' | 'recruiter' } | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [jobSearch, setJobSearch] = useState<string>('');
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [jobPosting, setJobPosting] = useState(false);
  const [postSuccess, setPostSuccess] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<Match | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // --- Data Fetching ---
  const fetchData = async () => {
    try {
      // Build jobs URL with optional filters: owner for recruiters, search for candidates
      let jobsUrl = `${API_BASE_URL}/api/jobs`;
      const params: string[] = [];
      if (user?.role === 'recruiter' && user.email) {
        params.push(`owner=${encodeURIComponent(user.email)}`);
      }
      if (view === 'candidate' && jobSearch) {
        params.push(`search=${encodeURIComponent(jobSearch)}`);
      }
      if (params.length) jobsUrl += `?${params.join('&')}`;

      const [jobsRes, statsRes] = await Promise.all([
        fetch(jobsUrl).then(r => r.json()),
        fetch(`${API_BASE_URL}/api/analytics`).then(r => r.json())
      ]);
      setJobs(jobsRes);
      setStats(statsRes);
      if (jobsRes.length > 0 && !selectedJob) setSelectedJob(jobsRes[0]);
    } catch (err) {
      console.error("Failed to fetch data", err);
    }
  };

  useEffect(() => {
    if (view !== 'login') fetchData();
  }, [view]);

  // Refresh jobs when candidate changes search term
  useEffect(() => {
    if (view === 'candidate') {
      fetchData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobSearch]);

  useEffect(() => {
    if (selectedJob) {
      fetch(`${API_BASE_URL}/api/ranked/${selectedJob.id}`)
        .then(r => r.json())
        .then(data => {
          if (Array.isArray(data)) {
            setMatches(data);
          } else {
            console.warn('ranked endpoint returned non-array', data);
            setMatches([]);
          }
        });
    }
  }, [selectedJob]);

  // --- Handlers ---
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('location', 'Remote'); // Default or could be from a form
      formData.append('salary_expectation', '100000'); // Default or from form

      const response = await fetch(`${API_BASE_URL}/api/upload-resume`, {
        method: 'POST',
        body: formData
      });

      const result = await response.json();
      if (!response.ok) {
        // Use server-provided message if available
        throw new Error(result.detail || "Upload failed");
      }

      // Use real job or demo job for analysis
      const jobForAnalysis = jobs.length > 0 ? jobs[0] : {
        title: 'Senior Software Engineer',
        description: 'Looking for experienced developers with strong technical background.',
        required_skills: ['JavaScript', 'React', 'Node.js', 'Python', 'SQL']
      };

      const analysisData = await generateAnalysis(result.resume, jobForAnalysis);
      setAnalysis({ ...analysisData, resume: result.resume });

      await fetchData();
    } catch (err) {
      console.error(err);
      alert("Error processing resume with Python ML Engine");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateJob = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setJobPosting(true);
    try {
      const formData = new FormData(e.currentTarget);
      const jobData = {
        title: formData.get('title') as string,
        description: formData.get('description') as string,
        required_skills: (formData.get('skills') as string).split(',').map(s => s.trim()),
        required_experience: parseInt(formData.get('experience') as string),
        location: formData.get('location') as string,
        salary_min: parseInt(formData.get('salary_min') as string),
        salary_max: parseInt(formData.get('salary_max') as string),
        poster_email: user?.email || 'demo@hiresense.ai'
      };

      const response = await fetch(`${API_BASE_URL}/api/post-job`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(jobData)
      });

      if (response.ok) {
        setPostSuccess(true);
        (e.target as HTMLFormElement).reset();
        await fetchData();
        // Auto-hide success message after 3 seconds
        setTimeout(() => setPostSuccess(false), 3000);
      }
    } catch (err) {
      console.error("Failed to post job", err);
    } finally {
      setJobPosting(false);
    }
  };

  const handleLogin = (role: 'candidate' | 'recruiter') => {
    setUser({ email: 'demo@hiresense.ai', role });
    setView(role === 'recruiter' ? 'recruiter' : 'candidate');
  };

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-[#FAFAFA] text-zinc-900 font-sans selection:bg-zinc-900 selection:text-white">
        {/* Sidebar */}
        {view !== 'login' && (
          <nav className="fixed left-0 top-0 bottom-0 w-72 bg-white border-r border-zinc-200 p-8 flex flex-col gap-10 z-50">
            <div className="flex items-center gap-4 px-2">
              <div className="w-12 h-12 bg-zinc-900 rounded-2xl flex items-center justify-center shadow-lg shadow-zinc-200">
                <BrainCircuit className="text-white w-7 h-7" />
              </div>
              <div>
                <h1 className="font-black text-xl tracking-tighter leading-none">HireSense AI</h1>
                <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">v2.0 Engine</span>
              </div>
            </div>

            <div className="flex flex-col gap-2">
              {user?.role === 'recruiter' && (
                <>
                  <button
                    onClick={() => setView('recruiter')}
                    className={cn("flex items-center gap-4 px-5 py-4 rounded-2xl transition-all group", view === 'recruiter' ? "bg-zinc-900 text-white shadow-xl shadow-zinc-200" : "hover:bg-zinc-100 text-zinc-500")}
                  >
                    <Briefcase size={22} className={cn(view === 'recruiter' ? "text-white" : "group-hover:text-zinc-900")} />
                    <span className="font-bold">Dashboard</span>
                  </button>
                  <button
                    onClick={() => setView('analytics')}
                    className={cn("flex items-center gap-4 px-5 py-4 rounded-2xl transition-all group", view === 'analytics' ? "bg-zinc-900 text-white shadow-xl shadow-zinc-200" : "hover:bg-zinc-100 text-zinc-500")}
                  >
                    <BarChart3 size={22} className={cn(view === 'analytics' ? "text-white" : "group-hover:text-zinc-900")} />
                    <span className="font-bold">Analytics</span>
                  </button>
                </>
              )}
              {user?.role === 'candidate' && (
                <button
                  onClick={() => setView('candidate')}
                  className={cn("flex items-center gap-4 px-5 py-4 rounded-2xl transition-all group", view === 'candidate' ? "bg-zinc-900 text-white shadow-xl shadow-zinc-200" : "hover:bg-zinc-100 text-zinc-500")}
                >
                  <User size={22} className={cn(view === 'candidate' ? "text-white" : "group-hover:text-zinc-900")} />
                  <span className="font-bold">My Profile</span>
                </button>
              )}
            </div>

            <div className="mt-auto p-6 bg-zinc-50 rounded-3xl border border-zinc-100 relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
                <ShieldCheck size={64} />
              </div>
              <div className="relative z-10">
                <div className="flex items-center gap-2 mb-3">
                  <ShieldCheck className="text-emerald-600" size={18} />
                  <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">Trust Protocol</span>
                </div>
                <p className="text-[11px] text-zinc-500 leading-relaxed font-medium">
                  Our multi-layer verification engine is actively monitoring for profile inconsistencies.
                </p>
              </div>
            </div>

            <button
              onClick={() => setView('login')}
              className="flex items-center gap-4 px-5 py-4 rounded-2xl text-rose-600 hover:bg-rose-50 transition-all font-bold text-sm"
            >
              <Zap size={20} className="rotate-180" />
              Sign Out
            </button>
          </nav>
        )}

        {/* Main Content */}
        <main className={cn("transition-all duration-500", view === 'login' ? "ml-0" : "ml-72 p-12")}>
          <AnimatePresence mode="wait">
            {view === 'login' && (
              <motion.div
                key="login"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="min-h-screen flex items-center justify-center p-8 bg-zinc-900 relative overflow-hidden"
              >
                <div className="absolute inset-0 overflow-hidden opacity-30 pointer-events-none">
                  <div className="absolute top-[-20%] left-[-20%] w-[60%] h-[60%] bg-indigo-600 rounded-full blur-[160px] animate-pulse" />
                  <div className="absolute bottom-[-20%] right-[-20%] w-[60%] h-[60%] bg-emerald-600 rounded-full blur-[160px] animate-pulse" style={{ animationDelay: '1s' }} />
                </div>

                <div className="max-w-4xl w-full grid grid-cols-1 lg:grid-cols-2 gap-12 items-center relative z-10">
                  <div className="text-white space-y-8">
                    <div className="flex items-center gap-4">
                      <div className="w-16 h-16 bg-white rounded-3xl flex items-center justify-center shadow-2xl">
                        <BrainCircuit className="text-zinc-900 w-10 h-10" />
                      </div>
                      <h1 className="text-4xl font-black tracking-tighter">HireSense AI</h1>
                    </div>
                    <h2 className="text-6xl font-black leading-[0.9] tracking-tighter">
                      THE FUTURE OF <span className="text-zinc-500">TALENT</span> VALIDATION.
                    </h2>
                    <p className="text-zinc-400 text-xl font-medium leading-relaxed">
                      Intelligent matching, fraud detection, and deep candidate analysis powered by next-gen AI.
                    </p>
                    <div className="flex gap-4 pt-4">
                      <div className="flex -space-x-4">
                        {[1, 2, 3, 4].map(i => (
                          <div key={i} className="w-12 h-12 rounded-full border-4 border-zinc-900 bg-zinc-800 flex items-center justify-center">
                            <User size={20} className="text-zinc-500" />
                          </div>
                        ))}
                      </div>
                      <div className="text-sm">
                        <p className="font-bold text-white">500+ Companies</p>
                        <p className="text-zinc-500">Trust our validation engine</p>
                      </div>
                    </div>
                  </div>

                  <Card className="p-10 bg-white/5 backdrop-blur-3xl border-white/10 shadow-2xl">
                    <h3 className="text-2xl font-black text-white mb-8 tracking-tight">Get Started</h3>
                    <div className="flex flex-col gap-4">
                      <button
                        onClick={() => handleLogin('recruiter')}
                        className="group relative flex items-center justify-between bg-white text-zinc-900 p-6 rounded-3xl font-black text-lg hover:bg-zinc-100 transition-all active:scale-[0.98]"
                      >
                        <span>Recruiter Portal</span>
                        <div className="w-10 h-10 bg-zinc-900 rounded-xl flex items-center justify-center text-white group-hover:translate-x-1 transition-transform">
                          <ArrowRight size={20} />
                        </div>
                      </button>
                      <button
                        onClick={() => handleLogin('candidate')}
                        className="group relative flex items-center justify-between bg-zinc-800 text-white p-6 rounded-3xl font-black text-lg hover:bg-zinc-700 transition-all active:scale-[0.98] border border-white/10"
                      >
                        <span>Candidate View</span>
                        <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center text-zinc-900 group-hover:translate-x-1 transition-transform">
                          <ArrowRight size={20} />
                        </div>
                      </button>
                    </div>
                    <p className="text-center text-zinc-500 text-xs mt-8 font-medium">
                      By continuing, you agree to our Terms of Service and Privacy Policy.
                    </p>
                  </Card>
                </div>
              </motion.div>
            )}

            {view === 'candidate' && (
              <motion.div
                key="candidate"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="max-w-5xl mx-auto space-y-12"
              >
                <header className="flex justify-between items-end">
                  <div className="space-y-2">
                    <Badge variant="info">Candidate Portal</Badge>
                    <h2 className="text-5xl font-black tracking-tighter">Your AI Profile.</h2>
                    <p className="text-zinc-500 text-lg font-medium">Upload your resume to see how you rank against top opportunities.</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <input
                        type="search"
                        placeholder="Search jobs..."
                        value={jobSearch}
                        onChange={(e) => setJobSearch(e.target.value)}
                        className="w-72 p-3 rounded-2xl border border-zinc-200 text-sm outline-none"
                      />
                      <Search className="absolute right-3 top-3 text-zinc-400" />
                    </div>
                  </div>
                </header>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                  <div className="lg:col-span-1 space-y-8">
                    <Card className="p-8 bg-zinc-900 text-white border-none shadow-2xl shadow-zinc-200">
                      <div className="space-y-6">
                        <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center text-zinc-900">
                          <Upload size={28} />
                        </div>
                        <div>
                          <h3 className="text-2xl font-black tracking-tight mb-2">Upload Resume</h3>
                          <p className="text-zinc-400 text-sm font-medium">PDF format only. Our AI will extract and analyze your data instantly.</p>
                        </div>

                        <input
                          type="file"
                          ref={fileInputRef}
                          onChange={handleFileUpload}
                          accept=".pdf"
                          className="hidden"
                        />

                        <button
                          onClick={() => fileInputRef.current?.click()}
                          disabled={loading}
                          className="w-full bg-white text-zinc-900 py-4 rounded-2xl font-black text-sm hover:bg-zinc-100 transition-all flex items-center justify-center gap-3 disabled:opacity-50"
                        >
                          {loading ? (
                            <div className="w-5 h-5 border-2 border-zinc-900 border-t-transparent rounded-full animate-spin" />
                          ) : (
                            <FileText size={18} />
                          )}
                          {loading ? 'Analyzing...' : 'Select PDF File'}
                        </button>
                      </div>
                    </Card>

                    <div className="p-6 bg-indigo-50 rounded-3xl border border-indigo-100">
                      <div className="flex items-center gap-3 mb-4">
                        <Zap className="text-indigo-600" size={20} />
                        <span className="text-xs font-black uppercase tracking-widest text-indigo-400">Pro Tip</span>
                      </div>
                      <p className="text-xs text-indigo-700 font-medium leading-relaxed">
                        Ensure your PDF is text-searchable for the best extraction accuracy. Scanned images may take longer to process.
                      </p>
                    </div>
                  </div>

                  <div className="lg:col-span-2">
                    <AnimatePresence mode="wait">
                      {analysis ? (
                        <motion.div
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          className="space-y-8"
                        >
                          <Card className="p-10">
                            <div className="flex justify-between items-start mb-10">
                              <div className="space-y-2">
                                <h3 className="text-3xl font-black tracking-tight">Analysis Result</h3>
                                <p className="text-zinc-500 font-medium">Matched against: <span className="text-zinc-900 font-bold">{jobs[0]?.title}</span></p>
                              </div>
                              <div className="text-right">
                                <div className="text-[10px] font-black text-zinc-400 uppercase tracking-widest mb-2">Match Score</div>
                                <div className="text-5xl font-black text-zinc-900">{Math.round(analysis.resume.trust_score)}%</div>
                              </div>
                            </div>

                            <div className="grid grid-cols-3 gap-10 mb-10 pb-10 border-b border-zinc-100">
                              <div className="space-y-4">
                                <div className="flex justify-between text-xs font-bold uppercase tracking-widest text-zinc-400">
                                  <span>Trust Level</span>
                                  <span className={cn(
                                    analysis.resume.trust_score > 80 ? "text-emerald-600" : "text-amber-600"
                                  )}>{analysis.resume.risk_level} Risk</span>
                                </div>
                                <ProgressBar value={analysis.resume.trust_score} color={analysis.resume.trust_score > 80 ? 'emerald' : 'rose'} />
                              </div>
                              <div className="space-y-4">
                                <div className="flex justify-between text-xs font-bold uppercase tracking-widest text-zinc-400">
                                  <span>Skill Match</span>
                                  <span className="text-emerald-600">{analysis.match_percentage || 85}%</span>
                                </div>
                                <ProgressBar value={analysis.match_percentage || 85} color="emerald" />
                              </div>
                              <div className="space-y-4">
                                <div className="flex justify-between text-xs font-bold uppercase tracking-widest text-zinc-400">
                                  <span>Mismatch</span>
                                  <span className="text-rose-600">{analysis.mismatch_percentage || 15}%</span>
                                </div>
                                <ProgressBar value={analysis.mismatch_percentage || 15} color="rose" />
                              </div>
                            </div>

                            <div className="space-y-6">
                              <div>
                                <h4 className="text-xs font-black text-zinc-400 uppercase tracking-widest mb-4">Extracted Skills</h4>
                                <div className="flex flex-wrap gap-2">
                                  {analysis.resume.skills.map((skill: string) => (
                                    <Badge key={skill} variant="info">{skill}</Badge>
                                  ))}
                                </div>
                              </div>

                              {analysis.skill_gap && analysis.skill_gap.length > 0 && (
                                <div>
                                  <h4 className="text-xs font-black text-zinc-400 uppercase tracking-widest mb-4">Skill Gaps ({analysis.skill_gap.length})</h4>
                                  <div className="flex flex-wrap gap-2">
                                    {analysis.skill_gap.map((skill: string) => (
                                      <Badge key={skill} variant="danger">{skill}</Badge>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {analysis.improvements && analysis.improvements.length > 0 && (
                                <div>
                                  <h4 className="text-xs font-black text-zinc-400 uppercase tracking-widest mb-4">📈 Improvement Areas</h4>
                                  <div className="space-y-3">
                                    {analysis.improvements.map((imp: string, i: number) => (
                                      <div key={i} className="flex gap-4 p-4 bg-amber-50 rounded-2xl border border-amber-100">
                                        <div className="text-amber-600 font-black text-lg min-w-fit">→</div>
                                        <p className="text-sm text-amber-800 font-medium">{imp}</p>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              <div>
                                <h4 className="text-xs font-black text-zinc-400 uppercase tracking-widest mb-4">AI Explanation</h4>
                                <p className="text-zinc-600 leading-relaxed font-medium bg-zinc-50 p-6 rounded-2xl border border-zinc-100">
                                  {analysis.explanation}
                                </p>
                              </div>
                            </div>
                          </Card>

                          <Card className="p-10 bg-indigo-900 text-white border-none">
                            <div className="flex items-center gap-4 mb-8">
                              <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center">
                                <BrainCircuit className="text-white" size={24} />
                              </div>
                              <h3 className="text-2xl font-black tracking-tight">AI Interview Prep</h3>
                            </div>
                            <div className="space-y-4">
                              {analysis.interview_questions.map((q: string, i: number) => (
                                <div key={i} className="flex gap-4 p-5 bg-white/5 rounded-2xl border border-white/10 hover:bg-white/10 transition-colors">
                                  <span className="text-indigo-400 font-black">0{i + 1}</span>
                                  <p className="font-medium text-sm leading-relaxed">{q}</p>
                                </div>
                              ))}
                            </div>
                          </Card>
                        </motion.div>
                      ) : (
                        <div className="h-full flex flex-col items-center justify-center p-20 border-2 border-dashed border-zinc-200 rounded-[40px] text-zinc-400">
                          <FileSearch size={64} className="mb-6 opacity-20" />
                          <h3 className="text-xl font-bold mb-2">No Analysis Yet</h3>
                          <p className="text-sm font-medium">Upload your resume to trigger the AI matching engine.</p>
                        </div>
                      )}
                    </AnimatePresence>
                  </div>
                </div>
              </motion.div>
            )}

            {view === 'recruiter' && (
              <motion.div
                key="recruiter"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-10"
              >
                <header className="flex justify-between items-end">
                  <div className="space-y-2">
                    <Badge variant="success">Recruiter Dashboard</Badge>
                    <h2 className="text-5xl font-black tracking-tighter">Talent Pipeline.</h2>
                    <p className="text-zinc-500 text-lg font-medium">Monitor verified candidates and manage your job postings.</p>
                  </div>
                  <div className="flex gap-4">
                    <div className="bg-white border border-zinc-200 rounded-2xl px-6 py-4 flex items-center gap-3 shadow-sm">
                      <Search size={18} className="text-zinc-400" />
                      <input type="text" placeholder="Search pipeline..." className="bg-transparent outline-none text-sm font-bold w-64" />
                    </div>
                  </div>
                </header>

                <div className="grid grid-cols-12 gap-10">
                  {/* Job List */}
                  <div className="col-span-4 space-y-6">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-black text-zinc-400 uppercase tracking-widest">Active Postings</h3>
                      <button className="p-2 hover:bg-zinc-200 rounded-xl transition-colors">
                        <Plus size={20} />
                      </button>
                    </div>

                    <div className="space-y-4">
                      {jobs.map(job => (
                        <button
                          key={job.id}
                          onClick={() => setSelectedJob(job)}
                          className={cn(
                            "w-full text-left p-6 rounded-3xl border transition-all relative overflow-hidden group",
                            selectedJob?.id === job.id
                              ? "bg-white border-zinc-900 shadow-xl shadow-zinc-200 ring-1 ring-zinc-900"
                              : "bg-white border-zinc-200 hover:border-zinc-400"
                          )}
                        >
                          <div className="flex justify-between items-start mb-4">
                            <h4 className="font-black text-xl group-hover:text-zinc-900">{job.title}</h4>
                            <ChevronRight size={18} className={cn("transition-transform", selectedJob?.id === job.id ? "rotate-90" : "")} />
                          </div>
                          <div className="flex flex-wrap gap-2">
                            <Badge>{job.location}</Badge>
                            <Badge variant="info">{job.required_experience}y Exp</Badge>
                          </div>
                        </button>
                      ))}

                      <Card className={cn("p-8 border-2", postSuccess ? "bg-emerald-50 border-emerald-200" : "bg-zinc-50 border-dashed")}>
                        <form onSubmit={handleCreateJob} className="space-y-6">
                          <div className="flex justify-between items-center">
                            <h4 className="text-xl font-black tracking-tight">Post New Role</h4>
                            {postSuccess && (
                              <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} className="flex items-center gap-2 text-emerald-700 font-bold text-sm">
                                <CheckCircle2 size={20} />
                                Posted!
                              </motion.div>
                            )}
                          </div>
                          <div className="space-y-4">
                            <input name="title" placeholder="Job Title" className="w-full p-4 border rounded-2xl text-sm font-bold outline-none focus:ring-2 ring-zinc-900 transition-all disabled:opacity-50" required disabled={jobPosting} />
                            <textarea name="description" placeholder="Description" className="w-full p-4 border rounded-2xl text-sm font-medium h-32 outline-none focus:ring-2 ring-zinc-900 transition-all disabled:opacity-50" required disabled={jobPosting} />
                            <input name="skills" placeholder="Skills (comma separated)" className="w-full p-4 border rounded-2xl text-sm font-bold outline-none focus:ring-2 ring-zinc-900 transition-all disabled:opacity-50" required disabled={jobPosting} />
                            <div className="grid grid-cols-2 gap-4">
                              <input name="experience" type="number" placeholder="Exp Years" className="p-4 border rounded-2xl text-sm font-bold outline-none focus:ring-2 ring-zinc-900 transition-all disabled:opacity-50" required disabled={jobPosting} />
                              <input name="location" placeholder="Location" className="p-4 border rounded-2xl text-sm font-bold outline-none focus:ring-2 ring-zinc-900 transition-all disabled:opacity-50" required disabled={jobPosting} />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                              <input name="salary_min" type="number" placeholder="Min Salary" className="p-4 border rounded-2xl text-sm font-bold outline-none focus:ring-2 ring-zinc-900 transition-all disabled:opacity-50" required disabled={jobPosting} />
                              <input name="salary_max" type="number" placeholder="Max Salary" className="p-4 border rounded-2xl text-sm font-bold outline-none focus:ring-2 ring-zinc-900 transition-all disabled:opacity-50" required disabled={jobPosting} />
                            </div>
                          </div>
                          <button type="submit" disabled={jobPosting} className="w-full bg-zinc-900 text-white py-4 rounded-2xl font-black text-sm hover:bg-zinc-800 transition-all shadow-lg shadow-zinc-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3">
                            {jobPosting ? (
                              <>
                                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                Publishing...
                              </>
                            ) : (
                              <>
                                <Plus size={18} />
                                Publish Posting
                              </>
                            )}
                          </button>
                        </form>
                      </Card>
                    </div>
                  </div>

                  {/* Candidate Table */}
                  <div className="col-span-8 space-y-6">
                    {selectedJob ? (
                      <>
                        <div className="flex items-center justify-between">
                          <h3 className="text-xs font-black text-zinc-400 uppercase tracking-widest">
                            Ranked Candidates for <span className="text-zinc-900">{selectedJob.title}</span>
                          </h3>
                          <div className="flex items-center gap-3 text-xs font-bold text-zinc-500">
                            <Zap size={14} className="text-amber-500" />
                            AI Match Ranking Active
                          </div>
                        </div>

                        <Card className="overflow-hidden border-none shadow-2xl shadow-zinc-100">
                          <table className="w-full text-left border-collapse">
                            <thead>
                              <tr className="bg-zinc-50 border-b border-zinc-100">
                                <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-zinc-400">Rank</th>
                                <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-zinc-400">Candidate</th>
                                <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-zinc-400 text-center">Match %</th>
                                <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-zinc-400 text-center">Trust</th>
                                <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-zinc-400 text-center">Risk</th>
                                <th className="px-8 py-5 text-[10px] font-black uppercase tracking-widest text-zinc-400 text-right">Action</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-zinc-50">
                              {matches.map((match, idx) => (
                                <tr key={match.id} className="hover:bg-zinc-50/50 transition-colors group">
                                  <td className="px-8 py-6">
                                    <div className="w-8 h-8 rounded-lg bg-zinc-100 flex items-center justify-center font-black text-xs text-zinc-500">
                                      {idx + 1}
                                    </div>
                                  </td>
                                  <td className="px-8 py-6">
                                    <div className="flex items-center gap-4">
                                      <div className="w-10 h-10 rounded-full bg-zinc-900 flex items-center justify-center text-white font-black text-xs">
                                        {match.resume?.email?.[0].toUpperCase() || 'C'}
                                      </div>
                                      <div>
                                        <p className="font-black text-sm">{match.resume?.email || 'Candidate'}</p>
                                        <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">{match.resume?.location}</p>
                                      </div>
                                    </div>
                                  </td>
                                  <td className="px-8 py-6 text-center">
                                    <span className="text-lg font-black text-zinc-900">{Math.round(match.final_match_score)}%</span>
                                  </td>
                                  <td className="px-8 py-6 text-center">
                                    <span className={cn(
                                      "font-bold",
                                      match.trust_score > 80 ? "text-emerald-600" : "text-amber-600"
                                    )}>{Math.round(match.trust_score)}%</span>
                                  </td>
                                  <td className="px-8 py-6 text-center">
                                    <Badge variant={match.risk_level === 'LOW' ? 'success' : match.risk_level === 'MEDIUM' ? 'warning' : 'danger'}>
                                      {match.risk_level}
                                    </Badge>
                                  </td>
                                  <td className="px-8 py-6 text-right">
                                    <button
                                      onClick={() => setSelectedCandidate(match)}
                                      className="p-3 hover:bg-zinc-900 hover:text-white rounded-xl transition-all text-zinc-400"
                                    >
                                      <ArrowRight size={20} />
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          {matches.length === 0 && (
                            <div className="p-20 text-center text-zinc-400">
                              <Search size={48} className="mx-auto mb-4 opacity-10" />
                              <p className="font-bold">No candidates matched for this role yet.</p>
                            </div>
                          )}
                        </Card>
                      </>
                    ) : (
                      <div className="h-full flex flex-col items-center justify-center p-20 border-2 border-dashed border-zinc-200 rounded-[40px] text-zinc-400">
                        <Briefcase size={64} className="mb-6 opacity-20" />
                        <h3 className="text-xl font-bold mb-2">Select a Posting</h3>
                        <p className="text-sm font-medium">Choose a job from the left to view ranked candidates.</p>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            )}

            {view === 'analytics' && (
              <motion.div
                key="analytics"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                className="space-y-12"
              >
                <header className="space-y-2">
                  <Badge variant="info">System Analytics</Badge>
                  <h2 className="text-5xl font-black tracking-tighter">Algorithm Performance.</h2>
                  <p className="text-zinc-500 text-lg font-medium">Real-time metrics on matching accuracy and trust protocols.</p>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                  <Card className="p-8 border-none shadow-xl shadow-zinc-100">
                    <div className="flex justify-between items-start mb-6">
                      <div className="w-12 h-12 bg-zinc-900 rounded-2xl flex items-center justify-center text-white">
                        <Target size={24} />
                      </div>
                      <Badge variant="success">+12%</Badge>
                    </div>
                    <h4 className="text-[10px] font-black text-zinc-400 uppercase tracking-widest mb-2">Avg Match Score</h4>
                    <div className="text-5xl font-black tracking-tighter">{Math.round(stats?.avg_match_score || 0)}%</div>
                  </Card>

                  <Card className="p-8 border-none shadow-xl shadow-zinc-100">
                    <div className="flex justify-between items-start mb-6">
                      <div className="w-12 h-12 bg-rose-500 rounded-2xl flex items-center justify-center text-white">
                        <ShieldAlert size={24} />
                      </div>
                      <Badge variant="danger">High</Badge>
                    </div>
                    <h4 className="text-[10px] font-black text-zinc-400 uppercase tracking-widest mb-2">Fraud Percentage</h4>
                    <div className="text-5xl font-black tracking-tighter">{Math.round(stats?.fraud_percentage || 0)}%</div>
                  </Card>

                  <Card className="p-8 border-none shadow-xl shadow-zinc-100">
                    <div className="flex justify-between items-start mb-6">
                      <div className="w-12 h-12 bg-emerald-500 rounded-2xl flex items-center justify-center text-white">
                        <Trophy size={24} />
                      </div>
                      <Badge variant="success">Stable</Badge>
                    </div>
                    <h4 className="text-[10px] font-black text-zinc-400 uppercase tracking-widest mb-2">System Confidence</h4>
                    <div className="text-5xl font-black tracking-tighter">{stats?.confidence_metric || 0}%</div>
                  </Card>

                  <Card className="p-8 border-none shadow-xl shadow-zinc-100">
                    <div className="flex justify-between items-start mb-6">
                      <div className="w-12 h-12 bg-indigo-500 rounded-2xl flex items-center justify-center text-white">
                        <User size={24} />
                      </div>
                      <Badge variant="info">Live</Badge>
                    </div>
                    <h4 className="text-[10px] font-black text-zinc-400 uppercase tracking-widest mb-2">Total Candidates</h4>
                    <div className="text-5xl font-black tracking-tighter">{stats?.total_candidates || 0}</div>
                  </Card>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                  <Card className="lg:col-span-2 p-10 border-none shadow-xl shadow-zinc-100">
                    <h3 className="text-2xl font-black tracking-tight mb-10">Match Score Distribution</h3>
                    <div className="h-64 flex items-end gap-3">
                      {Array.from({ length: 20 }).map((_, i) => {
                        const count = stats?.match_score_distribution?.filter((s: number) => s >= i * 5 && s < (i + 1) * 5).length || 0;
                        const height = Math.max(4, (count / (stats?.match_score_distribution?.length || 1)) * 100);
                        return (
                          <div
                            key={i}
                            className="flex-1 bg-zinc-900 rounded-t-xl transition-all hover:bg-indigo-500 relative group cursor-pointer"
                            style={{ height: `${height}%` }}
                          >
                            <div className="absolute -top-12 left-1/2 -translate-x-1/2 bg-zinc-900 text-white text-[10px] px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap font-bold shadow-xl">
                              {count} Candidates
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    <div className="flex justify-between mt-6 text-[10px] font-black text-zinc-400 uppercase tracking-widest">
                      <span>0% Match</span>
                      <span>50% Match</span>
                      <span>100% Match</span>
                    </div>
                  </Card>

                  <Card className="p-10 border-none shadow-xl shadow-zinc-100 bg-zinc-900 text-white">
                    <h3 className="text-2xl font-black tracking-tight mb-10">Top Demanded Skills</h3>
                    <div className="space-y-6">
                      {stats?.top_demanded_skills?.map((skill: string, i: number) => (
                        <div key={skill} className="flex items-center justify-between group">
                          <div className="flex items-center gap-4">
                            <span className="text-zinc-600 font-black text-xl">0{i + 1}</span>
                            <span className="font-bold group-hover:text-indigo-400 transition-colors">{skill}</span>
                          </div>
                          <div className="w-12 h-1 bg-zinc-800 rounded-full overflow-hidden">
                            <div className="h-full bg-indigo-500 w-[70%]" />
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </main>

        {/* Candidate Detail Modal */}
        <AnimatePresence>
          {selectedCandidate && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/80 backdrop-blur-md z-[100] flex items-center justify-center p-8"
            >
              <motion.div
                initial={{ scale: 0.9, y: 40 }}
                animate={{ scale: 1, y: 0 }}
                className="bg-white rounded-[40px] shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col relative"
              >
                <button
                  onClick={() => setSelectedCandidate(null)}
                  className="absolute top-8 right-8 p-3 hover:bg-zinc-100 rounded-2xl transition-colors z-10"
                >
                  <X size={24} />
                </button>

                <div className="p-12 overflow-y-auto space-y-12">
                  <header className="flex justify-between items-start">
                    <div className="flex items-center gap-6">
                      <div className="w-24 h-24 rounded-[32px] bg-zinc-900 flex items-center justify-center text-white text-3xl font-black">
                        {selectedCandidate.resume?.email?.[0].toUpperCase()}
                      </div>
                      <div className="space-y-2">
                        <h3 className="text-4xl font-black tracking-tighter">{selectedCandidate.resume?.email}</h3>
                        <div className="flex gap-4">
                          <span className="flex items-center gap-2 text-sm font-bold text-zinc-500">
                            <MapPin size={16} /> {selectedCandidate.resume?.location}
                          </span>
                          <span className="flex items-center gap-2 text-sm font-bold text-zinc-500">
                            <Clock size={16} /> {selectedCandidate.resume?.experience_years}y Experience
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-[10px] font-black text-zinc-400 uppercase tracking-widest mb-2">Final Match Score</div>
                      <div className="text-6xl font-black tracking-tighter">{Math.round(selectedCandidate.final_match_score)}%</div>
                    </div>
                  </header>

                  <div className="grid grid-cols-3 gap-8">
                    <Card className="p-6 bg-zinc-50 border-none">
                      <h4 className="text-[10px] font-black text-zinc-400 uppercase tracking-widest mb-4">Skill Score</h4>
                      <div className="text-3xl font-black mb-2">{Math.round(selectedCandidate.skill_score)}%</div>
                      <ProgressBar value={selectedCandidate.skill_score} color="indigo" />
                    </Card>
                    <Card className="p-6 bg-zinc-50 border-none">
                      <h4 className="text-[10px] font-black text-zinc-400 uppercase tracking-widest mb-4">Trust Score</h4>
                      <div className="text-3xl font-black mb-2">{Math.round(selectedCandidate.trust_score)}%</div>
                      <ProgressBar value={selectedCandidate.trust_score} color={selectedCandidate.trust_score > 80 ? 'emerald' : 'rose'} />
                    </Card>
                    <Card className={cn("p-6 border-none", selectedCandidate.risk_level === 'LOW' ? "bg-emerald-50" : selectedCandidate.risk_level === 'MEDIUM' ? "bg-amber-50" : "bg-rose-50")}>
                      <h4 className="text-[10px] font-black text-zinc-400 uppercase tracking-widest mb-4">Risk Level</h4>
                      <div className={cn("text-3xl font-black mb-2", selectedCandidate.risk_level === 'LOW' ? "text-emerald-600" : selectedCandidate.risk_level === 'MEDIUM' ? "text-amber-600" : "text-rose-600")}>
                        {selectedCandidate.risk_level}
                      </div>
                      <Badge variant={selectedCandidate.risk_level === 'LOW' ? 'success' : selectedCandidate.risk_level === 'MEDIUM' ? 'warning' : 'danger'}>
                        {selectedCandidate.match_grade}
                      </Badge>
                    </Card>
                  </div>

                  <div className="space-y-8">
                    <div>
                      <h4 className="text-xs font-black text-zinc-400 uppercase tracking-widest mb-4">Matched Skills</h4>
                      <div className="flex flex-wrap gap-2">
                        {selectedCandidate.matched_skills && selectedCandidate.matched_skills.length > 0 ? (
                          selectedCandidate.matched_skills.map(skill => (
                            <Badge key={skill} variant="success">{skill}</Badge>
                          ))
                        ) : (
                          <p className="text-sm text-zinc-500">No matched skills</p>
                        )}
                      </div>
                    </div>

                    {selectedCandidate.skill_gaps && selectedCandidate.skill_gaps.length > 0 && (
                      <div>
                        <h4 className="text-xs font-black text-zinc-400 uppercase tracking-widest mb-4">Skill Gaps</h4>
                        <div className="flex flex-wrap gap-2">
                          {selectedCandidate.skill_gaps.map(skill => (
                            <Badge key={skill} variant="danger">{skill}</Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="p-8 bg-zinc-900 rounded-[32px] text-white">
                      <h4 className="text-xs font-black text-zinc-400 uppercase tracking-widest mb-6">Match Analysis</h4>
                      <p className="text-sm font-medium leading-relaxed text-zinc-300">
                        {selectedCandidate.explanation}
                      </p>
                    </div>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Global Loading Overlay */}
        {loading && !analysis && (
          <div className="fixed bottom-12 right-12 bg-white border border-zinc-200 shadow-2xl rounded-3xl p-6 flex items-center gap-6 z-[200] animate-in slide-in-from-bottom-12">
            <div className="w-8 h-8 border-4 border-zinc-900 border-t-transparent rounded-full animate-spin" />
            <div className="space-y-1">
              <p className="font-black text-sm">Processing with AI Engine</p>
              <p className="text-zinc-500 text-xs font-medium">Running multimodal PDF analysis...</p>
            </div>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
}
