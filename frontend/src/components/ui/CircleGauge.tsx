import React from 'react';
import { cn } from '../../lib/utils';

interface CircleGaugeProps {
  score: number;
  label: string;
  className?: string;
}

export default function CircleGauge({ score, label, className }: CircleGaugeProps) {
  const radius = 60;
  const strokeWidth = 10;
  const normalizedRadius = radius - strokeWidth * 2;
  // Circumference = 2 * pi * r
  // We want a 270 degree arc (3/4 of a circle)
  const circumference = normalizedRadius * 2 * Math.PI;
  
  // Calculate the dash offset based on score (0-100)
  // Total arc length is 0.75 * circumference
  const arcLength = circumference * 0.75;
  const strokeDashoffset = circumference - (score / 100) * arcLength;

  // The gap is the remaining 0.25 of circumference
  const gap = circumference * 0.25;

  return (
    <div className={cn("relative flex flex-col items-center justify-center", className)}>
      <svg
        height={radius * 2}
        width={radius * 2}
        className="transform rotate-135"
        style={{ transform: 'rotate(135deg)' }}
      >
        {/* Background Arc */}
        <circle
          stroke="var(--color-brand-border)"
          fill="transparent"
          strokeWidth={strokeWidth}
          strokeDasharray={`${arcLength} ${gap}`}
          r={normalizedRadius}
          cx={radius}
          cy={radius}
          strokeLinecap="round"
        />
        {/* Foreground Arc */}
        <circle
          stroke="var(--color-brand-terracotta)"
          fill="transparent"
          strokeWidth={strokeWidth}
          strokeDasharray={`${circumference} ${circumference}`}
          style={{ strokeDashoffset }}
          r={normalizedRadius}
          cx={radius}
          cy={radius}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center pt-2">
        <span className="text-4xl font-serif font-bold text-brand-charcoal dark:text-gray-100 italic">{score}</span>
        <span className="text-[10px] uppercase tracking-widest text-muted-foreground mt-1">{label}</span>
      </div>
    </div>
  );
}
