import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, UploadCloud, AlertCircle, Building, UserCircle, Loader2 } from 'lucide-react';
import { useChatStore } from '../store/chatStore';
import { submitVerification, arthaApi } from '../api/artha';

const Verification = () => {
  const { user, setAuth, authToken } = useChatStore();
  const navigate = useNavigate();
  
  const [institution, setInstitution] = useState('');
  const [role, setRole] = useState('Student');
  const [file, setFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);

  // If already approved, redirect to dashboard
  if (user?.status === 'approved') {
    navigate('/dashboard');
    return null;
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!institution || !role || !file) {
      setError('Please fill in all fields and upload an ID document.');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('institution', institution);
      formData.append('role', role);
      formData.append('id_file', file);

      const updatedUser = await submitVerification(formData);
      
      // Update store
      if (authToken) {
        setAuth(updatedUser, authToken);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit verification request.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const checkStatus = async () => {
    setIsRefreshing(true);
    try {
      const res = await arthaApi.get('/auth/me');
      if (authToken) {
        setAuth(res.data, authToken);
      }
    } catch (err) {
      console.error('Failed to fetch user status', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans relative overflow-hidden">
      {/* Decorative blurs */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-brand-red/5 blur-[100px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-secondary/10 blur-[100px] pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="flex justify-center">
          <div className="w-16 h-16 rounded-full bg-brand-red/10 flex items-center justify-center">
            <ShieldCheck className="w-8 h-8 text-brand-red" />
          </div>
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-foreground">
          Account Verification
        </h2>
        <p className="mt-2 text-center text-sm text-muted-foreground">
          We need a few more details before you can access the ARTHA Chatbot.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div className="bg-card py-8 px-4 shadow-sm sm:rounded-2xl sm:px-10 border border-border">
          
          {user?.status === 'pending_approval' ? (
            <div className="text-center">
              <div className="rounded-lg bg-brand-red/10 p-4 mb-6 border border-brand-red/20">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <AlertCircle className="h-5 w-5 text-brand-red" aria-hidden="true" />
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-brand-red">
                      Verification Pending
                    </h3>
                    <div className="mt-2 text-sm text-brand-red/80 text-left">
                      <p>
                        Your request has been submitted and is currently under review by an admin. Once approved, you will have access to the chatbot.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              <button
                onClick={checkStatus}
                disabled={isRefreshing}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-brand-red hover:bg-brand-red/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-red disabled:opacity-50 transition-colors"
              >
                {isRefreshing ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : null}
                Check Status
              </button>
            </div>
          ) : (
            <form className="space-y-6" onSubmit={handleSubmit}>
              {error && (
                <div className="rounded-lg bg-red-50 text-brand-red text-xs p-4 border border-red-100 font-medium">
                  <div className="flex">
                    <AlertCircle className="h-5 w-5 text-brand-red" />
                    <div className="ml-3">
                      <h3 className="text-sm">{error}</h3>
                    </div>
                  </div>
                </div>
              )}

              <div>
                <label htmlFor="institution" className="block text-sm font-medium text-foreground mb-1">
                  Institution or Company Name
                </label>
                <div className="relative rounded-md shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Building className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <input
                    type="text"
                    id="institution"
                    value={institution}
                    onChange={(e) => setInstitution(e.target.value)}
                    className="block w-full pl-10 sm:text-sm bg-secondary border border-border text-foreground placeholder:text-muted-foreground/60 rounded-lg py-2.5 focus:outline-none focus:ring-1 focus:ring-brand-red focus:border-brand-red transition-all"
                    placeholder="e.g. National Law School"
                    required
                  />
                </div>
              </div>

              <div>
                <label htmlFor="role" className="block text-sm font-medium text-foreground mb-1">
                  Your Role
                </label>
                <div className="relative rounded-md shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <UserCircle className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <select
                    id="role"
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    className="block w-full pl-10 sm:text-sm bg-secondary border border-border text-foreground rounded-lg py-2.5 focus:outline-none focus:ring-1 focus:ring-brand-red focus:border-brand-red transition-all"
                  >
                    <option value="Student">Student</option>
                    <option value="Lawyer">Lawyer / Advocate</option>
                    <option value="Researcher">Academic Researcher</option>
                    <option value="Corporate Professional">Corporate Professional</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  ID Document (PDF or Image)
                </label>
                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-border border-dashed rounded-lg group hover:border-brand-red transition-colors bg-secondary/50">
                  <div className="space-y-1 text-center">
                    <UploadCloud className="mx-auto h-12 w-12 text-muted-foreground group-hover:text-brand-red transition-colors" />
                    <div className="flex text-sm text-muted-foreground justify-center">
                      <label
                        htmlFor="file-upload"
                        className="relative cursor-pointer rounded-md font-medium text-brand-red hover:text-brand-red/80 focus-within:outline-none"
                      >
                        <span>Upload a file</span>
                        <input
                          id="file-upload"
                          name="file-upload"
                          type="file"
                          accept=".pdf,.png,.jpg,.jpeg"
                          className="sr-only"
                          onChange={handleFileChange}
                          required
                        />
                      </label>
                      <p className="pl-1">or drag and drop</p>
                    </div>
                    <p className="text-xs text-muted-foreground/80">
                      {file ? file.name : "PNG, JPG, PDF up to 10MB"}
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={isSubmitting || !file}
                  className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-brand-red hover:bg-brand-red/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-red disabled:opacity-50 transition-colors"
                >
                  {isSubmitting ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    "Submit Request"
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
        
        <div className="mt-6 text-center">
          <button onClick={() => navigate('/dashboard')} className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            Return to Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};

export default Verification;
