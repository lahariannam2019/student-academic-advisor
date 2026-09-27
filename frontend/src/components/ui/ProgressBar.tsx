import React from 'react';

interface ProgressBarProps {
  value: number; // 0 to 100
  threshold?: number; // e.g. 75 for attendance
  showLabel?: boolean;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  threshold,
  showLabel = false,
  className = '',
  size = 'md',
}) => {
  const clampedValue = Math.min(100, Math.max(0, value));

  // Determine color based on threshold if provided
  let barColor = 'bg-indigo-600';
  if (threshold !== undefined) {
    if (clampedValue < threshold) {
      barColor = 'bg-rose-500';
    } else if (clampedValue < threshold + 10) {
      barColor = 'bg-amber-500';
    } else {
      barColor = 'bg-emerald-500';
    }
  }

  const heightStyles = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  };

  return (
    <div className={`w-full ${className}`}>
      {showLabel && (
        <div className="flex justify-between items-center text-xs font-medium text-slate-600 mb-1.5">
          <span>Progress</span>
          <span className="font-semibold text-slate-800">{Math.round(clampedValue)}%</span>
        </div>
      )}
      <div className={`w-full bg-slate-100 rounded-full overflow-hidden ${heightStyles[size]}`}>
        <div
          className={`${barColor} ${heightStyles[size]} rounded-full transition-all duration-500 ease-out`}
          style={{ width: `${clampedValue}%` }}
        />
      </div>
    </div>
  );
};
