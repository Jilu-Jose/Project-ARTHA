import Layout from '../components/ui/Layout';
import { FileText, Building2, Globe2 } from 'lucide-react';

export default function Dashboard() {
  return (
    <Layout>
      <div className="flex flex-col h-full animate-in fade-in duration-500 pb-10">
        
        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Main Left Column (Takes up 2 cols) */}
          <div className="lg:col-span-2 flex flex-col gap-8">
            
            {/* Compliance Standing Card */}
            <div className="bg-card border border-border rounded-2xl p-8 shadow-sm flex flex-col sm:flex-row justify-between items-center gap-8 relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-brand-red-light to-brand-red"></div>
              
              <div className="flex-1">
                <h2 className="text-2xl font-serif text-foreground mb-3">Compliance Standing</h2>
                <p className="text-sm text-muted-foreground mb-6 max-w-md">
                  Your organization is currently maintaining optimal compliance levels across all registered jurisdictions.
                </p>
                <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-red-50 rounded-full border border-red-100">
                  <div className="w-2 h-2 rounded-full bg-brand-red"></div>
                  <span className="text-xs font-semibold text-brand-red">Status: Optimal</span>
                </div>
              </div>

              {/* Red Circle Gauge (Hardcoded CSS approach for UI accuracy) */}
              <div className="relative w-40 h-40 shrink-0 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                  {/* Background Circle */}
                  <circle 
                    cx="50" cy="50" r="40" 
                    fill="none" stroke="#FEF2F2" strokeWidth="12"
                  />
                  {/* Progress Circle (Score 92) */}
                  <circle 
                    cx="50" cy="50" r="40" 
                    fill="none" stroke="#B91C1C" strokeWidth="12"
                    strokeDasharray="251.2" strokeDashoffset="20"
                    strokeLinecap="round"
                    className="drop-shadow-md"
                  />
                </svg>
                <div className="absolute flex flex-col items-center justify-center text-center">
                  <span className="text-4xl font-bold text-foreground font-serif tracking-tight">92</span>
                  <span className="text-xs text-muted-foreground font-medium">Score</span>
                </div>
              </div>
            </div>

            {/* Active Filings */}
            <div>
              <div className="flex justify-between items-end mb-4 px-1">
                <h3 className="text-xl font-serif text-foreground">Active Filings</h3>
                <button className="text-xs font-semibold text-brand-red hover:text-brand-red-dark transition-colors">
                  View All
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Card 1 */}
                <ActiveFilingCard 
                  icon={<FileText className="w-4 h-4 text-brand-red" />}
                  title="Annual Return (MGT-7)"
                  subtitle="Ministry of Corporate Affairs"
                  dueText="Due in 5 days"
                  progress={75}
                  stepText="Step 3 of 4"
                  buttonText="Review"
                />

                {/* Card 2 */}
                <ActiveFilingCard 
                  icon={<Building2 className="w-4 h-4 text-brand-red" />}
                  title="GSTR-3B"
                  subtitle="Goods and Services Tax Network"
                  dueText="Due in 12 days"
                  progress={40}
                  stepText="Step 2 of 5"
                  buttonText="Continue"
                />

                {/* Card 3 (Full width) */}
                <ActiveFilingCard 
                  icon={<Globe2 className="w-4 h-4 text-brand-red" />}
                  title="FDI Reporting (FC-GPR)"
                  subtitle="Reserve Bank of India"
                  dueText="Due in 20 days"
                  progress={0}
                  buttonText="Start Filing"
                  fullWidth
                />
              </div>
            </div>

          </div>

          {/* Right Column (Intelligence Feed) */}
          <div className="flex flex-col h-[calc(100vh-140px)]">
            <h3 className="text-xl font-serif text-foreground mb-4 px-1">Intelligence Feed</h3>
            
            <div className="bg-card border border-border rounded-2xl shadow-sm flex-1 overflow-y-auto p-6 relative">
              <div className="absolute left-7 top-10 bottom-10 w-[1px] bg-secondary"></div>
              
              <div className="space-y-8 relative">
                <FeedItem 
                  time="2 hours ago"
                  source="RBI Update"
                  title="Revised Guidelines on Digital Lending"
                  description="The RBI has issued new directives tightening the norms for digital lending platforms, requiring explicit consent for data usage."
                />
                <FeedItem 
                  time="Yesterday"
                  source="SEBI Notification"
                  title="Disclosure Requirements Enhanced"
                  description="Listed entities must now disclose ESG metrics in their annual reports starting next fiscal year."
                  sourceColor="text-blue-600"
                  dotColor="bg-blue-600"
                />
                <FeedItem 
                  time="3 days ago"
                  source="MCA Circular"
                  title="Extension of AGM Timeline"
                  description="Relaxation provided for holding Annual General Meetings through video conferencing."
                  sourceColor="text-foreground"
                  dotColor="bg-border"
                />
              </div>
            </div>
          </div>

        </div>
      </div>
    </Layout>
  );
}

function ActiveFilingCard({ 
  icon, title, subtitle, dueText, progress, stepText, buttonText, fullWidth 
}: { 
  icon: React.ReactNode, title: string, subtitle: string, dueText: string, progress: number, stepText?: string, buttonText: string, fullWidth?: boolean 
}) {
  return (
    <div className={`bg-card border border-border rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col ${fullWidth ? 'md:col-span-2' : ''}`}>
      <div className="flex justify-between items-start mb-4">
        <div className="w-8 h-8 rounded-full bg-red-50 flex items-center justify-center">
          {icon}
        </div>
        <div className="px-3 py-1 bg-secondary border border-gray-100 rounded-full text-[10px] font-medium text-foreground">
          {dueText}
        </div>
      </div>
      
      <div className="mb-4 flex-1">
        <h4 className="font-semibold text-foreground text-sm mb-1">{title}</h4>
        <p className="text-xs text-muted-foreground">{subtitle}</p>
      </div>

      {progress > 0 && (
        <div className="mb-5">
          <div className="w-full h-2 bg-secondary rounded-full overflow-hidden mb-2">
            <div className="h-full bg-brand-red rounded-full" style={{ width: `${progress}%` }}></div>
          </div>
          <div className="flex justify-between items-center text-[10px] text-muted-foreground">
            <span>{progress}% Complete</span>
            {stepText && <span>{stepText}</span>}
          </div>
        </div>
      )}

      <button className={`w-full py-2.5 rounded-lg text-sm font-semibold transition-colors mt-auto ${
        progress > 0 
          ? 'bg-secondary text-brand-red hover:bg-secondary' 
          : 'bg-card border border-border text-brand-red hover:bg-secondary'
      }`}>
        {buttonText}
      </button>
    </div>
  );
}

function FeedItem({ time, source, title, description, sourceColor = "text-brand-red", dotColor = "bg-brand-red" }: { time: string, source: string, title: string, description: string, sourceColor?: string, dotColor?: string }) {
  return (
    <div className="relative pl-6">
      {/* Timeline dot */}
      <div className={`absolute -left-[5px] top-1.5 w-2.5 h-2.5 rounded-full ${dotColor} ring-4 ring-card z-10`}></div>
      
      <div className="flex items-center gap-2 mb-2">
        <span className={`text-[10px] font-semibold ${sourceColor}`}>{source}</span>
        <span className="text-[10px] text-muted-foreground">{time}</span>
      </div>
      
      <div className="bg-secondary rounded-xl p-4 border border-border/50">
        <h4 className="font-medium text-foreground text-sm mb-1.5 leading-snug">{title}</h4>
        <p className="text-xs text-muted-foreground leading-relaxed">{description}</p>
      </div>
    </div>
  );
}
