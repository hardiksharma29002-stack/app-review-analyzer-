"use client";

import { useState } from "react";

import { motion, Variants } from "framer-motion";
import { Download, Mail, TrendingUp, TrendingDown, Star } from "lucide-react";

export default function ReportView({ data }: { data: any }) {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState("");

  const handleSendEmail = async () => {
    if (!email) {
      setStatus("Please enter an email");
      return;
    }
    setStatus("Sending...");
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/send-email`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
      });
      const data = await res.json();
      if (res.ok) {
        setStatus("Sent successfully!");
      } else {
        setStatus("Failed: " + data.detail);
      }
    } catch (e) {
      setStatus("Error sending email");
    }
  };

  const container: Variants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.2, delayChildren: 0.3 }
    }
  };

  const item: Variants = {
    hidden: { opacity: 0, y: 50, scale: 0.95 },
    show: { opacity: 1, y: 0, scale: 1, transition: { type: "spring", stiffness: 100, damping: 20 } }
  };

  return (
    <section className="relative min-h-screen px-6 py-24 max-w-7xl mx-auto z-10 flex flex-col">
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1, delay: 0.2 }}
        className="mb-16 text-center"
      >
        <h2 className="text-4xl md:text-6xl font-bold mb-4">Product Pulse Summary</h2>
        <p className="text-xl text-foreground/50">Based on provided dataset</p>
      </motion.div>

      <motion.div 
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16"
      >
        {/* Metric Cards */}
        {(data?.metrics || []).map((metric: any, i: number) => (
          <motion.div 
            key={i}
            variants={item}
            whileHover={{ y: -10, scale: 1.02 }}
            className="glass rounded-3xl p-8 border-t border-l border-white/10 shadow-2xl relative overflow-hidden group"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-foreground/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <h3 className="text-lg text-foreground/60 font-medium mb-4">{metric.title}</h3>
            <div className="flex items-end gap-4">
              <span className={`text-6xl font-black ${metric.color}`}>{metric.value}</span>
              {metric.trend === 'up' ? <TrendingUp className={metric.color} size={32} /> : <TrendingDown className={metric.color} size={32} />}
            </div>
          </motion.div>
        ))}
        {(!data?.metrics || data.metrics.length === 0) && (
           <div className="col-span-3 text-center text-foreground/50 italic py-8">
             No metrics available. Data analysis failed or returned empty results.
           </div>
        )}
      </motion.div>

      <motion.div 
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 lg:grid-cols-2 gap-8 flex-1"
      >
        {/* Actionable Recommendations */}
        <motion.div variants={item} className="glass rounded-3xl p-8 border-t border-l border-foreground/10">
          <div className="flex justify-between items-center mb-8">
            <h3 className="text-2xl font-bold">Strategic Priorities</h3>
            <span className="px-3 py-1 rounded-full bg-primary/20 text-primary text-xs font-bold tracking-wider">AI GENERATED</span>
          </div>
          <div className="space-y-6">
            {(data?.recommendations || []).map((insight: string, i: number) => (
              <div key={i} className="flex gap-4 group">
                <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold shrink-0 group-hover:scale-110 group-hover:bg-primary group-hover:text-background transition-all">
                  {i + 1}
                </div>
                <p className="text-foreground/80 leading-relaxed group-hover:text-foreground transition-colors">{insight}</p>
              </div>
            ))}
            {(!data?.recommendations || data.recommendations.length === 0) && (
               <p className="text-foreground/60 italic">No recommendations available.</p>
            )}
          </div>
        </motion.div>

        {/* Voice of Customer */}
        <motion.div variants={item} className="flex flex-col gap-6">
          <h3 className="text-2xl font-bold px-4">Voice of the Customer</h3>
          {(data?.quotes || []).map((quote: any, i: number) => (
            <motion.div 
              key={i}
              whileHover={{ x: 10 }}
              className="neumorphic-btn rounded-2xl p-6 border-l-4 border-primary"
            >
              <div className="flex gap-1 mb-3">
                {[...Array(5)].map((_, j) => (
                  <Star key={j} size={16} className={j < quote.stars ? "fill-yellow-400 text-yellow-400" : "text-foreground/20"} />
                ))}
              </div>
              <p className="text-foreground/70 italic text-lg leading-relaxed mb-4">"{quote.text}"</p>
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-primary to-blue-500" />
                <span className="text-sm font-medium text-foreground/50">Verified User</span>
              </div>
            </motion.div>
          ))}
          {(!data?.quotes || data.quotes.length === 0) && (
               <p className="text-foreground/60 italic px-4">No quotes available.</p>
          )}
        </motion.div>
      </motion.div>

      {/* Footer Actions */}
      <motion.div 
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.5, duration: 1 }}
        className="mt-16 flex flex-col md:flex-row items-center justify-between gap-6 p-6 glass rounded-full"
      >
        <button 
          onClick={async () => {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
            try {
              const res = await fetch(`${apiUrl}/report/download`);
              if (!res.ok) {
                const err = await res.json();
                alert(`Download failed: ${err.detail || "Error"}`);
                return;
              }
              const blob = await res.blob();
              const url = window.URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.style.display = "none";
              a.href = url;
              a.download = "weekly_pulse.pdf";
              document.body.appendChild(a);
              a.click();
              
              // Delay cleanup to ensure the download actually starts
              setTimeout(() => {
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
              }, 1000);
            } catch (e: any) {
              console.error("PDF Download Error:", e);
              alert(`Failed to download PDF: ${e.message || e}`);
            }
          }}
          className="flex items-center gap-2 px-8 py-4 rounded-full border border-foreground/20 hover:bg-foreground/5 transition-colors font-medium text-foreground"
        >
          <Download size={20} />
          Download PDF
        </button>
        
        <div className="flex w-full md:w-auto relative group flex-col">
          <div className="relative w-full md:w-80">
            <input 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter email address..." 
              className="w-full bg-background/50 border border-foreground/10 text-foreground rounded-full py-4 pl-6 pr-32 outline-none focus:border-primary/50 transition-colors placeholder:text-foreground/30"
            />
            <button onClick={handleSendEmail} className="absolute right-2 top-2 bottom-2 bg-primary text-background px-6 rounded-full font-bold hover:bg-primary/90 transition-colors flex items-center gap-2">
              <Mail size={18} />
              Send
            </button>
          </div>
          {status && (
            <p className="text-sm mt-2 ml-4 text-foreground/60">{status}</p>
          )}
        </div>
      </motion.div>
    </section>
  );
}
